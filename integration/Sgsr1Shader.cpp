#include "../render/PostProcessRenderer.hpp"
#include "PostProcessShaders.hpp"

namespace bv::shaders::sgsr1 {

// Qualcomm Snapdragon Game Super Resolution 1, adapted from the official
// mobile GLSL implementation for the GLSL ES 1.00 shader interface used by
// BetterVisuals. textureGather is expanded into four nearest texture2D taps.
// Copyright (c) 2025 Qualcomm Innovation Center, Inc.
// SPDX-License-Identifier: BSD-3-Clause

constexpr char kFragmentSource[] = R"glsl(
precision highp float;
precision highp int;

uniform sampler2D u_texture;
uniform vec2 u_invResolution;
varying vec2 v_texCoord;

vec4 sgsrGatherGreen(vec2 uv)
{
    vec2 h = 0.5 * u_invResolution;
    // Gather order: upper-left, upper-right, lower-right, lower-left.
    return vec4(
        texture2D(u_texture, uv + vec2(-h.x,  h.y)).g,
        texture2D(u_texture, uv + vec2( h.x,  h.y)).g,
        texture2D(u_texture, uv + vec2( h.x, -h.y)).g,
        texture2D(u_texture, uv + vec2(-h.x, -h.y)).g
    );
}

float fastLanczos2(float x)
{
    float wA = x - 4.0;
    float wB = x * wA - wA;
    wA *= wA;
    return wB * wA;
}

vec2 weightY(float dx, float dy, float c, float std)
{
    float x = ((dx * dx) + (dy * dy)) * 0.55 + clamp(abs(c) * std, 0.0, 1.0);
    float w = fastLanczos2(x);
    return vec2(w, w * c);
}

void main()
{
    const float edgeThreshold = 8.0 / 255.0;
    const float edgeSharpness = 2.0;

    vec4 color = texture2D(u_texture, v_texCoord);
    vec2 imageSize = vec2(1.0) / u_invResolution;
    vec2 imgCoord = (v_texCoord * imageSize) + vec2(-0.5, 0.5);
    vec2 imgCoordPixel = floor(imgCoord);
    vec2 coord = imgCoordPixel * u_invResolution;
    vec2 pl = imgCoord - imgCoordPixel;

    vec4 left = sgsrGatherGreen(coord);
    float edgeVote = abs(left.z - left.y) + abs(color.g - left.y) + abs(color.g - left.z);

    if (edgeVote > edgeThreshold)
    {
        coord.x += u_invResolution.x;
        vec4 right = sgsrGatherGreen(coord + vec2(u_invResolution.x, 0.0));
        vec4 upDown;
        upDown.xy = sgsrGatherGreen(coord + vec2(0.0, -u_invResolution.y)).wz;
        upDown.zw = sgsrGatherGreen(coord + vec2(0.0,  u_invResolution.y)).yx;

        float mean = (left.y + left.z + right.x + right.w) * 0.25;
        left -= vec4(mean);
        right -= vec4(mean);
        upDown -= vec4(mean);
        color.g -= mean;

        float sum = abs(left.x) + abs(left.y) + abs(left.z) + abs(left.w)
                  + abs(right.x) + abs(right.y) + abs(right.z) + abs(right.w)
                  + abs(upDown.x) + abs(upDown.y) + abs(upDown.z) + abs(upDown.w);
        float std = 2.181818 / max(sum, 0.000001);

        vec2 aWY = weightY(pl.x,     pl.y + 1.0, upDown.x, std);
        aWY += weightY(pl.x - 1.0, pl.y + 1.0, upDown.y, std);
        aWY += weightY(pl.x - 1.0, pl.y - 2.0, upDown.z, std);
        aWY += weightY(pl.x,     pl.y - 2.0, upDown.w, std);
        aWY += weightY(pl.x + 1.0, pl.y - 1.0, left.x, std);
        aWY += weightY(pl.x,     pl.y - 1.0, left.y, std);
        aWY += weightY(pl.x,     pl.y,       left.z, std);
        aWY += weightY(pl.x + 1.0, pl.y,     left.w, std);
        aWY += weightY(pl.x - 1.0, pl.y - 1.0, right.x, std);
        aWY += weightY(pl.x - 2.0, pl.y - 1.0, right.y, std);
        aWY += weightY(pl.x - 2.0, pl.y,       right.z, std);
        aWY += weightY(pl.x - 1.0, pl.y,       right.w, std);

        float finalY = aWY.y / max(aWY.x, 0.000001);
        float maxY = max(max(left.y, left.z), max(right.x, right.w));
        float minY = min(min(left.y, left.z), min(right.x, right.w));
        finalY = clamp(edgeSharpness * finalY, minY, maxY);
        float deltaY = clamp(finalY - color.g, -23.0 / 255.0, 23.0 / 255.0);

        color.rgb = clamp(color.rgb + vec3(deltaY), 0.0, 1.0);
    }

    gl_FragColor = vec4(color.rgb, 1.0);
}
)glsl";

} // namespace bv::shaders::sgsr1

namespace bv::shaders {

render::PostProcessShader const kSgsr1Shader{
    "Snapdragon GSR1",
    kFullscreenVertexSource,
    sgsr1::kFragmentSource,
};

} // namespace bv::shaders
