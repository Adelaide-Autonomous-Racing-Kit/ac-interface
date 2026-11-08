# Headless Assetto Corsa

This is an opt-in CrossOver launch path for the existing Monza/Audi collection
worker. It captures the Vulkan swapchain presented by `acs.exe`, copies it once
from GPU to CPU, and publishes the latest complete frame to ACI. The desktop
backend remains the default; selecting `images.backend: desktop` uses the
existing PyAV capture (`x11grab` on Linux).

**Validation status:** the default agent drove real Assetto Corsa at Monza
and recorded direct frames on private Xvfb. The Agent Dashboard was on the
desktop and the game window was confined to Xvfb. An independent Steam
bottle has not been tested.

## Run it

From this worktree, using the original project's prepared virtualenv, runtime
assets, and AC-MPC checkout:

```sh
make -C tools/headless
tools/headless/run.sh --display-provider xvfb --check-display
tools/headless/run.sh --display-provider xvfb --check
tools/headless/run.sh --display-provider xvfb
```

The wrapper locates the original `ac-mpc-run` via the common Git directory.
Set `AC_MPC_RUNTIME` to its absolute path if the layout differs. The build needs
a C++17 compiler and Vulkan development headers. The Xvfb provider needs
`Xvfb`, `xvfb-run` and `xauth`. It still captures the game's Vulkan frame directly;
the X server supplies a display and startup input. This workstation's RTX 3090
was verified with that display provider using the synthetic Vulkan test.

For Gamescope, use `tools/headless/run.sh --check-display` first, then omit
`--display-provider xvfb` in the commands above. Use `--gamescope /path/to/gamescope`
if needed. Select a build with `--backend headless` and working XTEST (libei).
The tested 3.16.11 package started Xwayland and delivered frames but reported no
libei and crashed during shutdown; use Xvfb for the first real AC test here.

Prepare an independent CrossOver bottle named `Assetto_Corsa_Headless` (or pass
`--bottle NAME`). Install or duplicate AC, Steam and the existing `acs.server`
Python setup into that bottle. Confirm it can start Steam/AC and is authorized
to play, ideally offline for an isolated test. Close its processes before the
run. Do not run the desktop collector at the same time; both use telemetry port
6002. The runner starts its own Steam instance in this mode.

CrossOver may link `drive_c/users/crossover/Documents` to the host. In the
**new bottle**, use an independent Documents directory with its own
`Assetto Corsa/cfg` and setups, and independent Steam and game files. The
supervisor rejects paths outside the bottle or known shared files before
staging settings. The new bottle's game directory needs `steam_appid.txt`
containing `244210`. The runner starts Steam and Wine on the private display;
it does not change graphics options, the controller configuration, or the
runtime's model and map. If Steam needs a login or an update, complete that
step in the isolated bottle before trying a headless lap.

Logs are under `tools/headless/logs`: `agent.log`, `steam.log`, DXVK logs if DXVK
is active, the effective INIs, telemetry, recording, and `result.json`. The
existing 1280×736 config and JPEG processing are reused. Stop with Ctrl+C.
For the original desktop path, run the original `ac-mpc-run/run-live-lap.sh`.

## Show only the Agent Dashboard

With Steam already running in the default CrossOver bottle, and AC and
telemetry port 6002 idle:

```sh
tools/headless/run.sh --display-provider xvfb --dashboard --reuse-desktop-steam
```

AC and its startup clicks stay on the private Xvfb display. Only the Python
Qt dashboard connects to your desktop. Use the Start/Stop buttons to control
Camera, Masks, Control, Predictions, Localisation, and Map independently.
Close the Agent Dashboard to stop the run. The supervisor
also stops at a completed lap or its existing time limit and restores
the staged game settings.

This mode reuses the existing Steam and Wine server; it hides the game window
without changing the desktop Steam session. For a session independent of
desktop Steam, prepare an isolated bottle as described above and omit
`--reuse-desktop-steam`. You can still use `--dashboard` to show the Qt window
when the game runs in that bottle.

## Test direct capture with the default desktop agent

If the existing CrossOver Steam session is open and AC and telemetry port 6002
are idle, run:

```sh
tools/headless/run.sh --desktop-proof --check
tools/headless/run.sh --desktop-proof
```

This launches the default Monza/Audi agent on the desktop for 20 seconds of
driving. The window is visible and startup setup clicks use that display.
Frames come from the Vulkan hook. The test reuses Steam, stops only the new
game and helper processes, and restores the staged INIs and setup. This
tests direct capture with the real game before changing the display.

## Frame delivery

The native layer is only enabled for the game subprocess and additionally
checks its Linux process name. It supports an SDR, unrotated, 8-bit RGBA/BGRA
swapchain on a graphics present queue with transfer-source support. The layer
waits for a Vulkan copy fence before passing the presentation to the driver;
this can affect rendering cadence. It does not encode video, crop a desktop,
change gamma, or fall back to another capture path. OpenGL/WineD3D, HDR,
multi-swapchain presents, and other sizes are outside this version. Wrong-size
swapchains are skipped; failure to start or continue presenting times out.

The receiver owns a private Unix sequenced-packet socket and one mapped frame
slot. Notifications wake the reader; a nonblocking file lock prevents partial
reads and lets the writer drop a frame if the reader holds the slot. There is
no growing frame queue and no reconnect after producer exit. Frames have a
monotonic sequence ID, with gaps for skipped or overwritten frames. ACI adds
`image_metadata` to direct observations and reports a cached image as stale on
telemetry-only updates. The timestamp in `present_hook_ns` is when the game
entered the hook before readback; `received_ns` is when Python finished copying
the frame. Both are host monotonic nanoseconds, not exposure or display times.
`source_drops` counts gaps before the receiver; `capture_drops` counts received
frames overwritten before the observation consumer. `recording/direct-frames.csv`
joins to the recorder's `frames.csv` on `host_observation_ns`. A camera frame and
the latest telemetry sample are independent.

## Evidence on this workstation

CrossOver 24.0.4 (build 37063), Linux NVIDIA driver 580.178.04 on the RTX 3090,
Vulkan loader 1.3.275, and Xwayland 23.2.6. Vulkan detected both the NVIDIA
device and llvmpipe; the synthetic test explicitly selected the discrete GPU.
The real game log confirmed DXVK `cxaddon-1.10.3-1-5-geba12f4` on the RTX
3090 with a 1280×736 BGRA8 swapchain. The existing Steam instance was on
desktop `:1`, and no separate bottle was present. NVIDIA's DRM modeset
setting was not readable as this user.

| Synthetic test (1280×736, 60 FPS target) | Result |
| --- | --- |
| Xvfb 21.1.12, no capture, 20 s | 1,199 presentations, 13.58 CPU seconds for renderer, mean sampled GPU utilization 13.7% |
| Xvfb with direct capture, 600 s | 35,938/35,938 presentations, 59.90 received FPS, zero frame drops |
| Direct Xvfb hook-to-receive | p50 12.94 ms, p95 15.09 ms, p99 17.40 ms, max 44.02 ms |
| Direct Xvfb CPU/GPU | 372.56 renderer CPU seconds, 20.43 receiver CPU seconds, mean sampled GPU utilization 28.7% |
| Gamescope 3.16.11 headless/Xwayland, 5 s | 300/300 presentations at 60.02 received FPS, p95 2.73 ms; compositor shutdown exited 139 |
| Vulkan validation on private Xvfb, 3 s | 180/180 frames; no validation messages |

The asymmetric moving pattern was checked for channel order, row orientation,
padding, and changing frames. During the ten-minute run the first and last
minute p95s were 14.73 and 16.00 ms. GPU figures are whole-device samples every
two seconds; the host desktop remained active and the synthetic runs have
different durations. These are not AC performance or baseline latency figures.
The native `VK_EXT_headless_surface` test crashed in the NVIDIA library even
with the layer disabled; the passing runs used private X displays instead.
The [upstream obs-vkcapture hook](https://github.com/nowrep/obs-vkcapture/tree/8a2c43295fae2ede8ffd382a1581281ceb6153c0)
was evaluated for this design. Its shared texture protocol does not send a
notification for each presentation. The implementation here uses Vulkan readback
directly so sequence and ownership are explicit.

The saved desktop Monza baseline at
`ac-mpc-run/logs/live-lap-20261108T040406Z` recorded 6,925 image/state pairs
(22.91 recording FPS) and a completed 309.322 s lap on MPC commit
`7840da3c0fc05fc6a3e4bb36141bc77ee154559c`. Its effective video settings were
1280×736, 2× AA, default post-process filter, saturation 100, clear weather and
sun angle −48°. Recording rate is not desktop capture or render rate.

The real AC desktop proof in
`logs/desktop-proof-20261108T044652.872893Z` recorded 511 distinct 1280×736
driving-camera JPEGs and matched each to its direct frame metadata and latest
telemetry. The recorder delivered 25.38 FPS across 20.10 s, with 4.87 ms p50
and 7.41 ms p95 hook-to-receive for the recorded frames. The swapchain ran
faster than the reader, so the latest-frame buffer skipped 1,916 presentations
over that span; the ACI buffer skipped another 541 before observation reads.
The displayed driving scene was verified in `recording/images/0000255.jpg`.
The runner stopped at its test limit, restored the staged settings, and
released port 6002. The existing Steam and Wine server stayed up. This was
not a timed lap or a headless AC run.

The private Xvfb run in `logs/headless-20261108T045912.872918Z` verified the
Agent Dashboard on desktop `:1` and the AC window at `(0, 0)` on private
display `:99`. Wine had reused coordinates from the larger desktop, putting
the window outside Xvfb's screen; placing it at the private screen's origin
allowed the existing setup and Drive clicks to work. Telemetry reached
80 km/h on track, and `recording/images/0000500.jpg` shows the driving camera
captured directly from the game. The run recorded 3,412 distinct frames in
154 seconds of driving before the agent stopped for lack of progress. It did
not complete a timed lap. The runner verified restoration of the staged game
settings.

To repeat the adapter check in a private X server:

```sh
make -C tools/headless smoke
PYTHONPATH="$PWD/src" xvfb-run -a -s '-screen 0 1280x736x24 -nolisten tcp' \
  "$AC_MPC_RUNTIME/.venv/bin/python" tools/headless/benchmark.py --xcb --seconds 600
PYTHONPATH="$PWD/src" "$AC_MPC_RUNTIME/.venv/bin/python" -m unittest discover -s tests -v
```

Use the real `ac-mpc-run` path for `AC_MPC_RUNTIME` in these standalone commands.
The tests use local Unix sockets and do not start AC.
