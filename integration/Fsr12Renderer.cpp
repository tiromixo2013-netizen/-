#include "Fsr12Renderer.hpp"

#include <Geode/Geode.hpp>
#include <cassert>

using namespace geode::prelude;

namespace bv::render {

bool Fsr12Renderer::prepare(
    PostProcessShader const& easuShader,
    PostProcessShader const& rcasShader,
    GLsizei inputWidth, GLsizei inputHeight,
    GLsizei outputWidth, GLsizei outputHeight
) {
    if (inputWidth <= 0 || inputHeight <= 0 || outputWidth <= 0 || outputHeight <= 0) {
        return false;
    }

    glActiveTexture(GL_TEXTURE0);
    if (m_width != outputWidth || m_height != outputHeight || m_texture == 0 || m_framebuffer == 0) {
        destroyResources();
        glGenTextures(1, &m_texture);
        glBindTexture(GL_TEXTURE_2D, m_texture);
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE);
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, outputWidth, outputHeight, 0, GL_RGBA, GL_UNSIGNED_BYTE, nullptr);

        glGenFramebuffers(1, &m_framebuffer);
        glBindFramebuffer(GL_FRAMEBUFFER, m_framebuffer);
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, m_texture, 0);
        auto const status = glCheckFramebufferStatus(GL_FRAMEBUFFER);
        if (m_texture == 0 || m_framebuffer == 0 || status != GL_FRAMEBUFFER_COMPLETE) {
            log::error("FSR 1.2 intermediate framebuffer creation failed ({:#x})", status);
            destroyResources();
            return false;
        }
        m_width = outputWidth;
        m_height = outputHeight;
    }

    return m_easu.prepare(easuShader, inputWidth, inputHeight) &&
        m_rcas.prepare(rcasShader, outputWidth, outputHeight);
}

void Fsr12Renderer::apply(
    GLuint inputTexture, GLuint outputFramebuffer,
    GLint outputX, GLint outputY,
    GLsizei outputWidth, GLsizei outputHeight,
    GLfloat sharpness
) {
    assert(m_framebuffer != 0 && m_texture != 0 && inputTexture != 0);

    glBindFramebuffer(GL_FRAMEBUFFER, m_framebuffer);
    glViewport(0, 0, m_width, m_height);
    m_easu.apply(inputTexture, 1.f);

    glBindFramebuffer(GL_FRAMEBUFFER, outputFramebuffer);
    glViewport(outputX, outputY, outputWidth, outputHeight);
    m_rcas.apply(m_texture, sharpness);
}

void Fsr12Renderer::reset() {
    destroyResources();
    m_easu.reset();
    m_rcas.reset();
}

void Fsr12Renderer::destroyResources() {
    if (m_framebuffer != 0) {
        glDeleteFramebuffers(1, &m_framebuffer);
        m_framebuffer = 0;
    }
    if (m_texture != 0) {
        glDeleteTextures(1, &m_texture);
        m_texture = 0;
    }
    m_width = 0;
    m_height = 0;
}

} // namespace bv::render
