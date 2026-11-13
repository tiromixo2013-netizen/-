# Frame Generation integration status

## Compatibility contract
- Preserve BetterVisuals, FSR 1, SGSR1, the existing Geode mod ID, and normal Geode mod discovery.
- Frame Generation remains opt-in and defaults to off.
- If the custom Loader bridge is missing or the renderer cannot produce valid history, use normal rendering.
- Never advance Geometry Dash simulation on a generated-frame callback.

## Implemented in this branch
1. The mod captures the final post-processed output into two GPU textures.
2. The existing bidirectional Lucas–Kanade shader synthesizes a temporal midpoint from the previous/current captures.
3. The mod registers a GL-thread callback with the custom Loader bridge using the exported `GeodeSetFrameGenerationPresentCallback` symbol.
4. The Loader's Java render loop advances the game on phase 0, presents the delayed source image, and on the next display callback presents the generated midpoint without calling `nativeRender()`.
5. If history, bridge registration, or rendering is unavailable, the Loader falls back to ordinary `nativeRender()`.
6. The setting `Enable Frame Generation` is exposed in the mod settings and is off by default.

## Important limitations
- The patch changes the Android Geode Loader source. A regular `.geode` package alone cannot activate the Java/JNI bridge.
- The current workflow checks that the Loader patch applies and builds the mod package; it does not yet build and package a custom Loader/APK.
- The callback uses `dlsym(RTLD_DEFAULT, ...)`; runtime symbol visibility must be confirmed in the paired Android Loader build.
- The midpoint shader is a lightweight heuristic Lucas–Kanade implementation. It does not have complete disocclusion reconstruction or HUD/text masks; HUD ghosting and artifacts are possible.
- Actual 2x displayed cadence is not guaranteed on every refresh rate/device. The game simulation is intentionally advanced once per two display callbacks only while the callback succeeds. GPU deadline misses and physical-device timing need measurement.

## Acceptance tests still required
- Build the custom Android64 Geode Loader and package it with the matching Geometry Dash Android host.
- Install the paired Loader and mod on a physical device.
- Confirm the mod is still discovered under `tiromixo2013.bettervisuals-gsr`.
- Measure presented refreshes, simulation tick cadence, GPU time, missed callbacks, input latency, pause/menu transitions, and context loss.
- Verify OFF exactly preserves normal rendering and ON safely falls back when the bridge is unavailable.
