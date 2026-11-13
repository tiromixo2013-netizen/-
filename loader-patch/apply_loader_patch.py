#!/usr/bin/env python3
"""Apply the paired Android Frame Generation bridge to a Geode Loader checkout."""
from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
java = root / "loader/include/Geode/cocos/platform/android/java/src/org/cocos2dx/lib/Cocos2dxRenderer.java"
jni = root / "loader/include/Geode/cocos/platform/android/jni/Java_org_cocos2dx_lib_Cocos2dxRenderer.cpp"

def replace_once(path: Path, old: str, new: str):
    data = path.read_text()
    count = data.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one exact patch point, found {count}: {old[:90]!r}")
    path.write_text(data.replace(old, new, 1))

replace_once(java, "\tprivate int mScreenHeight;\n",
             "\tprivate int mScreenHeight;\n\tprivate int mFrameGenerationPhase = 0;\n")
replace_once(
    java,
    "\t\tCocos2dxRenderer.nativeRender();\n",
    """\t\tif (this.mFrameGenerationPhase == 0) {
\t\t\tCocos2dxRenderer.nativeRender();
\t\t\tif (Cocos2dxRenderer.nativePresentGeneratedFrame(0)) {
\t\t\t\tthis.mFrameGenerationPhase = 1;
\t\t\t}
\t\t} else {
\t\t\tif (Cocos2dxRenderer.nativePresentGeneratedFrame(1)) {
\t\t\t\tthis.mFrameGenerationPhase = 0;
\t\t\t} else {
\t\t\t\tCocos2dxRenderer.nativeRender();
\t\t\t\tthis.mFrameGenerationPhase = 0;
\t\t\t}
\t\t}
""")
replace_once(java, "\tprivate static native void nativeRender();\n",
             "\tprivate static native void nativeRender();\n\tprivate static native boolean nativePresentGeneratedFrame(final int pPhase);\n")
replace_once(jni, "#include <jni.h>\n", "#include <jni.h>\n#include <atomic>\n")
replace_once(
    jni,
    '''extern "C" {
    JNIEXPORT void JNICALL Java_org_cocos2dx_lib_Cocos2dxRenderer_nativeRender(JNIEnv* env) {
''',
    '''extern "C" {
    using GeodeFrameGenerationPresentCallback = bool (*)(int phase);
    static std::atomic<GeodeFrameGenerationPresentCallback> s_frameGenerationCallback{nullptr};

    __attribute__((visibility("default")))
    void GeodeSetFrameGenerationPresentCallback(GeodeFrameGenerationPresentCallback callback) {
        s_frameGenerationCallback.store(callback, std::memory_order_release);
    }

    JNIEXPORT jboolean JNICALL Java_org_cocos2dx_lib_Cocos2dxRenderer_nativePresentGeneratedFrame(
        JNIEnv*, jclass, jint phase
    ) {
        auto callback = s_frameGenerationCallback.load(std::memory_order_acquire);
        if (!callback || (phase != 0 && phase != 1)) {
            return JNI_FALSE;
        }
        return callback(static_cast<int>(phase)) ? JNI_TRUE : JNI_FALSE;
    }

    JNIEXPORT void JNICALL Java_org_cocos2dx_lib_Cocos2dxRenderer_nativeRender(JNIEnv* env) {
''')
print("Applied Android Loader Frame Generation bridge.")
