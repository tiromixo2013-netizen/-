#pragma once
#include <Geode/cocos/platform/CCGL.h>

namespace bv::render {
class FrameInterpolationRenderer final {
public:
    FrameInterpolationRenderer() = default;
    FrameInterpolationRenderer(FrameInterpolationRenderer const&) = delete;
    FrameInterpolationRenderer& operator=(FrameInterpolationRenderer const&) = delete;
    // Captures the completed output and, once history exists, draws a motion-warped
    // temporal midpoint back to the same framebuffer. This is a preview/replacement
    // path; it does not create an independently presented Android display refresh.
    bool process(GLuint framebuffer, GLint x, GLint y, GLsizei width, GLsizei height);
    void reset();
private:
    bool initialize();
    void destroy();
    GLuint m_program = 0;
    GLint m_previousUniform = -1;
    GLint m_currentUniform = -1;
    GLint m_inverseResolutionUniform = -1;
    std::array<GLuint, 2> m_frames = {};
    GLsizei m_width = 0;
    GLsizei m_height = 0;
    unsigned m_writeIndex = 0;
    bool m_hasHistory = false;
};
}
