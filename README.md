# BetterVisuals + FSR 1 + Snapdragon GSR1 + Frame Generation

This repository builds an Android ARM64 Geode package for Geometry Dash 2.2081.

## Frame Generation design

Frame Generation is implemented inside the `.geode` mod. It does not require a custom Geode Loader binary, replacement APK, root, or a companion application.

On Android, the mod hooks the Cocos2d `CCDirector::drawScene` and `CCEGLView::swapBuffers` boundaries:
- A normal game render captures the completed post-processed frame.
- At the swap boundary, the mod attempts to draw an optical-flow midpoint from the previous and current captures.
- On the next Cocos draw callback, the mod presents the retained current source frame and skips the game scene update for that callback. This keeps physics and input simulation from advancing twice.
- If capture, shader presentation, or the GL context fails, the hook falls back to ordinary Cocos rendering.

The option is experimental and disabled by default. The implementation must still be verified on a physical Android device: the Cocos hook order, actual display cadence, GPU deadline, pause/menu transitions, context loss, and compatibility with other mods are not proven by a successful build. Do not assume that a doubled display cadence is guaranteed on every device or refresh mode.

## Upscaling

- FSR 1 uses the upstream EASU spatial upscaling path.
- SGSR1 is a separate adapted GLSL ES 1.00 spatial shader. It is not Qualcomm-certified.
- Frame Generation is independent from both spatial upscalers.

## Build

A push to `main` or `feature/frame-generation-prototype` runs the Android64 Geode build and uploads a single `.geode` artifact. The workflow does not build a custom Loader or APK.

## Target and licenses

- Geometry Dash 2.2081, Android ARM64.
- Upstream BetterVisuals: https://github.com/ItMe12s/BetterVisuals
- Qualcomm SGSR reference: https://github.com/SnapdragonGameStudios/snapdragon-gsr
- See `integration/SGSR1-LICENSE-NOTICE.txt` for shader license attribution.
