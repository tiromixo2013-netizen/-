# BetterVisuals + FSR 1 + Snapdragon GSR1

This repository builds an Android ARM64 Geode package with the upstream FSR 1 spatial upscaler and an independent SGSR1-inspired spatial upscaler.

## Target

- Geometry Dash 2.2081
- Geode Android ARM64
- Upstream source: https://github.com/ItMe12s/BetterVisuals (master)
- Qualcomm SGSR reference: https://github.com/SnapdragonGameStudios/snapdragon-gsr

## Build

A push to `main` or `feature/frame-generation-prototype` starts `.github/workflows/android64.yml`. The workflow checks out BetterVisuals, applies `integration/apply_patch.py`, copies the SGSR1 shader into the upstream source tree, builds Android64 with the Geode build action, and uploads the resulting `.geode` package as an artifact.

The patch validates the Geode version string against the version tags supported by Geode before writing `mod.json`. The generated package must still pass CI and be tested in-game before it can be described as verified.

## Current implementation notes

- FSR 1 retains the upstream EASU spatial upscaling path.
- SGSR1 is exposed as a separate upscale option and uses BetterVisuals' existing post-process renderer.
- FSR 1 quality presets multiply the manual Render Scale and apply only when FSR 1 is selected.
- FSR 1.2 / RCAS has been removed from the source patch, build workflow, settings, and packaged build inputs.
- These are spatial upscalers, not FSR 2/3 or frame generation.
- SGSR1 is an adapted GLSL ES 1.00 spatial shader using explicit texture taps in place of `textureGather`.
- Runtime image quality, device compatibility, and performance still require physical Android testing. Do not treat SGSR1 as Qualcomm-certified or device-verified.

## Third-party license

The shader adaptation is marked BSD-3-Clause. See `integration/SGSR1-LICENSE-NOTICE.txt` and the upstream license:
https://github.com/SnapdragonGameStudios/snapdragon-gsr/blob/main/LICENSE
