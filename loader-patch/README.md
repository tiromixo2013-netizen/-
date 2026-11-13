# Android Loader Frame Generation bridge

The authoritative integration script is `apply_loader_patch.py`. It targets Geode Loader commit `d22af2464ec97ab6c0fbef18004e82f3d2f36713` and applies exact, unique source replacements to:

- `loader/include/Geode/cocos/platform/android/java/src/org/cocos2dx/lib/Cocos2dxRenderer.java`
- `loader/include/Geode/cocos/platform/android/jni/Java_org_cocos2dx_lib_Cocos2dxRenderer.cpp`

Run it from any machine with Python 3 and a Geode Loader checkout:

```sh
python3 loader-patch/apply_loader_patch.py /path/to/geode
```

It adds only the Java render-loop phase state, JNI presentation callback, and exported C ABI registration function `GeodeSetFrameGenerationPresentCallback`. It does not alter Geode mod IDs, manifests, dependency discovery, package scanning, or mod loading.

## Runtime contract

The mod registers `bool callback(int phase)` through the exported C ABI.

- Phase 0 runs after one ordinary `nativeRender()`. The mod captures the completed post-processed image during that render, then draws the previous game image. Returning true schedules phase 1 for the next GLSurfaceView callback.
- Phase 1 draws the optical-flow midpoint between retained previous/current images. It does not call `nativeRender()`, so game simulation, input, actions, and physics are not advanced a second time.
- A false return falls back to ordinary game rendering.

Android's GLSurfaceView performs its normal EGL presentation after each `onDrawFrame()`; this bridge does not call `eglSwapBuffers()` manually.

## Build and verification boundary

The repository workflow validates the patcher and builds the `.geode` mod. It does **not** build a custom Loader binary or APK. A separate Android Loader build and APK packaging step is required to produce an installable paired Loader. Device testing is required to verify refresh cadence, GPU budget, latency, symbol visibility, and compatibility.

The mod keeps its existing Geode ID `tiromixo2013.bettervisuals-gsr`; Frame Generation is disabled by default and requires this paired Loader bridge.
