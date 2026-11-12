#include "../render/PostProcessRenderer.hpp"
#include "PostProcessShaders.hpp"

namespace bv::shaders::lanczos {
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
varying vec2 v_texCoord;
float sinc(float x) {
    if (abs(x) < 0.00001) return 1.0;
    const float PI = 3.14159265358979323846;
    float px = PI * x;
    return sin(px) / px;
}
float lanczos3(float x) {
    x = abs(x);
    if (x >= 3.0) return 0.0;
    return sinc(x) * sinc(x / 3.0);
}
void main() {
    vec2 sourcePos = v_texCoord / u_invResolution - vec2(0.5);
    vec2 base = floor(sourcePos);
    vec2 fraction = sourcePos - base;
    vec4 sum = vec4(0.0);
    float totalWeight = 0.0;
    for (int y = -2; y <= 3; ++y) {
        for (int x = -2; x <= 3; ++x) {
            vec2 offset = vec2(float(x), float(y));
            vec2 distance = fraction - offset;
            float weight = lanczos3(distance.x) * lanczos3(distance.y);
            vec2 sampleUV = (base + offset + vec2(0.5)) * u_invResolution;
            sum += texture2D(u_texture, sampleUV) * weight;
            totalWeight += weight;
        }
    }
    gl_FragColor = clamp(sum / max(totalWeight, 0.000001), 0.0, 1.0);
}
)glsl";
}
namespace bv::shaders {
render::PostProcessShader const kLanczosShader{
    "Lanczos 3 Upscaler", kFullscreenVertexSource, lanczos::kFragmentSource,
};
}
