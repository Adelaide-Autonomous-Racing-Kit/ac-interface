#pragma once

#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>

#include <fcntl.h>
#include <sys/file.h>
#include <sys/mman.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <sys/un.h>
#include <time.h>
#include <unistd.h>

namespace aci {

struct FrameHeader {
    uint32_t magic, version, width, height, format, pitch;
    uint64_t sequence, present_hook_ns;
};
static_assert(sizeof(FrameHeader) == 40);
constexpr uint32_t magic = 0x46494341; // ACIF (little endian)

inline uint64_t monotonic_ns() {
    timespec ts{};
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return uint64_t(ts.tv_sec) * 1000000000 + ts.tv_nsec;
}

class Publisher {
    std::string path;
    int peer = -1, slot = -1;
    void *map = MAP_FAILED;
    size_t size = 0;
    uint64_t retry_at = 0, sequence = 0;
    uint32_t width = 0, height = 0;
    bool disabled = false;

    void close_peer() {
        if (map != MAP_FAILED) munmap(map, size);
        if (slot >= 0) close(slot);
        if (peer >= 0) close(peer);
        map = MAP_FAILED;
        slot = peer = -1;
    }

    void notify(const char *message, size_t length) {
        if (send(peer, message, length, MSG_DONTWAIT | MSG_NOSIGNAL) < 0 &&
            errno != EAGAIN && errno != EWOULDBLOCK) {
            close_peer();
            disabled = true; // A receiver may not reconnect to an old game.
        }
    }

public:
    Publisher() {
        const auto *endpoint = getenv("ACI_FRAME_SOCKET");
        const auto *expected = getenv("ACI_FRAME_PROCESS");
        if (!endpoint || !expected) return;
        char name[64]{};
        auto *comm = fopen("/proc/self/comm", "re");
        if (!comm) return;
        const bool found = fgets(name, sizeof(name), comm) != nullptr;
        fclose(comm);
        name[strcspn(name, "\n")] = '\0';
        if (found && !strcmp(name, expected)) path = endpoint;
    }

    ~Publisher() { close_peer(); }

    bool ready(uint64_t now) {
        if (disabled || path.empty() || now < retry_at) return false;
        if (peer >= 0) return true;
        retry_at = now + 100000000; // No listener until ACI starts its capture child.
        sockaddr_un address{};
        address.sun_family = AF_UNIX;
        if (path.size() >= sizeof(address.sun_path) ||
            path.size() < 6 || path.substr(path.size() - 5) != ".sock") return false;
        memcpy(address.sun_path, path.c_str(), path.size() + 1);
        peer = socket(AF_UNIX, SOCK_SEQPACKET | SOCK_CLOEXEC | SOCK_NONBLOCK, 0);
        if (peer < 0) return false;
        if (connect(peer, reinterpret_cast<sockaddr *>(&address), sizeof(address)) < 0) {
            close_peer();
            return false;
        }

        const auto slot_path = path.substr(0, path.size() - 5) + ".frame";
        slot = open(slot_path.c_str(), O_RDWR | O_CLOEXEC | O_NOFOLLOW);
        struct stat st{};
        if (slot < 0 || fstat(slot, &st) || !S_ISREG(st.st_mode) ||
            st.st_uid != getuid() || st.st_size <= int64_t(sizeof(FrameHeader))) {
            fail("Invalid ACI frame slot");
            return false;
        }
        FrameHeader initial{};
        if (pread(slot, &initial, sizeof(initial), 0) != sizeof(initial) ||
            initial.magic != magic || initial.version != 1 || initial.sequence != 0) {
            fail("Invalid ACI frame slot header");
            return false;
        }
        width = initial.width;
        height = initial.height;
        size = size_t(st.st_size);
        map = mmap(nullptr, size, PROT_WRITE, MAP_SHARED, slot, 0);
        if (map == MAP_FAILED) {
            fail("Cannot map ACI frame slot");
            return false;
        }
        retry_at = 0;
        return true;
    }

    bool matches(uint32_t w, uint32_t h) const { return w == width && h == height; }

    void fail(const char *reason) {
        fprintf(stderr, "ACI Vulkan capture: %s\n", reason);
        if (peer >= 0) {
            const auto error = std::string("E") + reason;
            notify(error.data(), error.size());
        }
        close_peer();
        disabled = true;
    }

    void publish(uint32_t w, uint32_t h, uint32_t format, uint64_t ns,
                 const void *pixels) {
        const auto bytes = size_t(w) * h * 4;
        if (size != sizeof(FrameHeader) + bytes) {
            fail("Swapchain dimensions differ from the configured ACI frame slot");
            return;
        }
        ++sequence;
        if (flock(slot, LOCK_EX | LOCK_NB)) {
            if (errno != EWOULDBLOCK) fail("Cannot lock ACI frame slot");
            return;
        }
        const FrameHeader header{magic, 1, w, h, format, w * 4, sequence, ns};
        memcpy(map, &header, sizeof(header));
        memcpy(static_cast<char *>(map) + sizeof(header), pixels, bytes);
        flock(slot, LOCK_UN);
        notify("F", 1);
    }
};

} // namespace aci
