#include "FrameInterpolationRenderer.hpp"
#include "ShaderProgram.hpp"
#include "GlStateGuard.hpp"
#include <array>
#include <algorithm>

namespace bv::render {
namespace {
constexpr char kFrameInterpolationFragment[] = R"glsl(
precision highp float;
uniform sampler2D u_previous;
uniform sampler2D u_current;
uniform vec2 u_invResolution;
varying vec2 v_texCoord;
float luma(vec3 c) { return dot(c, vec3(0.299, 0.587, 0.114)); }
vec2 estimateFlow(sampler2D fromFrame, sampler2D toFrame, vec2 uv) {
    vec2 flow = vec2(0.0);
    for (int iteration = 0; iteration < 3; ++iteration) {
        float a = 0.0, b = 0.0, c = 0.0, d = 0.0, e = 0.0;
        for (int y = -1; y <= 1; ++y) {
            for (int x = -1; x <= 1; ++x) {
                vec2 offset = vec2(float(x), float(y)) * u_invResolution;
                vec2 p = uv + offset;
                float i0 = luma(texture2D(fromFrame, p).rgb);
                vec2 q = p + flow;
                float ix = 0.5 * (luma(texture2D(toFrame, q + vec2(u_invResolution.x, 0.0)).rgb)
                                - luma(texture2D(toFrame, q - vec2(u_invResolution.x, 0.0)).rgb));
                float iy = 0.5 * (luma(texture2D(toFrame, q + vec2(0.0, u_invResolution.y)).rgb)
                                - luma(texture2D(toFrame, q - vec2(0.0, u_invResolution.y)).rgb));
                float it = luma(texture2D(toFrame, q).rgb) - i0;
                float weight = 1.0 / (1.0 + float(x*x + y*y));
                a += weight * ix * ix; b += weight * ix * iy;
                c += weight * iy * iy; d += weight * ix * it; e += weight * iy * it;
            }
        }
        float determinant = a * c - b * b;
        if (determinant > 0.0000005) {
            vec2 delta = vec2(c * d - b * e, a * e - b * d) / determinant;
            flow -= clamp(delta, vec2(-2.0), vec2(2.0)) * u_invResolution;
        }
    }
    return clamp(flow, -12.0 * u_invResolution, 12.0 * u_invResolution);
}
void main() {
    vec2 uv = v_texCoord;
    vec2 forwardFlow = estimateFlow(u_previous, u_current, uv);
    vec2 backwardFlow = estimateFlow(u_current, u_previous, uv);
    float consistency = length(forwardFlow + backwardFlow) /
        max(length(forwardFlow) + length(backwardFlow), 0.00001);
    vec2 previousUV = clamp(uv - 0.5 * forwardFlow, vec2(0.001), vec2(0.999));
    vec2 currentUV = clamp(uv - 0.5 * backwardFlow, vec2(0.001), vec2(0.999));
    vec4 previousColor = texture2D(u_previous, previousUV);
    vec4 currentColor = texture2D(u_current, currentUV);
    float difference = length(previousColor.rgb - currentColor.rgb);
    float confidence = (1.0 - smoothstep(0.08, 0.45, consistency)) *
                       (1.0 - smoothstep(0.18, 0.55, difference));
    vec4 warpedAverage = 0.5 * (previousColor + currentColor);
    vec4 midpoint = mix(currentColor, warpedAverage, confidence);
    gl_FragColor = vec4(midpoint.rgb, currentColor.a);
}
)glsl";
constexpr char kVertex[] = R"glsl(
attribute vec2 a_position; attribute vec2 a_texCoord; varying vec2 v_texCoord;
void main(){ v_texCoord=a_texCoord; gl_Position=vec4(a_position,0.0,1.0); }
)glsl";
}
bool FrameInterpolationRenderer::initialize() {
    if (m_program) return true;
    std::array vs{std::string_view(kVertex)};
    std::array fs{std::string_view(kFrameInterpolationFragment)};
    m_program = compileShaderProgram("Frame Generation (Lucas-Kanade)", vs, fs);
    if (!m_program) return false;
    if (!m_quad.initialize("frame generation")) {
        glDeleteProgram(m_program);
        m_program = 0;
        return false;
    }
    m_previousUniform = glGetUniformLocation(m_program, "u_previous");
    m_currentUniform = glGetUniformLocation(m_program, "u_current");
    m_inverseResolutionUniform = glGetUniformLocation(m_program, "u_invResolution");
    if (m_previousUniform < 0 || m_currentUniform < 0 || m_inverseResolutionUniform < 0) {
        destroy(); return false;
    }
    glUseProgram(m_program);
    glUniform1i(m_previousUniform, 0);
    glUniform1i(m_currentUniform, 1);
    return true;
}
bool FrameInterpolationRenderer::capture(GLuint framebuffer, GLint x, GLint y,
                                          GLsizei width, GLsizei height) {
    GlStateGuard state;
    if (width <= 0 || height <= 0 || !initialize()) return false;
    if (width != m_width || height != m_height) {
        reset();
        if (!initialize()) return false;
        glGenTextures(2, m_frames.data());
        for (auto texture : m_frames) {
            if (!texture) { reset(); return false; }
            glBindTexture(GL_TEXTURE_2D, texture);
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE);
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0,
                         GL_RGBA, GL_UNSIGNED_BYTE, nullptr);
        }
        m_width = width; m_height = height;
        m_writeIndex = 0; m_currentIndex = 0;
        m_hasCurrent = false; m_hasHistory = false;
    }
    glBindFramebuffer(GL_FRAMEBUFFER, framebuffer);
    glActiveTexture(GL_TEXTURE0);
    glBindTexture(GL_TEXTURE_2D, m_frames[m_writeIndex]);
    glCopyTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, x, y, width, height);
    if (glGetError() != GL_NO_ERROR) {
        // A failed capture must never be used as frame history. Drop both
        // textures so the Loader callback falls back to the game's own frame.
        reset();
        return false;
    }
    m_currentIndex = m_writeIndex;
    m_writeIndex = 1u - m_writeIndex;
    if (m_hasCurrent) m_hasHistory = true;
    m_hasCurrent = true;
    return true;
}
bool FrameInterpolationRenderer::present(int phase) {
    GlStateGuard state;
    if ((phase != 0 && phase != 1) || !m_hasHistory || !initialize()) return false;
    // Discard stale GL errors from unrelated game rendering. Only errors
    // produced by this presentation pass may trigger our fallback path.
    while (glGetError() != GL_NO_ERROR) {}
    unsigned const previousIndex = 1u - m_currentIndex;
    unsigned const currentIndex = m_currentIndex;
    // The captured game texture can be smaller than the EGL surface (for
    // example when Render Scale / FSR is active). Never use capture dimensions
    // as the presentation viewport: that can leave most of the surface stale
    // or black. Keep the current surface viewport and only fall back to the
    // capture size if the host has not established one.
    GLint surfaceViewport[4] = {0, 0, 0, 0};
    glGetIntegerv(GL_VIEWPORT, surfaceViewport);
    if (surfaceViewport[2] <= 0 || surfaceViewport[3] <= 0) {
        return false;
    }
    glBindFramebuffer(GL_FRAMEBUFFER, 0);
    glViewport(surfaceViewport[0], surfaceViewport[1],
               surfaceViewport[2], surfaceViewport[3]);
    glDisable(GL_BLEND);
    glDisable(GL_DEPTH_TEST);
    glDisable(GL_STENCIL_TEST);
    glDisable(GL_SCISSOR_TEST);
    glDisable(GL_CULL_FACE);
    glColorMask(GL_TRUE, GL_TRUE, GL_TRUE, GL_TRUE);
    glUseProgram(m_program);
    glUniform2f(m_inverseResolutionUniform, 1.f / m_width, 1.f / m_height);
    glActiveTexture(GL_TEXTURE0);
    glBindTexture(GL_TEXTURE_2D, m_frames[previousIndex]);
    glActiveTexture(GL_TEXTURE1);
    glBindTexture(GL_TEXTURE_2D, phase == 0 ? m_frames[previousIndex] : m_frames[currentIndex]);
    m_quad.bind();
    FullscreenQuad::draw();
    auto const error = glGetError();
    if (error != GL_NO_ERROR) {
        // Do not keep presenting a potentially incomplete generated image.
        // The Loader will present the game's original frame on the next tick.
        reset();
        return false;
    }
    return true;
}
void FrameInterpolationRenderer::destroy() {
    if (m_program) glDeleteProgram(m_program);
    m_program = 0;
    m_previousUniform = m_currentUniform = m_inverseResolutionUniform = -1;
    m_quad.reset();
}
void FrameInterpolationRenderer::reset() {
    if (m_frames[0] || m_frames[1]) glDeleteTextures(2, m_frames.data());
    m_frames = {};
    m_width = m_height = 0;
    m_writeIndex = m_currentIndex = 0;
    m_hasCurrent = m_hasHistory = false;
    destroy();
}
}
