# BetterVisuals + FSR 1 + FSR 1.2 + Snapdragon GSR1

This repository builds an Android ARM64 Geode package with selectable spatial paths: Nearest, Bilinear, FSR 1, FSR 1.2 EASU+RCAS, SGSR1, and Lanczos 3.

## Target

- Geometry Dash 2.2081
- Geode Android ARM64
- Upstream source: https://github.com/ItMe12s/BetterVisuals (master)
- Qualcomm SGSR reference: https://github.com/SnapdragonGameStudios/snapdragon-gsr

## Build

A push to `main` starts `.github/workflows/android64.yml`. The workflow checks out BetterVisuals, applies `integration/apply_patch.py`, copies the dedicated SGSR1 and FSR 1.2 RCAS shaders plus the FSR 1.2 renderer into the upstream source tree, builds Android64 with the Geode build action, and uploads the resulting `.geode` package as an artifact.

The patch validates the Geode version string against the version tags supported by Geode before writing `mod.json`. The generated package must still pass CI and be tested in-game before it can be described as verified.

## Current implementation notes

- SGSR1 is exposed as a separate upscale option and uses BetterVisuals' existing post-process renderer.
- FSR 1 keeps BetterVisuals' original single-pass EASU path.
- FSR 1.2 is exposed as a separate two-pass renderer: EASU into an intermediate texture, followed by a dedicated RCAS shader into the display target. It has its own framebuffer and renderer lifecycle. Technically, FSR 1.2 is a revision within the FSR 1 family, so EASU remains the shared core; the added RCAS pass is what distinguishes this complete path from the existing EASU-only option.
- Both FSR choices expose the same five resolution presets: Ultra Quality 0.77, Quality 0.67, Balanced 0.59, Performance 0.50, Ultra Performance 0.33. Presets multiply the manual Render Scale; neither control overwrites the other.
- SGSR1 and Lanczos 3 keep independent reconstruction paths; all selectable spatial methods share the same internal-resolution presets.
- Shared presets: Ultra Performance 0.33, Performance 0.50, Balanced 0.59, Quality 0.67, Ultra Quality 0.77. Each multiplies the manual Render Scale.
- These are spatial upscalers, not FSR 2/3 or frame generation. AMD's FSR 1 documentation describes EASU and RCAS as the two stages of the FSR 1 technique.
- SGSR1 is an adapted GLSL ES 1.00 spatial shader using explicit texture taps in place of `textureGather`.
- Lanczos 3 is a spatial reconstruction filter, not AI upscaling; its 6x6 sampling kernel may cost more GPU time than Nearest/Bilinear.
- Runtime image quality, device compatibility, and performance still require physical Android testing. Do not treat SGSR1 as Qualcomm-certified or device-verified.

## Third-party license

The shader adaptation is marked BSD-3-Clause. See `integration/SGSR1-LICENSE-NOTICE.txt` and the upstream license:
https://github.com/SnapdragonGameStudios/snapdragon-gsr/blob/main/LICENSE
