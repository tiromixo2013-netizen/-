#!/usr/bin/env python3
"""Apply the SGSR1 integration to a clean checkout of ItMe12s/BetterVisuals."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]

def replace_once(path, old, new):
    p = Path(path)
    text = p.read_text()
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"Expected exactly one patch point in {p}: found {count}")
    p.write_text(text.replace(old, new, 1))

main = Path("src/main.cpp")
s = main.read_text()

def sub(old, new):
    global s
    count = s.count(old)
    if count != 1:
        raise SystemExit(f"main.cpp patch point count {count}, expected 1: {old[:90]!r}")
    s = s.replace(old, new, 1)

sub("""#include "render/PostProcessRenderer.hpp"
""", """#include "render/PostProcessRenderer.hpp"
#include "render/Fsr12Renderer.hpp"
""")

sub("""        Fsr,
    };""", """        Fsr,
        Fsr12,
        Sgsr1,
    };""")
sub("""    bv::render::PostProcessRenderer g_fsrRenderer;
    bv::render::PostProcessRenderer g_casRenderer;""", """    bv::render::PostProcessRenderer g_fsrRenderer;
    bv::render::Fsr12Renderer g_fsr12Renderer;
    bv::render::PostProcessRenderer g_sgsr1Renderer;
    bv::render::PostProcessRenderer g_casRenderer;""")
sub("""        g_fsrRenderer.reset();
        g_casRenderer.reset();""", """        g_fsrRenderer.reset();
        g_fsr12Renderer.reset();
        g_sgsr1Renderer.reset();
        g_casRenderer.reset();""")
sub("""        if (value == "FSR 1") {
            g_upscaleMethod.store(UpscaleMethod::Fsr, std::memory_order_relaxed);
            return;
        }

        if (value != "Nearest") {""", """        Mod::get()->setSavedValue<bool>("fsr-preset-enabled", value == "FSR 1" || value == "FSR 1.2");
        if (value == "FSR 1") {
            g_upscaleMethod.store(UpscaleMethod::Fsr, std::memory_order_relaxed);
            return;
        }
        if (value == "FSR 1.2") {
            g_upscaleMethod.store(UpscaleMethod::Fsr12, std::memory_order_relaxed);
            return;
        }
        if (value == "SGSR1") {
            g_upscaleMethod.store(UpscaleMethod::Sgsr1, std::memory_order_relaxed);
            return;
        }

        if (value != "Nearest") {""")
sub("""            else if (config.upscaling == UpscaleMethod::Fsr) {
                g_renderScaleRenderer.reset();
                g_fsr12Renderer.reset();
                g_sgsr1Renderer.reset();
                g_ssaaRenderer.reset();
                prepared = g_fsrRenderer.prepare(bv::shaders::kFsrShader, key.width, key.height);
            }
            else {
                g_fsrRenderer.reset();
                g_ssaaRenderer.reset();
                prepared = g_renderScaleRenderer.prepare(
                    bv::shaders::kRenderScaleShader, key.width, key.height
                );
            }""", """            else if (config.upscaling == UpscaleMethod::Fsr) {
                g_renderScaleRenderer.reset();
                g_sgsr1Renderer.reset();
                g_ssaaRenderer.reset();
                prepared = g_fsrRenderer.prepare(bv::shaders::kFsrShader, key.width, key.height);
            }
            else if (config.upscaling == UpscaleMethod::Fsr12) {
                g_fsrRenderer.reset();
                g_sgsr1Renderer.reset();
                g_ssaaRenderer.reset();
                prepared = g_fsr12Renderer.prepare(
                    bv::shaders::kFsrShader, bv::shaders::kFsrRcasShader,
                    key.width, key.height, key.outputWidth, key.outputHeight
                );
            }
            else if (config.upscaling == UpscaleMethod::Sgsr1) {
                g_renderScaleRenderer.reset();
                g_fsrRenderer.reset();
                g_fsr12Renderer.reset();
                g_ssaaRenderer.reset();
                prepared = g_sgsr1Renderer.prepare(
                    bv::shaders::kSgsr1Shader, key.width, key.height
                );
            }
            else {
                g_fsrRenderer.reset();
                g_fsr12Renderer.reset();
                g_sgsr1Renderer.reset();
                g_ssaaRenderer.reset();
                prepared = g_renderScaleRenderer.prepare(
                    bv::shaders::kRenderScaleShader, key.width, key.height
                );
            }""")
sub("""            if (key.needsDownsample) {
                g_fsrRenderer.reset();
                g_renderScaleRenderer.reset();""", """            if (key.needsDownsample) {
                g_fsrRenderer.reset();
                g_fsr12Renderer.reset();
                g_sgsr1Renderer.reset();
                g_renderScaleRenderer.reset();""")
sub("""            g_renderScaleRenderer.reset();
            g_fsrRenderer.reset();
            g_ssaaRenderer.reset();""", """            g_renderScaleRenderer.reset();
            g_fsrRenderer.reset();
            g_fsr12Renderer.reset();
            g_sgsr1Renderer.reset();
            g_ssaaRenderer.reset();""")
sub("""                else if (config.upscaling == UpscaleMethod::Fsr) {
                    g_fsrRenderer.apply(sourceTexture, g_fsrSharpness.load(std::memory_order_relaxed));
                }
                else {
                    g_renderScaleRenderer.apply(sourceTexture);
                }""", """                else if (config.upscaling == UpscaleMethod::Fsr) {
                    g_fsrRenderer.apply(sourceTexture, g_fsrSharpness.load(std::memory_order_relaxed));
                }
                else if (config.upscaling == UpscaleMethod::Fsr12) {
                    g_fsr12Renderer.apply(
                        sourceTexture, callerTarget.framebuffer,
                        callerTarget.x, callerTarget.y,
                        callerTarget.width, callerTarget.height,
                        g_fsrSharpness.load(std::memory_order_relaxed)
                    );
                }
                else if (config.upscaling == UpscaleMethod::Sgsr1) {
                    g_sgsr1Renderer.apply(sourceTexture);
                }
                else {
                    g_renderScaleRenderer.apply(sourceTexture);
                }""")
# FSR quality presets multiply with the manual Render Scale; they never overwrite it.
sub("""    struct PostProcessKey {
        PostProcessConfig config;
        GLsizei width = 0;
        GLsizei height = 0;""", """    struct PostProcessKey {
        PostProcessConfig config;
        GLsizei width = 0;
        GLsizei height = 0;
        GLsizei outputWidth = 0;
        GLsizei outputHeight = 0;""")
sub("""            config, internalWidth, internalHeight, needsPresentation, needsDownsample
        };""", """            config, internalWidth, internalHeight, width, height,
            needsPresentation, needsDownsample
        };")
sub("""    std::atomic<float> g_renderScale = 1.f;""", """    std::atomic<float> g_renderScale = 1.f;
    std::atomic<float> g_fsrPresetScale = 0.67f;""")
sub("""    void bindBoolSetting(char const* name, std::atomic<bool>& value) {""", """    void updateFsrQualityPreset(std::string_view value) {
        float scale = 0.67f;
        if (value == "Ultra Quality") scale = 0.77f;
        else if (value == "Quality") scale = 0.67f;
        else if (value == "Balanced") scale = 0.59f;
        else if (value == "Performance") scale = 0.50f;
        else if (value == "Ultra Performance") scale = 0.33f;
        else log::warn("Unknown FSR quality preset '{}', using Quality", value);
        g_fsrPresetScale.store(scale, std::memory_order_relaxed);
    }

    void bindBoolSetting(char const* name, std::atomic<bool>& value) {""")
sub("""        auto const renderScale = g_renderScale.load(std::memory_order_relaxed);
        auto const effectiveScale = renderScale * ssaaFactor(config.aa);""", """        auto const manualRenderScale = g_renderScale.load(std::memory_order_relaxed);
        auto const usesFsrPreset = config.upscaling == UpscaleMethod::Fsr ||
            config.upscaling == UpscaleMethod::Fsr12;
        auto const fsrPresetScale = usesFsrPreset ?
            g_fsrPresetScale.load(std::memory_order_relaxed) : 1.f;
        auto const effectiveScale = manualRenderScale * fsrPresetScale * ssaaFactor(config.aa);""")
sub("""    bindStringSetting("upscale-method", updateUpscaleMethod);""", """    bindStringSetting("upscale-method", updateUpscaleMethod);
    bindStringSetting("fsr-quality-preset", updateFsrQualityPreset);""")
main.write_text(s)



shader_header = Path("src/shaders/PostProcessShaders.hpp")
h = shader_header.read_text()
old = "    extern render::PostProcessShader const kFsrShader;\n"
if h.count(old) != 1:
    raise SystemExit("Could not locate FSR shader declaration")
shader_header.write_text(h.replace(old, old + "    extern render::PostProcessShader const kFsrRcasShader;\n    extern render::PostProcessShader const kSgsr1Shader;\n", 1))

mod_path = Path("mod.json")
mod = json.loads(mod_path.read_text())
mod["id"] = "tiromixo2013.bettervisuals-gsr"
mod["name"] = "BetterVisuals GSR1"
version = "v2.3.6"
if not __import__("re").fullmatch(
    r"v\d+\.\d+\.\d+(?:-(?:alpha|beta|prerelease|pr)(?:\.\d+)?)?",
    version,
):
    raise SystemExit(f"Invalid Geode version: {version}")
mod["version"] = version
mod["developer"] = "tiromixo2013"
mod.setdefault("links", {})["source"] = "https://github.com/tiromixo2013-netizen/-"
opts = mod["settings"]["upscale-method"]["one-of"]
if "FSR 1.2" not in opts:
    opts.append("FSR 1.2")
if "SGSR1" not in opts:
    opts.append("SGSR1")
mod["settings"]["upscale-method"]["description"] = (
    "Choose an independent spatial upscaler: FSR 1 (EASU), FSR 1.2 (EASU + RCAS), or SGSR1."
)
mod["settings"]["fsr-sharpness"]["name"] = "FSR 1 / FSR 1.2 RCAS Sharpness"
mod["settings"]["fsr-sharpness"]["description"] = (
    "Controls FSR 1 reconstruction blend and FSR 1.2 RCAS sharpening."
)
mod["settings"]["fsr-quality-preset"] = {
    "type": "string",
    "name": "FSR Quality Preset",
    "description": "Extra FSR input-resolution multiplier. It multiplies with the manual Render Scale; it does not replace it.",
    "default": "Quality",
    "one-of": ["Ultra Quality", "Quality", "Balanced", "Performance", "Ultra Performance"],
    "enable-if": "saved:fsr-preset-enabled",
    "enable-if-description": "Select FSR 1 or FSR 1.2 in Upscale Method"
}
mod_path.write_text(json.dumps(mod, indent=2) + "\n")

# Ensure the renderer is reset if the scene-capture pipeline takes the downsample path.
print("Independent FSR 1, FSR 1.2 EASU+RCAS, and SGSR1 paths with shared quality presets applied.")
