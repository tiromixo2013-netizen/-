# Android Loader Frame Generation bridge (experimental)

This patch targets Geode Loader commit `d22af2464ec97ab6c0fbef18004e82f3d2f36713`.

It adds a Java render-loop phase switch and a narrow native callback ABI without changing Geode's mod manifest, package ID, dependency discovery, or mod-loading code.

## Callback contract

The mod exports/registers a function with the C ABI:

```cpp
using GeodeFrameGenerationPresentCallback = bool (*)(int phase);
extern "C" void GeodeSetFrameGenerationPresentCallback(
    GeodeFrameGenerationPresentCallback callback
);
```

The callback executes on the GLSurfaceView GL thread while the EGL context is current.

- phase 0: after one real `nativeRender()`, draw the delayed previous game frame to the default framebuffer and return true only when a valid delayed source frame was drawn.
- phase 1: draw the interpolated midpoint between the delayed source and the newest captured game frame. Do not call `CCDirector::mainLoop()`, update actions, physics, input, or game objects.
- return false on missing history, resize/context loss, scene cut, shader failure, or missed GPU budget. The Java renderer falls back to normal game rendering.

This creates a one-game-frame presentation delay while the game simulation advances on alternate display callbacks. It is deliberately not enabled by default. A mod must register a callback and implement source-frame capture plus both presentation phases before the Loader will insert frames.

## Important status

This is a **Loader source patch**, not a ready-to-install Loader binary. The existing workflow builds only the BetterVisuals `.geode` mod and does not build or package a custom Geode Loader/APK. The patch must be applied to a custom Loader build and tested on a physical Android device before claiming doubled displayed FPS. The current interpolation renderer still needs to be refactored to implement the callback contract; until then, the existing in-mod interpolation option remains a preview/replacement path, not true frame generation.

The patch does not touch `main`, does not replace the Geode mod loader, and does not change `tiromixo2013.bettervisuals-gsr`.
