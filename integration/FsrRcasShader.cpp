#include "../PostProcessShaders.hpp"

 /*
  * RCAS pass adapted from AMD FidelityFX Super Resolution 1.
  * https://github.com/GPUOpen-Effects/FidelityFX-FSR
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

float luma2(vec3 c) {
    return c.b * 0.5 + (c.r * 0.5 + c.g);
}

void main() {
    vec2 px = u_invResolution;
    vec3 b = texture2D(u_texture, v_texCoord - vec2(0.0, px.y)).rgb;
    vec3 d = texture2D(u_texture, v_texCoord - vec2(px.x, 0.0)).rgb;
    vec4 center = texture2D(u_texture, v_texCoord);
    vec3 e = center.rgb;
    vec3 f = texture2D(u_texture, v_texCoord + vec2(px.x, 0.0)).rgb;
    vec3 h = texture2D(u_texture, v_texCoord + vec2(0.0, px.y)).rgb;

    float bL = luma2(b);
    float dL = luma2(d);
    float eL = luma2(e);
    float fL = luma2(f);
    float hL = luma2(h);

    float nz = abs(0.25 * (bL + dL + fL + hL) - eL);
    float lumaMax = max(max(max(bL, dL), max(eL, fL)), hL);
    float lumaMin = min(min(min(bL, dL), min(eL, fL)), hL);
    nz = clamp(nz / max(lumaMax - lumaMin, 1.0e-6), 0.0, 1.0);
    nz = 1.0 - 0.5 * nz;

    vec3 mn4 = min(min(b, d), min(f, h));
    vec3 mx4 = max(max(b, d), max(f, h));

    vec3 hitMin = min(mn4, e) / max(4.0 * mx4, vec3(1.0e-6));
    vec3 hitMaxDenom = min(4.0 * mn4 - 4.0, vec3(-1.0e-6));
    vec3 hitMax = (vec3(1.0) - max(mx4, e)) / hitMaxDenom;

    vec3 lobeRGB = max(-hitMin, hitMax);
    float lobe = max(-0.1875, min(max(max(lobeRGB.r, lobeRGB.g), lobeRGB.b), 0.0));

    // Map the 0..1 UI slider to the RCAS attenuation range.
    float sharpness = exp2(-4.0 * (1.0 - clamp(u_sharpness, 0.0, 1.0)));
    lobe *= sharpness * nz;

    float rcpL = 1.0 / (4.0 * lobe + 1.0);
    vec3 result = (lobe * (b + d + f + h) + e) * rcpL;
    gl_FragColor = vec4(clamp(result, 0.0, 1.0), center.a);
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
