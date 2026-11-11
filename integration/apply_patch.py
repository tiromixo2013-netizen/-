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
sub("""                if (config.upscaling == UpscaleMethod::Fsr) {
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
                }""", """                if (config.upscaling == UpscaleMethod::Fsr) {
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
main.write_text(s)

shader_header = Path("src/shaders/PostProcessShaders.hpp")
h = shader_header.read_text()
old = "    extern render::PostProcessShader const kFsrShader;\n"
if h.count(old) != 1:
    raise SystemExit("Could not locate FSR shader declaration")
shader_header.write_text(h.replace(old, old + "    extern render::PostProcessShader const kSgsr1Shader;\n", 1))

mod_path = Path("mod.json")
mod = json.loads(mod_path.read_text())
mod["id"] = "tiromixo2013.bettervisuals-gsr"
mod["name"] = "BetterVisuals GSR1"
mod["version"] = "v2.3.2-gsr1.1"
mod["developer"] = "tiromixo2013"
mod.setdefault("links", {})["source"] = "https://github.com/tiromixo2013-netizen/-"
opts = mod["settings"]["upscale-method"]["one-of"]
if "SGSR1" not in opts:
    opts.append("SGSR1")
mod["settings"]["upscale-method"]["description"] = (
    "How the game is scaled back up. SGSR1 is the Qualcomm spatial upscaler port."
)
mod_path.write_text(json.dumps(mod, indent=2) + "\n")

# Ensure the renderer is reset if the scene-capture pipeline takes the downsample path.
print("SGSR1 patch applied to BetterVisuals source.")
