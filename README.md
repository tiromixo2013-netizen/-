# BetterVisuals + FSR 1 + FSR 1.2 + Snapdragon GSR1

This repository builds an Android ARM64 Geode package that adds three selectable spatial paths: the upstream FSR 1 path, a separate two-pass FSR 1.2 EASU+RCAS path, and an independent SGSR1 path.

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
- FSR 1.2 is a separate two-pass renderer: EASU into an intermediate texture, followed by a dedicated RCAS shader into the display target. It has its own framebuffer and renderer lifecycle; it is not an alias for FSR 1.
- Both FSR choices expose the same five resolution presets: Ultra Quality 0.77, Quality 0.67, Balanced 0.59, Performance 0.50, Ultra Performance 0.33. Presets multiply the manual Render Scale; neither control overwrites the other.
- SGSR1 has its own shader and renderer path and does not share the FSR preset scale.
- These are spatial upscalers, not FSR 2/3 or frame generation.
- SGSR1 is an adapted GLSL ES 1.00 spatial shader using explicit texture taps in place of `textureGather`.
- Runtime image quality, device compatibility, and performance still require physical Android testing. Do not treat SGSR1 as Qualcomm-certified or device-verified.

## Third-party license

The shader adaptation is marked BSD-3-Clause. See `integration/SGSR1-LICENSE-NOTICE.txt` and the upstream license:
https://github.com/SnapdragonGameStudios/snapdragon-gsr/blob/main/LICENSE
