#pragma once

#include "PostProcessRenderer.hpp"

namespace bv::render {

class Fsr12Renderer final {
public:
    Fsr12Renderer() = default;
    Fsr12Renderer(Fsr12Renderer const&) = delete;
    Fsr12Renderer& operator=(Fsr12Renderer const&) = delete;

    bool prepare(
        PostProcessShader const& easuShader,
        PostProcessShader const& rcasShader,
        GLsizei inputWidth, GLsizei inputHeight,
        GLsizei outputWidth, GLsizei outputHeight
    );
    void apply(
        GLuint inputTexture, GLuint outputFramebuffer,
        GLint outputX, GLint outputY,
        GLsizei outputWidth, GLsizei outputHeight,
        GLfloat sharpness
    );
    void reset();

private:
    void destroyResources();

    PostProcessRenderer m_easu;
    PostProcessRenderer m_rcas;
    GLuint m_texture = 0;
    GLuint m_framebuffer = 0;
    GLsizei m_width = 0;
    GLsizei m_height = 0;
};

} // namespace bv::render
