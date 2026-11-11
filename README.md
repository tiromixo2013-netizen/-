# BetterVisuals + Snapdragon Game Super Resolution 1

This repository tracks an Android-focused integration of Snapdragon Game Super Resolution 1 (SGSR1) into the existing BetterVisuals Geode post-processing pipeline.

## Target

- Geometry Dash: 2.2081
- Geode mod, Android ARM64
- Primary test device class: Qualcomm Adreno 610 (Snapdragon 680)
- Scope for this stage: SGSR1 only

## Upstream projects

- BetterVisuals: https://github.com/ItMe12s/BetterVisuals
- Snapdragon Game Super Resolution: https://github.com/SnapdragonGameStudios/snapdragon-gsr
- SGSR1 mobile fragment shader: https://github.com/SnapdragonGameStudios/snapdragon-gsr/blob/main/sgsr/v1/include/glsl/sgsr1_shader_mobile.frag

## Integration notes

BetterVisuals already has a render-scale presentation pass and ping-pong post-processing targets. SGSR1 should be added as a selectable presentation/upscale method, operating on the lower-resolution scene texture and writing to the existing output framebuffer.

The upstream SGSR1 mobile shader is GLSL ES 3.x and uses `textureGather`. BetterVisuals' generic shader compiler currently prepends a GLSL ES 1.00 prelude for mobile. The SGSR1 pass therefore needs its own GLES 3.1-compatible shader compilation path; simply inserting the upstream fragment text into the existing generic shader renderer is not compatible.

The implementation must:
1. Keep the existing Nearest, Bilinear, and FSR 1 methods intact.
2. Add SGSR1 as a separate selectable upscale method.
3. Supply input texture dimensions and reciprocal dimensions through the SGSR1 `ViewportInfo` uniform.
4. Restore GL state and texture sampling state after the pass.
5. Fail safely if the active GLES context cannot compile the SGSR1 shader.
6. Build the Android64 Geode package and verify the produced artifact before publishing it.

## Status

- [x] Confirm upstream BetterVisuals render pipeline and settings.
- [x] Confirm the official SGSR1 mobile shader and BSD-3-Clause license.
- [ ] Add the dedicated GLES 3.x SGSR1 renderer.
- [ ] Add the SGSR1 setting and pipeline selection.
- [ ] Build Android ARM64 with Geometry Dash 2.2081 metadata.
- [ ] Verify the build artifact and publish a release.

No compiled mod is published by this repository yet.

## Third-party license

The SGSR1 shader is provided by Qualcomm Innovation Center, Inc. under the BSD 3-Clause license. Any redistributed source or binary containing that shader must retain the required copyright, conditions, and disclaimer. See the upstream license:
https://github.com/SnapdragonGameStudios/snapdragon-gsr/blob/main/LICENSE
