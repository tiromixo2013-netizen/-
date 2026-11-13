# Android render-loop findings for Frame Generation

## Verified call chain

The Geode Android source currently uses this flow:

1. Android's `GLSurfaceView` owns the EGL window surface and GL render thread.
2. `Cocos2dxGLSurfaceView.setCocos2dxRenderer()` installs `Cocos2dxRenderer` as its `GLSurfaceView.Renderer`.
3. Android invokes `Cocos2dxRenderer.onDrawFrame(GL10)` on the GL thread.
4. `onDrawFrame()` calls the JNI method `Cocos2dxRenderer.nativeRender()`.
5. After the renderer callback returns, the GLSurfaceView/EGL framework performs the window-buffer presentation as part of its managed render loop.

The Geode Android native `CCEGLView::swapBuffers()` body is empty. The Java renderer source also does not expose a per-mod callback between `nativeRender()` and the framework-managed buffer swap.

## Consequence for a Geode-only mod

A normal native Geode mod can hook Cocos scene rendering and can run GLES commands while the GL context is current. It cannot safely create an additional independently displayed window frame merely by calling `eglSwapBuffers()` itself: the Java GLSurfaceView still owns the surface lifecycle and performs its own presentation after the callback. A second swap may block, consume the wrong buffer, or simply not produce an extra display refresh.

A true inserted-frame implementation needs a supported integration point in the Java/GLSurfaceView render loop (or a different verified presentation architecture) so that the interpolated image is drawn and presented at a separately scheduled display opportunity. This is outside the normal native Geode mod API and would require a loader/host change or a verified platform-specific hook. Do not patch private Android framework internals or guess EGL ownership.

## What can be implemented safely in the native mod

- Capture the completed post-processed scene into GPU textures on the existing GL thread.
- Estimate motion and synthesize an interpolated image.
- Present the synthesized image as the output of an existing render callback (frame replacement / smoothing), without claiming an increased display refresh or doubled FPS.
- Keep all work disabled by default and preserve the unmodified BetterVisuals path when disabled.

This safe native-only mode is not equivalent to true extra-frame presentation. It can be developed as a prototype, but the UI and documentation must label it accurately.

## Verified upstream source files

- `loader/include/Geode/cocos/platform/android/CCEGLView.cpp`: empty `CCEGLView::swapBuffers()`.
- `loader/include/Geode/cocos/platform/android/java/src/org/cocos2dx/lib/Cocos2dxGLSurfaceView.java`: installs the Cocos renderer into Android GLSurfaceView.
- `loader/include/Geode/cocos/platform/android/java/src/org/cocos2dx/lib/Cocos2dxRenderer.java`: `onDrawFrame()` calls `nativeRender()`; Java source does not expose a mod callback after native rendering and before managed presentation.
