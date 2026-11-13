#!/usr/bin/env python3
"""Wire optical-flow frame generation into Geode Cocos render hooks."""
from pathlib import Path
import json

main = Path("src/main.cpp")
s = main.read_text()

def once(old, new):
    global s
    count = s.count(old)
    if count != 1:
        raise SystemExit(f"Frame Generation patch point count {count}, expected 1: {old[:100]!r}")
    s = s.replace(old, new, 1)

once('#include "render/BloomRenderer.hpp"\n',
     '#include "render/BloomRenderer.hpp"\n#include "render/FrameInterpolationRenderer.hpp"\n#include <Geode/utils/addresser.hpp>\n')
once('#include <chrono>\n',
     '#include <chrono>\n#ifdef GEODE_IS_ANDROID\n#include <Geode/mapping/CCEGLView.hpp>\n#endif\n')
once('    std::atomic<bool> g_modEnabled = true;\n',
     '    std::atomic<bool> g_modEnabled = true;\n    std::atomic<bool> g_frameGenerationEnabled = false;\n    std::atomic<bool> g_frameGenerationCaptureReady = false;\n    std::atomic<bool> g_frameGenerationShowSource = false;\n    std::atomic<bool> g_frameGenerationManualSwap = false;\n')
once('    bv::render::BloomRenderer g_bloomRenderer;\n',
     '    bv::render::BloomRenderer g_bloomRenderer;\n    bv::render::FrameInterpolationRenderer g_frameInterpolationRenderer;\n')
once('        g_crtRenderer.reset();\n        g_smaaRenderer.reset();\n',
     '        g_crtRenderer.reset();\n        g_smaaRenderer.reset();\n        g_frameInterpolationRenderer.reset();\n')
once('''        auto const needsPresentation = internalWidth != width || internalHeight != height;
''',
'''        auto const frameGeneration = g_frameGenerationEnabled.load(std::memory_order_relaxed);
        auto const needsPresentation = internalWidth != width || internalHeight != height || frameGeneration;
''')
once('''        g_failedPostProcessKey.reset();
    }

} // namespace
''',
'''        g_failedPostProcessKey.reset();
        if (g_frameGenerationEnabled.load(std::memory_order_relaxed) &&
            g_modEnabled.load(std::memory_order_relaxed) &&
            !g_temporarilyDisabled.load(std::memory_order_relaxed)) {
            auto const captured = g_frameInterpolationRenderer.capture(
                callerTarget.framebuffer, callerTarget.x, callerTarget.y,
                callerTarget.width, callerTarget.height
            );
            g_frameGenerationCaptureReady.store(captured, std::memory_order_relaxed);
            if (!captured) {
                g_frameGenerationShowSource.store(false, std::memory_order_relaxed);
                g_frameInterpolationRenderer.reset();
            }
        }
        else {
            g_frameGenerationCaptureReady.store(false, std::memory_order_relaxed);
            g_frameGenerationShowSource.store(false, std::memory_order_relaxed);
            g_frameInterpolationRenderer.reset();
        }
    }

} // namespace
''')
once('''#ifdef GEODE_IS_ANDROID
void betterVisualsFrameGenerationSwapBuffers(cocos2d::CCEGLView* self);
#endif

$on_mod(Loaded) {
    bindBoolSetting("enabled", g_modEnabled);
''',
'''$on_mod(Loaded) {
    bindBoolSetting("enabled", g_modEnabled);
    bindBoolSetting("frame-generation-enabled", g_frameGenerationEnabled);
#ifdef GEODE_IS_ANDROID
    auto const swapHook = Mod::get()->hook(
        reinterpret_cast<void*>(geode::addresser::getNonVirtual(&cocos2d::CCEGLView::swapBuffers)),
        &betterVisualsFrameGenerationSwapBuffers,
        "CCEGLView::swapBuffers (Frame Generation)",
        tulip::hook::TulipConvention::Cdecl
    );
    if (!swapHook) {
        log::warn("Could not hook CCEGLView::swapBuffers; Frame Generation will remain inactive");
    }
#endif
''')

once('''class $modify(BetterVisualsDirectorHook, CCDirector) {
    void setProjection(ccDirectorProjection kProjection) {
        CCDirector::setProjection(kProjection);
        applyCaptureViewport();
    }

    void setViewport() {
        CCDirector::setViewport();
        applyCaptureViewport();
    }
};''',
'''class $modify(BetterVisualsDirectorHook, CCDirector) {
    void setProjection(ccDirectorProjection kProjection) {
        CCDirector::setProjection(kProjection);
        applyCaptureViewport();
    }

    void setViewport() {
        CCDirector::setViewport();
        applyCaptureViewport();
    }

#ifdef GEODE_IS_ANDROID
    void drawScene() {
        if (!g_frameGenerationEnabled.load(std::memory_order_relaxed) ||
            !g_modEnabled.load(std::memory_order_relaxed) ||
            g_temporarilyDisabled.load(std::memory_order_relaxed)) {
            g_frameGenerationShowSource.store(false, std::memory_order_relaxed);
            CCDirector::drawScene();
            return;
        }
        if (g_frameGenerationShowSource.exchange(false, std::memory_order_relaxed)) {
            if (g_frameInterpolationRenderer.presentCurrent()) {
                if (auto view = cocos2d::CCEGLView::sharedOpenGLView()) {
                    g_frameGenerationManualSwap.store(true, std::memory_order_relaxed);
                    view->swapBuffers();
                    g_frameGenerationManualSwap.store(false, std::memory_order_relaxed);
                    return;
                }
            }
        }
        CCDirector::drawScene();
    }
#endif
};

#ifdef GEODE_IS_ANDROID
void betterVisualsFrameGenerationSwapBuffers(cocos2d::CCEGLView* self) {
    if (!g_frameGenerationManualSwap.load(std::memory_order_relaxed) &&
        g_frameGenerationEnabled.load(std::memory_order_relaxed) &&
        g_modEnabled.load(std::memory_order_relaxed) &&
        !g_temporarilyDisabled.load(std::memory_order_relaxed) &&
        g_frameGenerationCaptureReady.exchange(false, std::memory_order_relaxed)) {
        if (g_frameInterpolationRenderer.present(1)) {
            g_frameGenerationShowSource.store(true, std::memory_order_relaxed);
        }
    }
    // TulipHook's per-thread handler chain routes this same call to the next
    // handler, ultimately reaching the original CCEGLView implementation.
    self->swapBuffers();
}
#endif''');
main.write_text(s)

manifest = Path("mod.json")
mod = json.loads(manifest.read_text())
settings = mod.setdefault("settings", {})
settings["frame-generation-title"] = {"type": "title", "name": "Frame Generation"}
settings["frame-generation-enabled"] = {
    "type": "bool",
    "name": "Enable Frame Generation",
    "description": "Experimental Android Cocos frame pacing with bidirectional Lucas-Kanade midpoint synthesis. Uses Geode Cocos render hooks; no custom Loader or APK is required. Disabled by default; falls back to normal rendering if capture or frame history is unavailable.",
    "default": False,
    "enable-if": "enabled"
}
manifest.write_text(json.dumps(mod, indent=2) + "\n")
print("Frame Generation setting and Geode Cocos render-hook integration applied.")
