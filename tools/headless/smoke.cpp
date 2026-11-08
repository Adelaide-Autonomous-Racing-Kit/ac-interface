// A moving, asymmetric test pattern on a real Vulkan headless swapchain.
#define VK_USE_PLATFORM_XCB_KHR
#include <vulkan/vulkan.h>

#include <algorithm>
#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <stdexcept>
#include <thread>
#include <vector>

namespace {
constexpr uint32_t width = 1280, height = 736;
void check(VkResult result, const char *call) {
    if (result != VK_SUCCESS && result != VK_SUBOPTIMAL_KHR) {
        fprintf(stderr, "%s: Vulkan result %d\n", call, result);
        std::exit(1);
    }
}
#define CHECK(call) check((call), #call)

int run(int seconds, int fps) {
    VkApplicationInfo app{VK_STRUCTURE_TYPE_APPLICATION_INFO};
    app.apiVersion = VK_API_VERSION_1_1;
    const bool use_xcb = getenv("ACI_SMOKE_XCB") != nullptr;
    const char *extensions[] = {VK_KHR_SURFACE_EXTENSION_NAME,
        use_xcb ? VK_KHR_XCB_SURFACE_EXTENSION_NAME : VK_EXT_HEADLESS_SURFACE_EXTENSION_NAME};
    VkInstanceCreateInfo instance_info{VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO};
    instance_info.pApplicationInfo = &app;
    instance_info.enabledExtensionCount = 2;
    instance_info.ppEnabledExtensionNames = extensions;
    VkInstance instance;
    CHECK(vkCreateInstance(&instance_info, nullptr, &instance));
    VkSurfaceKHR surface;
    xcb_connection_t *xcb = nullptr;
    if (use_xcb) {
        xcb = xcb_connect(nullptr, nullptr);
        if (xcb_connection_has_error(xcb)) throw std::runtime_error("Cannot connect to X server");
        auto *screen = xcb_setup_roots_iterator(xcb_get_setup(xcb)).data;
        auto window = xcb_generate_id(xcb);
        CHECK(xcb_request_check(xcb, xcb_create_window_checked(
            xcb, XCB_COPY_FROM_PARENT, window, screen->root, 0, 0, width, height,
            0, XCB_WINDOW_CLASS_INPUT_OUTPUT, screen->root_visual, 0, nullptr))
            ? VK_ERROR_INITIALIZATION_FAILED : VK_SUCCESS);
        xcb_map_window(xcb, window);
        xcb_flush(xcb);
        VkXcbSurfaceCreateInfoKHR surface_info{VK_STRUCTURE_TYPE_XCB_SURFACE_CREATE_INFO_KHR};
        surface_info.connection = xcb;
        surface_info.window = window;
        CHECK(vkCreateXcbSurfaceKHR(instance, &surface_info, nullptr, &surface));
    } else {
        auto create_surface = reinterpret_cast<PFN_vkCreateHeadlessSurfaceEXT>(
            vkGetInstanceProcAddr(instance, "vkCreateHeadlessSurfaceEXT"));
        if (!create_surface) throw std::runtime_error("No VK_EXT_headless_surface support");
        VkHeadlessSurfaceCreateInfoEXT surface_info{VK_STRUCTURE_TYPE_HEADLESS_SURFACE_CREATE_INFO_EXT};
        CHECK(create_surface(instance, &surface_info, nullptr, &surface));
    }

    uint32_t count;
    CHECK(vkEnumeratePhysicalDevices(instance, &count, nullptr));
    std::vector<VkPhysicalDevice> physicals(count);
    CHECK(vkEnumeratePhysicalDevices(instance, &count, physicals.data()));
    VkPhysicalDevice physical{};
    uint32_t family = 0;
    for (auto p : physicals) {
        VkPhysicalDeviceProperties properties{};
        vkGetPhysicalDeviceProperties(p, &properties);
        if (properties.deviceType != VK_PHYSICAL_DEVICE_TYPE_DISCRETE_GPU) continue;
        vkGetPhysicalDeviceQueueFamilyProperties(p, &count, nullptr);
        std::vector<VkQueueFamilyProperties> families(count);
        vkGetPhysicalDeviceQueueFamilyProperties(p, &count, families.data());
        for (uint32_t i = 0; i < count; ++i) {
            VkBool32 supported;
            CHECK(vkGetPhysicalDeviceSurfaceSupportKHR(p, i, surface, &supported));
            if (!supported || !(families[i].queueFlags & VK_QUEUE_GRAPHICS_BIT)) continue;
            physical = p;
            family = i;
            printf("Device: %s\n", properties.deviceName);
            break;
        }
        if (physical) break;
    }
    if (!physical) throw std::runtime_error("No discrete GPU with headless Vulkan support");

    VkSurfaceCapabilitiesKHR caps{};
    CHECK(vkGetPhysicalDeviceSurfaceCapabilitiesKHR(physical, surface, &caps));
    CHECK(vkGetPhysicalDeviceSurfaceFormatsKHR(physical, surface, &count, nullptr));
    std::vector<VkSurfaceFormatKHR> formats(count);
    CHECK(vkGetPhysicalDeviceSurfaceFormatsKHR(physical, surface, &count, formats.data()));
    auto format = std::find_if(formats.begin(), formats.end(), [](const auto &f) {
        return (f.format == VK_FORMAT_B8G8R8A8_UNORM || f.format == VK_FORMAT_R8G8B8A8_UNORM)
            && f.colorSpace == VK_COLOR_SPACE_SRGB_NONLINEAR_KHR;
    });
    if (format == formats.end()) throw std::runtime_error("No supported SDR UNORM format");
    float priority = 1;
    VkDeviceQueueCreateInfo queues{VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO};
    queues.queueFamilyIndex = family;
    queues.queueCount = 1;
    queues.pQueuePriorities = &priority;
    const char *device_extension = VK_KHR_SWAPCHAIN_EXTENSION_NAME;
    VkDeviceCreateInfo device_info{VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO};
    device_info.queueCreateInfoCount = device_info.enabledExtensionCount = 1;
    device_info.pQueueCreateInfos = &queues;
    device_info.ppEnabledExtensionNames = &device_extension;
    VkDevice device;
    CHECK(vkCreateDevice(physical, &device_info, nullptr, &device));
    VkQueue queue;
    vkGetDeviceQueue(device, family, 0, &queue);
    VkSwapchainCreateInfoKHR swap_info{VK_STRUCTURE_TYPE_SWAPCHAIN_CREATE_INFO_KHR};
    swap_info.surface = surface;
    swap_info.minImageCount = caps.minImageCount;
    swap_info.imageFormat = format->format;
    swap_info.imageColorSpace = format->colorSpace;
    swap_info.imageExtent = {width, height};
    swap_info.imageArrayLayers = 1;
    swap_info.imageUsage = VK_IMAGE_USAGE_TRANSFER_DST_BIT;
    swap_info.preTransform = VK_SURFACE_TRANSFORM_IDENTITY_BIT_KHR;
    swap_info.compositeAlpha = VK_COMPOSITE_ALPHA_OPAQUE_BIT_KHR;
    swap_info.presentMode = VK_PRESENT_MODE_FIFO_KHR;
    swap_info.clipped = VK_TRUE;
    VkSwapchainKHR swap;
    CHECK(vkCreateSwapchainKHR(device, &swap_info, nullptr, &swap));
    CHECK(vkGetSwapchainImagesKHR(device, swap, &count, nullptr));
    std::vector<VkImage> images(count);
    CHECK(vkGetSwapchainImagesKHR(device, swap, &count, images.data()));
    std::vector<VkSemaphore> rendered(count);
    VkSemaphoreCreateInfo semaphore_info{VK_STRUCTURE_TYPE_SEMAPHORE_CREATE_INFO};
    for (auto &semaphore : rendered) CHECK(vkCreateSemaphore(device, &semaphore_info, nullptr, &semaphore));
    VkFenceCreateInfo fence_info{VK_STRUCTURE_TYPE_FENCE_CREATE_INFO};
    VkFence acquired;
    CHECK(vkCreateFence(device, &fence_info, nullptr, &acquired));

    VkBufferCreateInfo buffer_info{VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO};
    constexpr VkDeviceSize frame_bytes = width * height * 4;
    buffer_info.size = 2 * frame_bytes;
    buffer_info.usage = VK_BUFFER_USAGE_TRANSFER_SRC_BIT;
    VkBuffer buffer;
    CHECK(vkCreateBuffer(device, &buffer_info, nullptr, &buffer));
    VkMemoryRequirements requirements{};
    vkGetBufferMemoryRequirements(device, buffer, &requirements);
    VkPhysicalDeviceMemoryProperties memory{};
    vkGetPhysicalDeviceMemoryProperties(physical, &memory);
    uint32_t memory_type = 0;
    constexpr auto flags = VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT | VK_MEMORY_PROPERTY_HOST_COHERENT_BIT;
    for (; memory_type < memory.memoryTypeCount; ++memory_type) {
        if ((requirements.memoryTypeBits & (1u << memory_type)) &&
            (memory.memoryTypes[memory_type].propertyFlags & flags) == flags) break;
    }
    if (memory_type == memory.memoryTypeCount) throw std::runtime_error("No coherent host memory");
    VkMemoryAllocateInfo allocation{VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO};
    allocation.allocationSize = requirements.size;
    allocation.memoryTypeIndex = memory_type;
    VkDeviceMemory pixels;
    CHECK(vkAllocateMemory(device, &allocation, nullptr, &pixels));
    CHECK(vkBindBufferMemory(device, buffer, pixels, 0));
    void *map;
    CHECK(vkMapMemory(device, pixels, 0, VK_WHOLE_SIZE, 0, &map));
    auto *bytes = static_cast<uint8_t *>(map);
    bool bgra = format->format == VK_FORMAT_B8G8R8A8_UNORM;
    for (uint32_t i = 0; i < 2; ++i) {
        for (uint32_t y = 0; y < height; ++y) {
            for (uint32_t x = 0; x < width; ++x) {
                auto *p = bytes + i * frame_bytes + (y * width + x) * 4;
                p[bgra ? 2 : 0] = x < width / 2 ? 255 : 0;
                p[1] = i ? 240 : 16;
                p[bgra ? 0 : 2] = y < height / 2 ? 0 : 255;
                p[3] = 255;
            }
        }
    }
    vkUnmapMemory(device, pixels);

    VkCommandPoolCreateInfo pool_info{VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO};
    pool_info.queueFamilyIndex = family;
    VkCommandPool pool;
    CHECK(vkCreateCommandPool(device, &pool_info, nullptr, &pool));
    VkCommandBufferAllocateInfo commands_info{VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO};
    commands_info.commandPool = pool;
    commands_info.commandBufferCount = 2 * count;
    std::vector<VkCommandBuffer> commands(2 * count);
    CHECK(vkAllocateCommandBuffers(device, &commands_info, commands.data()));
    for (uint32_t i = 0; i < commands.size(); ++i) {
        const auto cmd = commands[i];
        VkCommandBufferBeginInfo begin{VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO};
        CHECK(vkBeginCommandBuffer(cmd, &begin));
        VkImageMemoryBarrier barrier{VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER};
        barrier.oldLayout = VK_IMAGE_LAYOUT_UNDEFINED;
        barrier.newLayout = VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL;
        barrier.srcQueueFamilyIndex = barrier.dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
        barrier.image = images[i % count];
        barrier.subresourceRange = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1};
        barrier.dstAccessMask = VK_ACCESS_TRANSFER_WRITE_BIT;
        vkCmdPipelineBarrier(cmd, VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT, VK_PIPELINE_STAGE_TRANSFER_BIT,
                             0, 0, nullptr, 0, nullptr, 1, &barrier);
        VkBufferImageCopy copy{};
        copy.bufferOffset = (i / count) * frame_bytes;
        copy.imageSubresource = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 0, 1};
        copy.imageExtent = {width, height, 1};
        vkCmdCopyBufferToImage(cmd, buffer, barrier.image, barrier.newLayout, 1, &copy);
        barrier.oldLayout = barrier.newLayout;
        barrier.newLayout = VK_IMAGE_LAYOUT_PRESENT_SRC_KHR;
        barrier.srcAccessMask = VK_ACCESS_TRANSFER_WRITE_BIT;
        barrier.dstAccessMask = 0;
        vkCmdPipelineBarrier(cmd, VK_PIPELINE_STAGE_TRANSFER_BIT, VK_PIPELINE_STAGE_BOTTOM_OF_PIPE_BIT,
                             0, 0, nullptr, 0, nullptr, 1, &barrier);
        CHECK(vkEndCommandBuffer(cmd));
    }

    using clock = std::chrono::steady_clock;
    const auto started = clock::now();
    const auto deadline = started + std::chrono::seconds(seconds);
    auto next = started;
    const auto interval = std::chrono::nanoseconds(1000000000 / fps);
    uint64_t frames = 0;
    while (clock::now() < deadline) {
        uint32_t index;
        CHECK(vkAcquireNextImageKHR(device, swap, UINT64_MAX, VK_NULL_HANDLE, acquired, &index));
        CHECK(vkWaitForFences(device, 1, &acquired, VK_TRUE, UINT64_MAX));
        CHECK(vkResetFences(device, 1, &acquired));
        const auto cmd = commands[(frames % 2) * count + index];
        VkSubmitInfo submit{VK_STRUCTURE_TYPE_SUBMIT_INFO};
        submit.commandBufferCount = submit.signalSemaphoreCount = 1;
        submit.pCommandBuffers = &cmd;
        submit.pSignalSemaphores = &rendered[index];
        CHECK(vkQueueSubmit(queue, 1, &submit, VK_NULL_HANDLE));
        VkPresentInfoKHR present{VK_STRUCTURE_TYPE_PRESENT_INFO_KHR};
        present.waitSemaphoreCount = present.swapchainCount = 1;
        present.pWaitSemaphores = &rendered[index];
        present.pSwapchains = &swap;
        present.pImageIndices = &index;
        CHECK(vkQueuePresentKHR(queue, &present));
        ++frames;
        next = std::max(next + interval, clock::now());
        std::this_thread::sleep_until(next);
    }

    CHECK(vkDeviceWaitIdle(device));
    printf("Rendered %lu frames in %.3f s\n", frames,
           std::chrono::duration<double>(clock::now() - started).count());
    vkDestroyCommandPool(device, pool, nullptr);
    vkDestroyBuffer(device, buffer, nullptr);
    vkFreeMemory(device, pixels, nullptr);
    vkDestroyFence(device, acquired, nullptr);
    for (auto semaphore : rendered) vkDestroySemaphore(device, semaphore, nullptr);
    vkDestroySwapchainKHR(device, swap, nullptr);
    vkDestroyDevice(device, nullptr);
    vkDestroySurfaceKHR(instance, surface, nullptr);
    vkDestroyInstance(instance, nullptr);
    if (xcb) xcb_disconnect(xcb);
    return 0;
}
} // namespace

int main(int argc, char **argv) {
    try {
        int seconds = argc > 1 ? std::stoi(argv[1]) : 5;
        int fps = argc > 2 ? std::stoi(argv[2]) : 60;
        if (seconds <= 0 || fps <= 0 || fps > 1000) throw std::runtime_error("Invalid duration or FPS");
        return run(seconds, fps);
    } catch (const std::exception &e) {
        fprintf(stderr, "%s\n", e.what());
        return 1;
    }
}
