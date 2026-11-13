# Android Loader Frame Generation bridge

Target: Geode Loader commit `d22af2464ec97ab6c0fbef18004e82f3d2f36713`.

Apply `geode-android-frame-generation.patch` to that Geode source tree. It adds only:
- a Java render-loop phase bit to `Cocos2dxRenderer`;
- a JNI entry point used on the GLSurfaceView GL thread;
- the exported C ABI registration function `GeodeSetFrameGenerationPresentCallback`.

It does **not** alter Geode mod IDs, manifests, dependency discovery, package scanning, or the mod-loading pipeline.

## Runtime contract

The mod registers `bool callback(int phase)` through the exported C ABI.

- Phase 0 runs after one ordinary `nativeRender()`. The mod captures the completed post-processed image during that render, then draws the previous game image. Returning true schedules phase 1 for the next GLSurfaceView callback.
- Phase 1 draws the optical-flow midpoint between the retained previous/current images. It does not call `nativeRender()`, so game simulation, input, actions, and physics are not advanced a second time.
- A false return falls back to ordinary game rendering.

The Android framework performs its normal EGL buffer presentation after each `onDrawFrame()`. This patch does not call `eglSwapBuffers()` manually.

## Build and verification boundary

This is a source patch, not a prebuilt Loader or APK. The BetterVisuals workflow builds the `.geode` mod and validates that this patch applies cleanly to the pinned Loader source. A separate Android Loader build and APK packaging step is still required to produce an installable paired Loader. Device testing is required to verify refresh cadence, GPU budget, latency, and compatibility.

The mod keeps its existing Geode ID `tiromixo2013.bettervisuals-gsr`; Frame Generation is disabled by default and requires this paired Loader bridge.
