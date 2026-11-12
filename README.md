# BetterVisuals + Snapdragon GSR1 + FSR quality presets

This repository builds an Android ARM64 Geode package that adds a separate SGSR1-labelled spatial upscale pass and independent FSR 1 quality presets to BetterVisuals.

## Target

- Geometry Dash 2.2081
- Geode Android ARM64
- Upstream source: https://github.com/ItMe12s/BetterVisuals (master)
- Qualcomm SGSR reference: https://github.com/SnapdragonGameStudios/snapdragon-gsr

## Build

A push to `main` starts `.github/workflows/android64.yml`. The workflow checks out BetterVisuals, applies `integration/apply_patch.py`, copies the SGSR1 and FSR RCAS shaders into the upstream shader directories, builds Android64 with the Geode build action, and uploads the resulting `.geode` package as the `BetterVisuals-GSR1-Android64` artifact.

The patch validates the Geode version string against the version tags supported by Geode before writing `mod.json`. The generated package must still pass CI and be tested in-game before it can be described as verified.

## Current implementation notes

- SGSR1 is exposed as a separate upscale option and uses BetterVisuals' existing post-process renderer.
- FSR remains BetterVisuals' existing FSR 1 spatial upscaler; it is not FSR 2/3 or frame generation.
- Five FSR quality presets independently multiply the manual Render Scale: Ultra Quality 0.77, Quality 0.67, Balanced 0.59, Performance 0.50, Ultra Performance 0.33. The two scale controls multiply together.
- The FSR preset selector is conditionally enabled through a boolean saved value when FSR 1 is selected.
- SGSR1 is an adapted GLSL ES 1.00 spatial shader using explicit texture taps in place of `textureGather`.
- Runtime image quality, device compatibility, and performance still require physical Android testing. Do not treat SGSR1 as Qualcomm-certified or device-verified.

## Third-party license

The shader adaptation is marked BSD-3-Clause. See `integration/SGSR1-LICENSE-NOTICE.txt` and the upstream license:
https://github.com/SnapdragonGameStudios/snapdragon-gsr/blob/main/LICENSE
