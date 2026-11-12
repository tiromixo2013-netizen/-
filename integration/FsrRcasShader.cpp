#include "../../render/PostProcessRenderer.hpp"
#include "../PostProcessShaders.hpp"

/*
 * RCAS pass ported from the official AMD FidelityFX Super Resolution 1
 * reference implementation (FsrRcasCon + FsrRcasF), adapted to GLSL ES 1.00.
 * Upstream: https://github.com/GPUOpen-Effects/FidelityFX-FSR
 *
 * Copyright (c) 2021 Advanced Micro Devices, Inc. All rights reserved.
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 * THE SOFTWARE.
 */

namespace bv::shaders::fsr_rcas {

constexpr char kFragmentSource[] = R"glsl(
#ifdef GL_ES
    #ifdef GL_FRAGMENT_PRECISION_HIGH
        precision highp float;
    #else
        precision mediump float;
    #endif
#endif

uniform sampler2D u_texture;
uniform vec2 u_invResolution;
uniform float u_sharpness;
varying vec2 v_texCoord;

const float FSR_RCAS_LIMIT = 0.1875;
const float FSR_EPSILON = 1.0e-6;

// Matches AMD FsrRcasCon(): the input is converted from sharpness stops
// to the linear attenuation constant with 2^(-stops).
float rcasAttenuation(float uiSharpness) {
    float sharpnessStops = 4.0 * (1.0 - clamp(uiSharpness, 0.0, 1.0));
    return exp2(-sharpnessStops);
}

float lumaTimesTwo(vec3 color) {
    return color.b * 0.5 + (color.r * 0.5 + color.g);
}

void main() {
    // AMD RCAS uses the cross-shaped 3x3 neighbourhood:
    //       b
    //     d e f
    //       h
    // Clamp-to-edge sampling is configured on the intermediate FSR texture.
    vec2 px = u_invResolution;
    vec3 b = texture2D(u_texture, v_texCoord - vec2(0.0, px.y)).rgb;
    vec3 d = texture2D(u_texture, v_texCoord - vec2(px.x, 0.0)).rgb;
    vec4 center = texture2D(u_texture, v_texCoord);
    vec3 e = center.rgb;
    vec3 f = texture2D(u_texture, v_texCoord + vec2(px.x, 0.0)).rgb;
    vec3 h = texture2D(u_texture, v_texCoord + vec2(0.0, px.y)).rgb;

    // Luma times two, matching FsrRcasF.
    float bL = lumaTimesTwo(b);
    float dL = lumaTimesTwo(d);
    float eL = lumaTimesTwo(e);
    float fL = lumaTimesTwo(f);
    float hL = lumaTimesTwo(h);

    // Per-channel min/max of the four-neighbour ring.
    vec3 mn4 = min(min(b, d), min(f, h));
    vec3 mx4 = max(max(b, d), max(f, h));

    // FsrRcasF limiter equations. Denominator guards only handle flat black/
    // white neighbourhoods where the reference reciprocal would be 0/0.
    vec3 hitMin = min(mn4, e) / max(4.0 * mx4, vec3(FSR_EPSILON));
    vec3 hitMaxDenom = min(4.0 * mn4 - 4.0, vec3(-FSR_EPSILON));
    vec3 hitMax = (vec3(1.0) - max(mx4, e)) / hitMaxDenom;

    vec3 lobeRGB = max(-hitMin, hitMax);
    float lobe = max(
        -FSR_RCAS_LIMIT,
        min(max(max(lobeRGB.r, lobeRGB.g), lobeRGB.b), 0.0)
    );

    // Official FsrRcasCon attenuation. The optional AMD RCAS denoise path is
    // intentionally not enabled, matching the default reference configuration.
    lobe *= rcasAttenuation(u_sharpness);

    // RCAS resolve: four neighbours plus the centre, normalized by 4*lobe+1.
    // At the specified lobe limit this denominator is always >= 0.25.
    float rcpL = 1.0 / max(4.0 * lobe + 1.0, FSR_EPSILON);
    vec3 result = (lobe * (b + d + f + h) + e) * rcpL;

    // Preserve the source alpha channel exactly as the reference passthrough.
    gl_FragColor = vec4(result, center.a);
}
)glsl";

} // namespace bv::shaders::fsr_rcas

namespace bv::shaders {

render::PostProcessShader const kFsrRcasShader{
    "AMD FidelityFX FSR 1 RCAS",
    kFullscreenVertexSource,
    fsr_rcas::kFragmentSource,
    "u_sharpness",
};

} // namespace bv::shaders
