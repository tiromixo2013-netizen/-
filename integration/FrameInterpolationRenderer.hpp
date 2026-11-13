#pragma once
#include <Geode/cocos/platform/CCGL.h>
#include <array>
#include "FullscreenQuad.hpp"

namespace bv::render {
class FrameInterpolationRenderer final {
public:
    FrameInterpolationRenderer() = default;
    FrameInterpolationRenderer(FrameInterpolationRenderer const&) = delete;
    FrameInterpolationRenderer& operator=(FrameInterpolationRenderer const&) = delete;

    // Capture the fully post-processed game image while its framebuffer is bound.
    bool capture(GLuint framebuffer, GLint x, GLint y, GLsizei width, GLsizei height);
    // Present a midpoint or the retained current source frame on the GL thread.
    bool present(int phase);
    bool presentCurrent();
    void reset();

private:
    bool initialize();
    bool presentImpl(int phase, bool currentOnly);
    void destroy();

    GLuint m_program = 0;
    GLint m_previousUniform = -1;
    GLint m_currentUniform = -1;
    GLint m_inverseResolutionUniform = -1;
    GLint m_currentOnlyUniform = -1;
    std::array<GLuint, 2> m_frames = {};
    FullscreenQuad m_quad;
    GLsizei m_width = 0;
    GLsizei m_height = 0;
    unsigned m_writeIndex = 0;
    unsigned m_currentIndex = 0;
    bool m_hasCurrent = false;
    bool m_hasHistory = false;
};
}
