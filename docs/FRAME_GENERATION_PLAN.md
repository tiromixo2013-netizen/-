# Frame Generation integration plan

## Scope and compatibility contract

This branch adds Frame Generation to the BetterVisuals GSR1 integration overlay. It must not replace or rewrite the existing BetterVisuals, FSR 1, FSR 1.2, or SGSR1 paths.

Frame Generation is opt-in and defaults to off. When off, the mod must not allocate frame-generation textures, run motion estimation, add render passes, or change presentation timing. If any prerequisite fails while enabled, rendering must fall back to the original BetterVisuals path for that frame (and disable the experimental path after repeated failures).

## What the upstream renderer provides

The upstream BetterVisuals source wraps the active game-layer or full-scene `visit()` call in `renderSceneWithPostProcessing()`. It captures the scene into an internal framebuffer, runs configured post-processing, then presents the result to the caller framebuffer.

This is a useful source-frame boundary, but it is not itself a frame-generation implementation. The Geode Android `CCEGLView::swapBuffers()` implementation is empty, so hooking that method alone will not insert an image into the display stream. A complete implementation must trace the Android Java `GLSurfaceView` callback and automatic EGL swap, then prove a safe way to present an interpolated image between two real game frames. A second `eglSwapBuffers` call inside the native callback is not assumed to work: it may block, be followed by the framework's normal swap, or fail to create a separately displayed refresh.

## Required pipeline

1. **Frame capture:** retain two completed post-processed color frames in GPU textures. Avoid synchronous GPU readback.
2. **Motion estimation:** estimate bidirectional motion between consecutive frames using GLES shaders. Start at reduced resolution and validate shader precision and texture formats on the target GPU.
3. **Disocclusion handling:** detect inconsistent forward/backward flow and newly exposed regions; blend or reject unreliable interpolation there.
4. **UI treatment:** preserve crisp HUD/text by excluding UI regions from interpolation where reliable masks can be obtained. If no trustworthy mask exists, use conservative fallback rather than smearing the HUD.
5. **Interpolation:** synthesize a midpoint frame from both source frames and motion fields. Never present it as a real game simulation tick.
6. **Presentation and pacing:** insert the synthesized frame only through a verified Android swap/presentation hook. Preserve original input sampling and simulation cadence; measure added latency and missed deadlines.
7. **Fallback:** bypass interpolation on scene changes, pause/menu transitions, invalid timestamps, resize/context loss, insufficient GPU capability, or missed frame budget.

## Milestones and acceptance gates

- [x] Inspect the Geode Android Cocos view API: `CCEGLView::swapBuffers()` exists but its Android implementation is empty, so it is not a usable presentation hook by itself.
- [ ] Trace the Android Java `GLSurfaceView` render callback and its automatic EGL buffer swap; determine whether an extra presentation can be scheduled without modifying Geode's loader or Java host.
- [ ] Add an off-by-default setting without changing the default renderer path.
- [ ] Implement asynchronous GPU frame history capture and lifecycle reset.
- [ ] Implement and test motion estimation and disocclusion shaders independently.
- [ ] Implement midpoint interpolation and UI-safe fallback.
- [ ] Add a presentation scheduler with strict deadline/fallback behavior.
- [ ] Build the Android64 `.geode` package in CI.
- [ ] Test on a physical Android device; measure actual displayed cadence, GPU time, memory, and input latency.

## Non-goals

- Do not claim that a second game simulation tick is being generated.
- Do not claim that CPU commands or every Geometry Dash object has been tracked.
- Do not advertise doubled FPS until the presentation hook and physical-device measurements prove that additional frames are actually displayed.
- Do not enable the experimental path by default.
