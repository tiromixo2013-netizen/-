# Frame Generation integration status

## Target contract
- One ordinary `.geode` package; no custom Loader, replacement APK, root, or companion app.
- Preserve the BetterVisuals mod ID and the independent FSR1 and SGSR1 paths.
- Frame Generation is opt-in and disabled by default.
- Never advance Geometry Dash simulation on a generated-frame callback.
- Any capture, GL, shader, or context failure must fall back to normal rendering.

## Geode-only implementation

The Android integration now targets two Cocos render boundaries exposed to Geode hooks:

1. `CCDirector::drawScene` controls whether a callback advances the game scene or presents a retained source frame.
2. `CCEGLView::swapBuffers` replaces a captured real frame with the optical-flow midpoint at the end of a normal render.
3. A later draw callback presents the retained current source frame without running the scene update a second time.
4. The post-process capture is forced while Frame Generation is enabled so the frame history is sourced from the completed output image.

This replaces the previous custom Loader callback design. The old `loader-patch` files are legacy reference material and are not part of the Android64 workflow.

## Verification boundary

A successful Android64 build proves that the C++ code compiles and packages; it does not prove that the game actually presents both frames. Physical-device tests are still required for:
- hook execution order and source/midpoint/source cadence,
- 60/90 Hz pacing and missed deadlines,
- optical-flow artifacts and HUD ghosting,
- input latency and simulation correctness,
- menus, pause, background/resume, GL context recreation,
- coexistence with other mods that hook Cocos rendering.

Do not advertise doubled FPS until these tests pass on-device.
