# BetterVisuals + FSR 1 + Snapdragon GSR1 + Frame Generation

This repository builds an Android ARM64 Geode package with the upstream FSR 1 spatial upscaler and an independent SGSR1-inspired spatial upscaler, plus an experimental Android Loader Frame Generation bridge.

## Target

- Geometry Dash 2.2081
- Geode Android ARM64
- Upstream source: https://github.com/ItMe12s/BetterVisuals (master)
- Qualcomm SGSR reference: https://github.com/SnapdragonGameStudios/snapdragon-gsr
- Loader patch base: Geode commit `d22af2464ec97ab6c0fbef18004e82f3d2f36713`

## Build

A push to `main` or `feature/frame-generation-prototype` starts `.github/workflows/android64.yml`. The workflow checks out BetterVisuals, applies the SGSR1 and Frame Generation integration, validates the Geode mod ID and setting, verifies that the custom Loader patch applies cleanly, builds Android64 with the Geode build action, and uploads the resulting `.geode` package as an artifact.

The workflow currently builds the mod package and validates the Loader source patch; it does **not** build a custom Geode Loader binary or package an installable APK. The paired Loader source patch is in `loader-patch/geode-android-frame-generation.patch`.

## Current implementation notes

- FSR 1 retains the upstream EASU spatial upscaling path.
- SGSR1 is exposed as a separate upscale option and uses BetterVisuals' existing post-process renderer.
- FSR 1 quality presets multiply the manual Render Scale and apply only when FSR 1 is selected.
- The experimental Frame Generation path captures two completed post-processed GPU frames and uses bidirectional Lucas–Kanade optical flow to synthesize a midpoint.
- The mod registers a presentation callback through the custom Loader bridge. The Loader alternates between a real game render (one simulation update) and a generated midpoint presentation (no second simulation update). Android's normal GLSurfaceView/EGL presentation remains responsible for swapping the displayed buffer.
- The `Enable Frame Generation` setting is off by default and requires the matching custom Loader build. A standard Geode Loader cannot activate the Java/JNI bridge.
- The callback is designed to fall back to ordinary game rendering if it cannot present a valid source or generated frame. Actual doubled displayed cadence is not yet verified.
- The midpoint shader is experimental; HUD/text ghosting, scene transitions, GPU budget, input latency, refresh-rate pacing, and Android device compatibility require physical-device testing.
- FSR 1 and SGSR1 remain independent spatial upscalers; neither is removed or replaced by Frame Generation.
- SGSR1 is an adapted GLSL ES 1.00 spatial shader using explicit texture taps in place of `textureGather`. Do not treat it as Qualcomm-certified or device-verified.

## Third-party license

The shader adaptation is marked BSD-3-Clause. See `integration/SGSR1-LICENSE-NOTICE.txt` and the upstream license:
https://github.com/SnapdragonGameStudios/snapdragon-gsr/blob/main/LICENSE

