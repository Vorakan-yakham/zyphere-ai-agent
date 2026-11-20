"""Super-Resolution — local real-ESR/EDSR upscaling for AI covers.

The free diffusion endpoint caps native output at ~627px. EDSR x4 (local
TensorFlow model, CPU) reconstructs detail before the final Lanczos fit, so
the published 1200x1800 cover is genuinely sharper than a plain upscale.
"""
import os, cv2, time
from PIL import Image, ImageFilter

ROOT = os.path.dirname(os.path.abspath(__file__))
MODEL = os.path.join(ROOT, "media", "models", "EDSR_x4.pb")
_sr = None


def _model():
    global _sr
    if _sr is None:
        sr = cv2.dnn_superres.DnnSuperResImpl_create()
        sr.readModel(MODEL)
        sr.setModel("edsr", 4)
        _sr = sr
    return _sr


def upscale(im, target=(1200, 1800)):
    """PIL image -> sharp PIL image at target size (EDSR x4 + Lanczos fit)."""
    import numpy as np
    if not os.path.exists(MODEL):
        return im.resize(target, Image.Resampling.LANCZOS)
    rgb = np.array(im.convert("RGB"))[:, :, ::-1]  # PIL RGB -> cv2 BGR
    try:
        big = _model().upsample(rgb)
        out = Image.fromarray(big[:, :, ::-1])
    except Exception:
        out = im
    out = out.resize(target, Image.Resampling.LANCZOS)
    return out.filter(ImageFilter.UnsharpMask(radius=1.2, percent=120, threshold=2))


if __name__ == "__main__":
    import glob
    fs = glob.glob(os.path.join(ROOT, "media", "diffusion_covers", "*.jpg"))
    if fs:
        t = time.time()
        im = Image.open(fs[0]).convert("RGB")
        print("before", im.size)
        out = upscale(im)
        print("after", out.size, "seconds", round(time.time() - t, 1))
        out.save(os.path.join(ROOT, "media", "superres_test.png"))
    else:
        print("no diffusion images yet")
