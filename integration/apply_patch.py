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

sub("""        Fsr,
    };""", """        Fsr,
        Sgsr1,
    };""")
sub("""    bv::render::PostProcessRenderer g_fsrRenderer;
    bv::render::PostProcessRenderer g_casRenderer;""", """    bv::render::PostProcessRenderer g_fsrRenderer;
    bv::render::PostProcessRenderer g_sgsr1Renderer;
    bv::render::PostProcessRenderer g_casRenderer;""")
sub("""        g_fsrRenderer.reset();
        g_casRenderer.reset();""", """        g_fsrRenderer.reset();
        g_sgsr1Renderer.reset();
        g_casRenderer.reset();""")
sub("""        if (value == "FSR 1") {
            g_upscaleMethod.store(UpscaleMethod::Fsr, std::memory_order_relaxed);
            return;
        }

        if (value != "Nearest") {""", """        if (value == "FSR 1") {
            g_upscaleMethod.store(UpscaleMethod::Fsr, std::memory_order_relaxed);
            return;
        }
        if (value == "SGSR1") {
            g_upscaleMethod.store(UpscaleMethod::Sgsr1, std::memory_order_relaxed);
            return;
        }

        if (value != "Nearest") {""")
sub("""            else if (config.upscaling == UpscaleMethod::Fsr) {
                g_renderScaleRenderer.reset();
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
            else if (config.upscaling == UpscaleMethod::Sgsr1) {
                g_renderScaleRenderer.reset();
                g_fsrRenderer.reset();
                g_ssaaRenderer.reset();
                prepared = g_sgsr1Renderer.prepare(
                    bv::shaders::kSgsr1Shader, key.width, key.height
                );
            }
            else {
                g_fsrRenderer.reset();
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
                g_sgsr1Renderer.reset();
                g_renderScaleRenderer.reset();""")
sub("""            g_renderScaleRenderer.reset();
            g_fsrRenderer.reset();
            g_ssaaRenderer.reset();""", """            g_renderScaleRenderer.reset();
            g_fsrRenderer.reset();
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
                else if (config.upscaling == UpscaleMethod::Sgsr1) {
                    g_sgsr1Renderer.apply(sourceTexture);
                }
                else {
                    g_renderScaleRenderer.apply(sourceTexture);
                }""")
# Add the full two-pass FSR 1 path: EASU at source size, RCAS at output size.
sub("""        GLsizei height = 0;
        bool needsPresentation = false;""", """        GLsizei height = 0;
        GLsizei outputWidth = 0;
        GLsizei outputHeight = 0;
        bool needsPresentation = false;""")
sub("""    bv::render::PostProcessPipeline g_postProcessPipeline;
    bv::render::PostProcessRenderer g_fxaaRenderer;""", """    bv::render::PostProcessPipeline g_postProcessPipeline;
    bv::render::PostProcessPipeline g_fsrOutputPipeline;
    bv::render::PostProcessRenderer g_fsrRcasRenderer;
    bv::render::PostProcessRenderer g_fxaaRenderer;""")
sub("""        if (value == "FSR 1") {""", """        if (value == "FSR 1.2 (EASU + RCAS)" || value == "FSR 1") {""")
sub("""                g_fsrRenderer.reset();
                g_sgsr1Renderer.reset();
                g_casRenderer.reset();""", """                g_fsrRenderer.reset();
                g_sgsr1Renderer.reset();
                g_fsrOutputPipeline.reset();
                g_fsrRcasRenderer.reset();
                g_casRenderer.reset();""")
sub("""            if (key.needsDownsample) {
                g_fsrRenderer.reset();
                g_sgsr1Renderer.reset();
                g_renderScaleRenderer.reset();""", """            if (key.needsDownsample) {
                g_fsrRenderer.reset();
                g_sgsr1Renderer.reset();
                g_fsrOutputPipeline.reset();
                g_fsrRcasRenderer.reset();
                g_renderScaleRenderer.reset();""")
sub("""            else if (config.upscaling == UpscaleMethod::Fsr) {
                g_renderScaleRenderer.reset();
                g_sgsr1Renderer.reset();
                g_ssaaRenderer.reset();
                prepared = g_fsrRenderer.prepare(bv::shaders::kFsrShader, key.width, key.height);
            }""", """            else if (config.upscaling == UpscaleMethod::Fsr) {
                g_renderScaleRenderer.reset();
                g_sgsr1Renderer.reset();
                g_ssaaRenderer.reset();
                prepared = g_fsrRenderer.prepare(bv::shaders::kFsrShader, key.width, key.height) &&
                    g_fsrOutputPipeline.prepare(key.outputWidth, key.outputHeight) &&
                    g_fsrRcasRenderer.prepare(
                        bv::shaders::kFsrRcasShader, key.outputWidth, key.outputHeight
                    );
            }""")
sub("""            else if (config.upscaling == UpscaleMethod::Sgsr1) {
                g_renderScaleRenderer.reset();
                g_fsrRenderer.reset();
                g_ssaaRenderer.reset();""", """            else if (config.upscaling == UpscaleMethod::Sgsr1) {
                g_renderScaleRenderer.reset();
                g_fsrRenderer.reset();
                g_fsrOutputPipeline.reset();
                g_fsrRcasRenderer.reset();
                g_ssaaRenderer.reset();""")
sub("""            else {
                g_fsrRenderer.reset();
                g_sgsr1Renderer.reset();
                g_ssaaRenderer.reset();""", """            else {
                g_fsrRenderer.reset();
                g_sgsr1Renderer.reset();
                g_fsrOutputPipeline.reset();
                g_fsrRcasRenderer.reset();
                g_ssaaRenderer.reset();""")
sub("""            g_renderScaleRenderer.reset();
            g_fsrRenderer.reset();
            g_sgsr1Renderer.reset();
            g_ssaaRenderer.reset();""", """            g_renderScaleRenderer.reset();
            g_fsrRenderer.reset();
            g_sgsr1Renderer.reset();
            g_fsrOutputPipeline.reset();
            g_fsrRcasRenderer.reset();
            g_ssaaRenderer.reset();""")
sub("""        PostProcessKey const key{
            config, internalWidth, internalHeight, needsPresentation, needsDownsample
        };""", """        PostProcessKey const key{
            config, internalWidth, internalHeight, width, height, needsPresentation, needsDownsample
        };""")
sub("""                else if (config.upscaling == UpscaleMethod::Fsr) {
                    g_fsrRenderer.apply(sourceTexture, g_fsrSharpness.load(std::memory_order_relaxed));
                }""", """                else if (config.upscaling == UpscaleMethod::Fsr) {
                    // EASU writes the upscaled image to a dedicated output-sized target.
                    g_fsrOutputPipeline.beginSceneCapture();
                    g_fsrOutputPipeline.bindQuad();
                    auto const fsrTarget = g_fsrOutputPipeline.nextTarget();
                    glBindFramebuffer(GL_FRAMEBUFFER, fsrTarget.framebuffer);
                    glViewport(fsrTarget.x, fsrTarget.y, fsrTarget.width, fsrTarget.height);
                    g_fsrRenderer.apply(sourceTexture, 1.f);
                    g_fsrOutputPipeline.advanceStage();

                    // Restore the captured source texture's normal sampling before RCAS.
                    glBindTexture(GL_TEXTURE_2D, sourceTexture);
                    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
                    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);

                    glBindFramebuffer(GL_FRAMEBUFFER, callerTarget.framebuffer);
                    glViewport(callerTarget.x, callerTarget.y, callerTarget.width, callerTarget.height);
                    g_fsrRcasRenderer.apply(
                        g_fsrOutputPipeline.currentTexture(),
                        g_fsrSharpness.load(std::memory_order_relaxed)
                    );
                }""")
main.write_text(s)

shader_header = Path("src/shaders/PostProcessShaders.hpp")
h = shader_header.read_text()
old = "    extern render::PostProcessShader const kFsrShader;\n"
if h.count(old) != 1:
    raise SystemExit("Could not locate FSR shader declaration")
shader_header.write_text(h.replace(old, old + "    extern render::PostProcessShader const kSgsr1Shader;\n    extern render::PostProcessShader const kFsrRcasShader;\n", 1))

mod_path = Path("mod.json")
mod = json.loads(mod_path.read_text())
mod["id"] = "tiromixo2013.bettervisuals-gsr"
mod["name"] = "BetterVisuals GSR1"
version = "v2.3.5"
if not __import__("re").fullmatch(
    r"v\d+\.\d+\.\d+(?:-(?:alpha|beta|prerelease|pr)(?:\.\d+)?)?",
    version,
):
    raise SystemExit(f"Invalid Geode version: {version}")
mod["version"] = version
mod["developer"] = "tiromixo2013"
mod.setdefault("links", {})["source"] = "https://github.com/tiromixo2013-netizen/-"
opts = mod["settings"]["upscale-method"]["one-of"]
if "SGSR1" not in opts:
    opts.append("SGSR1")
mod["settings"]["upscale-method"]["description"] = (
    "Choose the spatial upscaler: FSR EASU + RCAS or Qualcomm SGSR1."
)
mod_path.write_text(json.dumps(mod, indent=2) + "\n")

# Ensure the renderer is reset if the scene-capture pipeline takes the downsample path.
print("SGSR1 and FSR EASU+RCAS patches applied to BetterVisuals source.")
