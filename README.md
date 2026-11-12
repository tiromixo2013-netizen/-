# BetterVisuals + Snapdragon GSR1 + AMD FSR EASU/RCAS

This repository builds an Android ARM64 Geode package that adds a Qualcomm SGSR1-labelled spatial upscale pass and completes BetterVisuals' FSR path with an RCAS sharpening pass.

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
- FSR is exposed as `FSR 1.2 (EASU + RCAS)`: EASU upscales into an output-sized intermediate target, then RCAS sharpens that result in a separate pass.
- The FSR RCAS pass uses a dedicated output-sized post-process pipeline so render-scale input and display output dimensions are not confused.
- Input inverse resolution is provided by the renderer's existing `u_invResolution` uniform.
- The renderer is reset when switching upscale modes and on the existing render-resource reset paths.
- The shader is an adapted GLSL ES 1.00 implementation using explicit texture taps in place of `textureGather`.
- Runtime image quality, device compatibility, and performance for both paths still require physical Android testing. Do not treat either shader path as Qualcomm-certified or device-verified.

## Third-party license

The shader adaptation is marked BSD-3-Clause. See `integration/SGSR1-LICENSE-NOTICE.txt` and the upstream license:
https://github.com/SnapdragonGameStudios/snapdragon-gsr/blob/main/LICENSE
