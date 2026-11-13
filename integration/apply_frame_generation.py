#!/usr/bin/env python3
"""Wire optical-flow frame generation to the custom Geode Android Loader bridge."""
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
     '#include "render/BloomRenderer.hpp"\n#include "render/FrameInterpolationRenderer.hpp"\n')
once('#include <chrono>\n',
     '#include <chrono>\n#ifdef GEODE_IS_ANDROID\n#include <dlfcn.h>\n#endif\n')
once('    std::atomic<bool> g_modEnabled = true;\n',
     '    std::atomic<bool> g_modEnabled = true;\n    std::atomic<bool> g_frameGenerationEnabled = false;\n')
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
        if (g_frameGenerationEnabled.load(std::memory_order_relaxed)) {
            if (!g_frameInterpolationRenderer.capture(
                    callerTarget.framebuffer, callerTarget.x, callerTarget.y,
                    callerTarget.width, callerTarget.height)) {
                g_frameInterpolationRenderer.reset();
            }
        }
        else {
            g_frameInterpolationRenderer.reset();
        }
    }

    bool presentGeneratedFrame(int phase) {
        if (!g_frameGenerationEnabled.load(std::memory_order_relaxed) ||
            !g_modEnabled.load(std::memory_order_relaxed) ||
            g_temporarilyDisabled.load(std::memory_order_relaxed)) {
            return false;
        }
        return g_frameInterpolationRenderer.present(phase);
    }

    void registerFrameGenerationBridge() {
#ifdef GEODE_IS_ANDROID
        using RegisterCallback = void (*)(bool (*)(int));
        auto const registerCallback = reinterpret_cast<RegisterCallback>(
            dlsym(RTLD_DEFAULT, "GeodeSetFrameGenerationPresentCallback")
        );
        if (registerCallback) {
            registerCallback(&presentGeneratedFrame);
            log::info("Registered Android Loader Frame Generation bridge");
        }
        else {
            log::warn("Custom Geode Loader Frame Generation bridge not found; generation is unavailable");
        }
#endif
    }

} // namespace
''')
once('''$on_mod(Loaded) {
    bindBoolSetting("enabled", g_modEnabled);
''',
'''$on_mod(Loaded) {
    bindBoolSetting("enabled", g_modEnabled);
    bindBoolSetting("frame-generation-enabled", g_frameGenerationEnabled);
    registerFrameGenerationBridge();
''')

main.write_text(s)

manifest = Path("mod.json")
mod = json.loads(manifest.read_text())
settings = mod.setdefault("settings", {})
settings["frame-generation-title"] = {"type": "title", "name": "Frame Generation"}
settings["frame-generation-enabled"] = {
    "type": "bool",
    "name": "Enable Frame Generation",
    "description": "Experimental Android Loader frame pacing with bidirectional Lucas-Kanade midpoint synthesis. Requires the matching custom Geode Loader bridge. Disabled by default; falls back to normal rendering if the bridge or frame history is unavailable.",
    "default": False,
    "enable-if": "enabled"
}
manifest.write_text(json.dumps(mod, indent=2) + "\n")
print("Frame Generation setting and Loader callback integration applied.")
