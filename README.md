# BetterVisuals + Snapdragon Game Super Resolution 1

This repository builds an Android ARM64 Geode package that adds an SGSR1-labelled spatial upscale pass to BetterVisuals.

## Target

- Geometry Dash 2.2081
- Geode Android ARM64
- Upstream source: https://github.com/ItMe12s/BetterVisuals (master)
- Qualcomm SGSR reference: https://github.com/SnapdragonGameStudios/snapdragon-gsr

## Build

A push to `main` starts `.github/workflows/android64.yml`. The workflow checks out BetterVisuals, applies `integration/apply_patch.py`, copies `integration/Sgsr1Shader.cpp` into the upstream shader source directory, builds Android64 with the Geode build action, and uploads the resulting `.geode` package as the `BetterVisuals-GSR1-Android64` artifact.

The patch validates the Geode version string against the version tags supported by Geode before writing `mod.json`. The generated package must still pass CI and be tested in-game before it can be described as verified.

## Current implementation notes

- SGSR1 is exposed as a separate upscale option and uses BetterVisuals' existing post-process renderer.
- Input inverse resolution is provided by the renderer's existing `u_invResolution` uniform.
- The renderer is reset when switching upscale modes and on the existing render-resource reset paths.
- The shader is an adapted GLSL ES 1.00 implementation using explicit texture taps in place of `textureGather`.
- Runtime image quality, device compatibility, and performance have not yet been validated on a physical Android device. Do not treat the current shader as a Qualcomm-certified or device-verified implementation.

## Third-party license

The shader adaptation is marked BSD-3-Clause. See `integration/SGSR1-LICENSE-NOTICE.txt` and the upstream license:
https://github.com/SnapdragonGameStudios/snapdragon-gsr/blob/main/LICENSE
