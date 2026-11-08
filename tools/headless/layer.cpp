// Direct swapchain readback. Capture only the process explicitly named by the launch.
#include "publisher.hpp"

#include <vulkan/vk_layer.h>

#include <map>
#include <memory>
#include <mutex>
#include <vector>

#define EXPORT extern "C" __attribute__((visibility("default"))) VKAPI_ATTR
#define API VKAPI_CALL

namespace {

void *key(const void *dispatchable) { return *static_cast<void *const *>(dispatchable); }

struct Instance {
    VkInstance handle;
    PFN_vkGetInstanceProcAddr get;
    PFN_GetPhysicalDeviceProcAddr physical;
};

struct Swapchain {
    VkExtent2D extent;
    uint32_t format;
    bool supported;
    std::vector<VkImage> images;
    VkBuffer buffer{};
    VkDeviceMemory memory{};
    void *pixels{};
    bool coherent{};
    VkCommandPool pool{};
    VkCommandBuffer commands{};
    VkFence fence{};
    uint32_t family = VK_QUEUE_FAMILY_IGNORED;
};

struct Device {
    VkDevice handle;
    PFN_vkGetDeviceProcAddr get;
    VkPhysicalDevice physical;
    PFN_vkGetPhysicalDeviceSurfaceCapabilitiesKHR surface_caps;
    PFN_vkSetDeviceLoaderData set_loader_data;
    VkPhysicalDeviceMemoryProperties memory;
    std::vector<VkQueueFamilyProperties> families;
    std::map<VkQueue, uint32_t> queues;
    std::map<VkSwapchainKHR, Swapchain> swaps;
    bool single_graphics_family;
    std::mutex mutex;
};

std::mutex registry;
std::map<void *, Instance> instances;
std::map<void *, std::unique_ptr<Device>> devices;
std::mutex publisher_mutex;

Device &device(const void *dispatchable) {
    const std::lock_guard lock(registry);
    return *devices.at(key(dispatchable));
}

#define DEV(fn) auto fn = reinterpret_cast<PFN_vk##fn>(d.get(d.handle, "vk" #fn))

template <typename T, typename Info>
T *chain(const Info *info, VkStructureType type, VkLayerFunction function) {
    for (auto *p = reinterpret_cast<const VkBaseInStructure *>(info->pNext);
         p; p = p->pNext) {
        if (p->sType != type) continue;
        auto *candidate = reinterpret_cast<T *>(const_cast<VkBaseInStructure *>(p));
        if (candidate->function == function) return candidate;
    }
    return nullptr;
}

VkResult API create_instance(const VkInstanceCreateInfo *info,
                             const VkAllocationCallbacks *alloc, VkInstance *out) {
    auto *link = chain<VkLayerInstanceCreateInfo>(
        info, VK_STRUCTURE_TYPE_LOADER_INSTANCE_CREATE_INFO, VK_LAYER_LINK_INFO);
    if (!link || !link->u.pLayerInfo) return VK_ERROR_INITIALIZATION_FAILED;
    auto *next = link->u.pLayerInfo;
    auto get = next->pfnNextGetInstanceProcAddr;
    auto phys = next->pfnNextGetPhysicalDeviceProcAddr;
    auto create = reinterpret_cast<PFN_vkCreateInstance>(get(nullptr, "vkCreateInstance"));
    link->u.pLayerInfo = next->pNext;
    auto result = create(info, alloc, out);
    if (result == VK_SUCCESS) {
        const std::lock_guard lock(registry);
        instances.emplace(key(*out), Instance{*out, get, phys});
    }
    return result;
}

void API destroy_instance(VkInstance handle, const VkAllocationCallbacks *alloc) {
    PFN_vkDestroyInstance destroy;
    {
        const std::lock_guard lock(registry);
        auto entry = instances.find(key(handle));
        destroy = reinterpret_cast<PFN_vkDestroyInstance>(
            entry->second.get(handle, "vkDestroyInstance"));
        instances.erase(entry);
    }
    destroy(handle, alloc);
}

VkResult API create_device(VkPhysicalDevice physical, const VkDeviceCreateInfo *info,
                           const VkAllocationCallbacks *alloc, VkDevice *out) {
    auto *link = chain<VkLayerDeviceCreateInfo>(
        info, VK_STRUCTURE_TYPE_LOADER_DEVICE_CREATE_INFO, VK_LAYER_LINK_INFO);
    if (!link || !link->u.pLayerInfo) return VK_ERROR_INITIALIZATION_FAILED;
    auto *next = link->u.pLayerInfo;
    VkInstance instance;
    {
        const std::lock_guard lock(registry);
        instance = instances.at(key(physical)).handle;
    }
    auto get = next->pfnNextGetInstanceProcAddr;
    auto create = reinterpret_cast<PFN_vkCreateDevice>(get(instance, "vkCreateDevice"));
    auto d = std::make_unique<Device>();
    d->get = next->pfnNextGetDeviceProcAddr;
    d->physical = physical;
    d->surface_caps = reinterpret_cast<PFN_vkGetPhysicalDeviceSurfaceCapabilitiesKHR>(
        get(instance, "vkGetPhysicalDeviceSurfaceCapabilitiesKHR"));
    auto *callbacks = chain<VkLayerDeviceCreateInfo>(
        info, VK_STRUCTURE_TYPE_LOADER_DEVICE_CREATE_INFO, VK_LOADER_DATA_CALLBACK);
    d->set_loader_data = callbacks ? callbacks->u.pfnSetDeviceLoaderData : nullptr;
    auto properties = reinterpret_cast<PFN_vkGetPhysicalDeviceMemoryProperties>(
        get(instance, "vkGetPhysicalDeviceMemoryProperties"));
    properties(physical, &d->memory);
    auto families = reinterpret_cast<PFN_vkGetPhysicalDeviceQueueFamilyProperties>(
        get(instance, "vkGetPhysicalDeviceQueueFamilyProperties"));
    uint32_t count = 0;
    families(physical, &count, nullptr);
    d->families.resize(count);
    families(physical, &count, d->families.data());
    uint32_t graphics_families = 0;
    for (uint32_t i = 0; i < info->queueCreateInfoCount; ++i) {
        const auto family = info->pQueueCreateInfos[i].queueFamilyIndex;
        if (d->families[family].queueFlags & VK_QUEUE_GRAPHICS_BIT) ++graphics_families;
    }
    d->single_graphics_family = graphics_families == 1;
    link->u.pLayerInfo = next->pNext;
    auto result = create(physical, info, alloc, out);
    if (result == VK_SUCCESS) {
        d->handle = *out;
        const std::lock_guard lock(registry);
        devices.emplace(key(*out), std::move(d));
    }
    return result;
}

void release(Device &d, Swapchain &s) {
    DEV(DestroyFence); DEV(DestroyCommandPool); DEV(UnmapMemory);
    DEV(DestroyBuffer); DEV(FreeMemory);
    if (s.fence) DestroyFence(d.handle, s.fence, nullptr);
    if (s.pool) DestroyCommandPool(d.handle, s.pool, nullptr);
    if (s.pixels) UnmapMemory(d.handle, s.memory);
    if (s.buffer) DestroyBuffer(d.handle, s.buffer, nullptr);
    if (s.memory) FreeMemory(d.handle, s.memory, nullptr);
}

void API destroy_device(VkDevice handle, const VkAllocationCallbacks *alloc) {
    auto &d = device(handle);
    DEV(DestroyDevice);
    for (auto &[_, swap] : d.swaps) release(d, swap);
    {
        const std::lock_guard lock(registry);
        devices.erase(key(handle));
    }
    DestroyDevice(handle, alloc);
}

void API get_queue(VkDevice handle, uint32_t family, uint32_t index, VkQueue *queue) {
    auto &d = device(handle);
    DEV(GetDeviceQueue);
    GetDeviceQueue(handle, family, index, queue);
    if (*queue) {
        const std::lock_guard lock(d.mutex);
        d.queues[*queue] = family;
    }
}

void API get_queue2(VkDevice handle, const VkDeviceQueueInfo2 *info, VkQueue *queue) {
    auto &d = device(handle);
    DEV(GetDeviceQueue2);
    GetDeviceQueue2(handle, info, queue);
    if (*queue && info->flags == 0) {
        const std::lock_guard lock(d.mutex);
        d.queues[*queue] = info->queueFamilyIndex;
    }
}

uint32_t pixel_format(VkFormat format) {
    switch (format) {
    case VK_FORMAT_B8G8R8A8_UNORM: case VK_FORMAT_B8G8R8A8_SRGB: return 1;
    case VK_FORMAT_R8G8B8A8_UNORM: case VK_FORMAT_R8G8B8A8_SRGB: return 2;
    default: return 0;
    }
}

VkResult API create_swap(VkDevice handle, const VkSwapchainCreateInfoKHR *info,
                         const VkAllocationCallbacks *alloc, VkSwapchainKHR *out) {
    auto &d = device(handle);
    DEV(CreateSwapchainKHR); DEV(GetSwapchainImagesKHR);
    Swapchain s{};
    s.extent = info->imageExtent;
    s.format = pixel_format(info->imageFormat);
    s.supported = s.format && info->imageColorSpace == VK_COLOR_SPACE_SRGB_NONLINEAR_KHR &&
        info->imageArrayLayers == 1 && info->preTransform == VK_SURFACE_TRANSFORM_IDENTITY_BIT_KHR &&
        !(info->flags & VK_SWAPCHAIN_CREATE_PROTECTED_BIT_KHR) && d.single_graphics_family;
    auto copy = *info;
    if (s.supported && !(copy.imageUsage & VK_IMAGE_USAGE_TRANSFER_SRC_BIT)) {
        VkSurfaceCapabilitiesKHR caps{};
        s.supported = d.surface_caps &&
            d.surface_caps(d.physical, info->surface, &caps) == VK_SUCCESS &&
            (caps.supportedUsageFlags & VK_IMAGE_USAGE_TRANSFER_SRC_BIT);
        if (s.supported) copy.imageUsage |= VK_IMAGE_USAGE_TRANSFER_SRC_BIT;
    }
    auto result = CreateSwapchainKHR(handle, &copy, alloc, out);
    if (result == VK_SUCCESS) {
        uint32_t count = 0;
        s.supported = s.supported &&
            GetSwapchainImagesKHR(handle, *out, &count, nullptr) == VK_SUCCESS && count;
        if (s.supported) {
            s.images.resize(count);
            s.supported = GetSwapchainImagesKHR(handle, *out, &count, s.images.data()) == VK_SUCCESS;
            s.images.resize(count);
        }
        const std::lock_guard lock(d.mutex);
        d.swaps.emplace(*out, std::move(s));
    }
    return result;
}

void API destroy_swap(VkDevice handle, VkSwapchainKHR swap, const VkAllocationCallbacks *alloc) {
    auto &d = device(handle);
    DEV(DestroySwapchainKHR);
    const std::lock_guard lock(d.mutex);
    auto entry = d.swaps.find(swap);
    if (entry != d.swaps.end()) {
        release(d, entry->second);
        d.swaps.erase(entry);
    }
    DestroySwapchainKHR(handle, swap, alloc);
}

bool allocate(Device &d, Swapchain &s, uint32_t family) {
    DEV(CreateBuffer); DEV(GetBufferMemoryRequirements); DEV(AllocateMemory);
    DEV(BindBufferMemory); DEV(MapMemory); DEV(CreateCommandPool);
    DEV(AllocateCommandBuffers); DEV(CreateFence);

    VkBufferCreateInfo buf{VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO};
    buf.size = VkDeviceSize(s.extent.width) * s.extent.height * 4;
    buf.usage = VK_BUFFER_USAGE_TRANSFER_DST_BIT;
    if (CreateBuffer(d.handle, &buf, nullptr, &s.buffer) != VK_SUCCESS) return false;
    VkMemoryRequirements requirements{};
    GetBufferMemoryRequirements(d.handle, s.buffer, &requirements);

    int type = -1;
    for (uint32_t i = 0; i < d.memory.memoryTypeCount; ++i) {
        const auto flags = d.memory.memoryTypes[i].propertyFlags;
        if (!(requirements.memoryTypeBits & (1u << i)) ||
            !(flags & VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT)) continue;
        if (type < 0 || (flags & VK_MEMORY_PROPERTY_HOST_CACHED_BIT)) type = int(i);
        if (flags & VK_MEMORY_PROPERTY_HOST_CACHED_BIT) break;
    }
    if (type < 0) return false;
    s.coherent = d.memory.memoryTypes[type].propertyFlags & VK_MEMORY_PROPERTY_HOST_COHERENT_BIT;
    VkMemoryAllocateInfo mem{VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO};
    mem.allocationSize = requirements.size;
    mem.memoryTypeIndex = uint32_t(type);
    if (AllocateMemory(d.handle, &mem, nullptr, &s.memory) != VK_SUCCESS ||
        BindBufferMemory(d.handle, s.buffer, s.memory, 0) != VK_SUCCESS ||
        MapMemory(d.handle, s.memory, 0, VK_WHOLE_SIZE, 0, &s.pixels) != VK_SUCCESS) return false;
    VkCommandPoolCreateInfo pool{VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO};
    pool.flags = VK_COMMAND_POOL_CREATE_TRANSIENT_BIT;
    pool.queueFamilyIndex = family;
    if (CreateCommandPool(d.handle, &pool, nullptr, &s.pool) != VK_SUCCESS) return false;
    VkCommandBufferAllocateInfo cmd{VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO};
    cmd.commandPool = s.pool;
    cmd.commandBufferCount = 1;
    if (AllocateCommandBuffers(d.handle, &cmd, &s.commands) != VK_SUCCESS ||
        !d.set_loader_data || d.set_loader_data(d.handle, s.commands) != VK_SUCCESS) return false;
    VkFenceCreateInfo fence{VK_STRUCTURE_TYPE_FENCE_CREATE_INFO};
    s.family = family;
    return CreateFence(d.handle, &fence, nullptr, &s.fence) == VK_SUCCESS;
}

VkResult API present(VkQueue queue, const VkPresentInfoKHR *info) {
    auto &d = device(queue);
    DEV(QueuePresentKHR);
    const std::lock_guard sender_lock(publisher_mutex);
    static aci::Publisher publisher;
    const auto start = aci::monotonic_ns();
    if (!publisher.ready(start) || info->swapchainCount != 1) return QueuePresentKHR(queue, info);
    const std::lock_guard lock(d.mutex);
    const auto swap = d.swaps.find(info->pSwapchains[0]);
    const auto q = d.queues.find(queue);
    const auto index = info->pImageIndices[0];
    if (swap != d.swaps.end() &&
        !publisher.matches(swap->second.extent.width, swap->second.extent.height))
        return QueuePresentKHR(queue, info); // Ignore unrelated or loading swapchains.
    if (swap == d.swaps.end() || !swap->second.supported || index >= swap->second.images.size() ||
        q == d.queues.end() || !(d.families[q->second].queueFlags & VK_QUEUE_GRAPHICS_BIT)) {
        publisher.fail("Unsupported swapchain (need SDR 8-bit, transfer source, identity transform and a graphics present queue)");
        return QueuePresentKHR(queue, info);
    }
    auto &s = swap->second;
    if ((!s.fence && !allocate(d, s, q->second)) || s.family != q->second) {
        publisher.fail("Cannot allocate Vulkan readback resources on the present queue");
        return QueuePresentKHR(queue, info);
    }

    DEV(ResetCommandPool); DEV(ResetFences); DEV(BeginCommandBuffer); DEV(CmdPipelineBarrier);
    DEV(CmdCopyImageToBuffer); DEV(EndCommandBuffer); DEV(QueueSubmit); DEV(WaitForFences);
    DEV(InvalidateMappedMemoryRanges);
    VkCommandBufferBeginInfo begin{VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO};
    begin.flags = VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT;
    if (ResetCommandPool(d.handle, s.pool, 0) != VK_SUCCESS ||
        ResetFences(d.handle, 1, &s.fence) != VK_SUCCESS ||
        BeginCommandBuffer(s.commands, &begin) != VK_SUCCESS) {
        publisher.fail("Cannot prepare Vulkan readback commands");
        return QueuePresentKHR(queue, info);
    }
    VkImageMemoryBarrier image{VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER};
    image.oldLayout = VK_IMAGE_LAYOUT_PRESENT_SRC_KHR;
    image.newLayout = VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL;
    image.srcQueueFamilyIndex = image.dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
    image.image = s.images[index];
    image.subresourceRange = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1};
    image.dstAccessMask = VK_ACCESS_TRANSFER_READ_BIT;
    CmdPipelineBarrier(s.commands, VK_PIPELINE_STAGE_TRANSFER_BIT, VK_PIPELINE_STAGE_TRANSFER_BIT,
                       0, 0, nullptr, 0, nullptr, 1, &image);
    VkBufferImageCopy region{};
    region.imageSubresource = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 0, 1};
    region.imageExtent = {s.extent.width, s.extent.height, 1};
    CmdCopyImageToBuffer(s.commands, image.image, image.newLayout, s.buffer, 1, &region);
    std::swap(image.oldLayout, image.newLayout);
    image.srcAccessMask = VK_ACCESS_TRANSFER_READ_BIT;
    image.dstAccessMask = 0;
    VkBufferMemoryBarrier buffer{VK_STRUCTURE_TYPE_BUFFER_MEMORY_BARRIER};
    buffer.srcAccessMask = VK_ACCESS_TRANSFER_WRITE_BIT;
    buffer.dstAccessMask = VK_ACCESS_HOST_READ_BIT;
    buffer.srcQueueFamilyIndex = buffer.dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
    buffer.buffer = s.buffer;
    buffer.size = VK_WHOLE_SIZE;
    CmdPipelineBarrier(s.commands, VK_PIPELINE_STAGE_TRANSFER_BIT,
                       VK_PIPELINE_STAGE_HOST_BIT | VK_PIPELINE_STAGE_BOTTOM_OF_PIPE_BIT,
                       0, 0, nullptr, 1, &buffer, 1, &image);
    if (EndCommandBuffer(s.commands) != VK_SUCCESS) {
        publisher.fail("Cannot record Vulkan readback commands");
        return QueuePresentKHR(queue, info);
    }
    const std::vector<VkPipelineStageFlags> stages(info->waitSemaphoreCount,
                                                  VK_PIPELINE_STAGE_TRANSFER_BIT);
    VkSubmitInfo submit{VK_STRUCTURE_TYPE_SUBMIT_INFO};
    submit.waitSemaphoreCount = info->waitSemaphoreCount;
    submit.pWaitSemaphores = info->pWaitSemaphores;
    submit.pWaitDstStageMask = stages.data();
    submit.commandBufferCount = 1;
    submit.pCommandBuffers = &s.commands;
    const auto submitted = QueueSubmit(queue, 1, &submit, s.fence);
    if (submitted != VK_SUCCESS) {
        publisher.fail("Vulkan readback submission failed");
        return submitted;
    }
    const auto waited = WaitForFences(d.handle, 1, &s.fence, VK_TRUE, UINT64_MAX);
    if (waited != VK_SUCCESS) {
        publisher.fail("Vulkan readback fence failed");
        return waited;
    }

    // The copy submission consumed the application's wait semaphores. The image
    // is back in PRESENT_SRC_KHR and the fence guarantees completion before present.
    auto present_info = *info;
    present_info.waitSemaphoreCount = 0;
    present_info.pWaitSemaphores = nullptr;
    const auto result = QueuePresentKHR(queue, &present_info);
    if (result == VK_SUCCESS || result == VK_SUBOPTIMAL_KHR) {
        VkMappedMemoryRange range{VK_STRUCTURE_TYPE_MAPPED_MEMORY_RANGE};
        range.memory = s.memory;
        range.size = VK_WHOLE_SIZE;
        if (!s.coherent && InvalidateMappedMemoryRanges(d.handle, 1, &range) != VK_SUCCESS) {
            publisher.fail("Vulkan readback memory invalidation failed");
        } else {
            publisher.publish(s.extent.width, s.extent.height, s.format, start, s.pixels);
        }
    }
    return result;
}

PFN_vkVoidFunction API get_device_proc(VkDevice handle, const char *name) {
    if (!handle) return nullptr;
    auto next = device(handle).get(handle, name);
    if (!next) return nullptr;
#define HOOK(vk, impl) if (!strcmp(name, "vk" #vk)) return reinterpret_cast<PFN_vkVoidFunction>(impl)
    HOOK(GetDeviceProcAddr, get_device_proc);
    HOOK(DestroyDevice, destroy_device);
    HOOK(GetDeviceQueue, get_queue);
    HOOK(GetDeviceQueue2, get_queue2);
    HOOK(CreateSwapchainKHR, create_swap);
    HOOK(DestroySwapchainKHR, destroy_swap);
    HOOK(QueuePresentKHR, present);
    return next;
}

PFN_vkVoidFunction API get_instance_proc(VkInstance handle, const char *name) {
    HOOK(GetInstanceProcAddr, get_instance_proc);
    HOOK(CreateInstance, create_instance);
    HOOK(GetDeviceProcAddr, get_device_proc);
    if (!handle) return nullptr;
    HOOK(CreateDevice, create_device);
    HOOK(DestroyInstance, destroy_instance);
    HOOK(DestroyDevice, destroy_device);
    HOOK(GetDeviceQueue, get_queue);
    HOOK(GetDeviceQueue2, get_queue2);
    HOOK(CreateSwapchainKHR, create_swap);
    HOOK(DestroySwapchainKHR, destroy_swap);
    HOOK(QueuePresentKHR, present);
#undef HOOK
    const std::lock_guard lock(registry);
    return instances.at(key(handle)).get(handle, name);
}

PFN_vkVoidFunction API get_physical_proc(VkInstance handle, const char *name) {
    const std::lock_guard lock(registry);
    auto get = instances.at(key(handle)).physical;
    return get ? get(handle, name) : nullptr;
}

} // namespace

EXPORT VkResult API vkNegotiateLoaderLayerInterfaceVersion(VkNegotiateLayerInterface *info) {
    if (!info || info->sType != LAYER_NEGOTIATE_INTERFACE_STRUCT ||
        info->loaderLayerInterfaceVersion < 2) return VK_ERROR_INITIALIZATION_FAILED;
    info->loaderLayerInterfaceVersion = 2;
    info->pfnGetInstanceProcAddr = get_instance_proc;
    info->pfnGetDeviceProcAddr = get_device_proc;
    info->pfnGetPhysicalDeviceProcAddr = get_physical_proc;
    return VK_SUCCESS;
}
