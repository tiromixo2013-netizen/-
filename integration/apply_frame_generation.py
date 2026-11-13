#!/usr/bin/env python3
"""Integrate the experimental Lucas-Kanade midpoint interpolation path."""
from pathlib import Path
import json, shutil

root = Path(".")
integration = Path("integration")
Path("src/render").mkdir(parents=True, exist_ok=True)
shutil.copy2(integration / "FrameInterpolationRenderer.hpp", "src/render/FrameInterpolationRenderer.hpp")
shutil.copy2(integration / "FrameInterpolationRenderer.cpp", "src/render/FrameInterpolationRenderer.cpp")

main = Path("src/main.cpp")
s = main.read_text()
def once(old, new):
    global s
    n = s.count(old)
    if n != 1:
        raise SystemExit(f"Frame Generation patch point count {n}, expected 1: {old[:100]!r}")
    s = s.replace(old, new, 1)

once('#include "render/BloomRenderer.hpp"\n',
     '#include "render/BloomRenderer.hpp"\n#include "render/FrameInterpolationRenderer.hpp"\n')
once('    std::atomic<bool> g_modEnabled = true;\n',
     '    std::atomic<bool> g_modEnabled = true;\n    std::atomic<bool> g_frameGenerationEnabled = false;\n')
once('    bv::render::BloomRenderer g_bloomRenderer;\n',
     '    bv::render::BloomRenderer g_bloomRenderer;\n    bv::render::FrameInterpolationRenderer g_frameInterpolationRenderer;\n')
once('        g_bloomRenderer.reset();\n',
     '        g_bloomRenderer.reset();\n        g_frameInterpolationRenderer.reset();\n')
once('    bindBoolSetting("enabled", g_modEnabled);\n',
     '    bindBoolSetting("enabled", g_modEnabled);\n    bindBoolSetting("frame-generation-enabled", g_frameGenerationEnabled);\n')
once('        auto const needsPresentation = internalWidth != width || internalHeight != height;\n',\n     '        auto const frameGeneration = g_frameGenerationEnabled.load(std::memory_order_relaxed);\n        auto const needsPresentation = internalWidth != width || internalHeight != height || frameGeneration;\n')\nonce('''        glBindFramebuffer(GL_FRAMEBUFFER, callerTarget.framebuffer);
        glViewport(callerTarget.x, callerTarget.y, callerTarget.width, callerTarget.height);
        g_failedPostProcessKey.reset();
''',
'''        glBindFramebuffer(GL_FRAMEBUFFER, callerTarget.framebuffer);
        glViewport(callerTarget.x, callerTarget.y, callerTarget.width, callerTarget.height);
        if (g_frameGenerationEnabled.load(std::memory_order_relaxed)) {
            if (!g_frameInterpolationRenderer.process(
                    callerTarget.framebuffer, callerTarget.x, callerTarget.y,
                    callerTarget.width, callerTarget.height)) {
                g_frameInterpolationRenderer.reset();
            }
        }
        else {
            g_frameInterpolationRenderer.reset();
        }
        g_failedPostProcessKey.reset();
''')
main.write_text(s)

manifest = Path("mod.json")
mod = json.loads(manifest.read_text())
mod["settings"]["frame-generation-title"] = {
    "type": "title", "name": "Frame Generation (Experimental)"
}
mod["settings"]["frame-generation-enabled"] = {
    "type": "bool",
    "name": "Enable Frame Interpolation",
    "description": "Experimental Lucas-Kanade motion estimation and midpoint reconstruction. This replaces the current output with a synthesized midpoint; it does not insert an independently presented display refresh or guarantee higher FPS.",
    "default": False,
    "enable-if": "enabled"
}
manifest.write_text(json.dumps(mod, indent=2) + "\n")
print("Experimental Frame Interpolation integrated (disabled by default).")
