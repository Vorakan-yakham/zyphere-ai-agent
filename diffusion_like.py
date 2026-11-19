"""Diffusion-LIKE guided refinement (NumPy, CPU, no torch).

HONEST: this is NOT a trained diffusion model (no UNet, no learned reverse
process, no diffusion weights available here). It is an INSPIRED iterative
procedure: start from noise, repeatedly denoise while being guided toward a
real reference photograph, then inject the photograph's high-frequency detail
back at finer and finer scales. The result is a coherent, textured image whose
structure comes from genuine photography — not invented faces.

It is useful as a polish pass for covers/posters where a slightly more painted,
cinematic texture is wanted, while keeping real-world detail.
"""
import os, time, json, hashlib
import numpy as np
from PIL import Image, ImageFilter, ImageEnhance

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data", "diffusion_like.json")


def _blur(im, radius):
    return im.filter(ImageFilter.GaussianBlur(max(0.3, float(radius))))


def _box_blur_np(a, k=3):
    """Simple separable box blur using cumulative sums (no scipy)."""
    p = np.pad(a, ((k, k), (k, k), (0, 0)), mode="edge")
    c = np.cumsum(np.cumsum(p, axis=0), axis=1)
    c = np.pad(c, ((1, 0), (1, 0), (0, 0)))
    H, W, _ = a.shape
    s = c[2*k:, 2*k:] - c[:-2*k, 2*k:] - c[2*k:, :-2*k] + c[:-2*k, :-2*k]
    return s / (k*k)


def guided_refine(photo, steps=14, seed=0, strength=0.85, apply=True):
    """Iterative noise->photo refinement. `photo` is the conditioning image."""
    rng = np.random.default_rng(seed % (2**31))
    target = np.asarray(photo.convert("RGB"), dtype=np.float32) / 255.0
    h, w = target.shape[:2]
    # start: noise blended with a heavily blurred version of the condition
    start = rng.normal(0.42, 0.16, size=target.shape).astype(np.float32)
    coarse = np.asarray(_blur(photo.convert("RGB"), 26), dtype=np.float32) / 255.0
    x = (1 - strength) * start + strength * coarse
    x = np.clip(x, 0, 1)

    history = []
    for i in range(steps):
        p = (i + 1) / steps
        # radius shrinks: big denoise early, fine detail late (like a reverse
        # diffusion schedule moving from low to high frequency).
        radius = max(0.6, 22.0 * (1 - p) ** 1.6)
        x_im = Image.fromarray((np.clip(x, 0, 1) * 255).astype(np.uint8))
        den = np.asarray(_blur(x_im, radius), dtype=np.float32) / 255.0
        # guidance toward the real photo, stronger at coarse stages
        guide = 0.30 * (1 - p) + 0.06
        x = (1 - guide) * den + guide * target
        # inject high-frequency residual from the photo at this scale
        photo_s = np.asarray(_blur(photo.convert("RGB"), max(0.6, radius)),
                             dtype=np.float32) / 255.0
        residual = target - photo_s
        x = x + residual * (0.22 * (1 - p) + 0.05)
        x = np.clip(x, 0, 1)
        history.append(round(float(np.mean(np.abs(x - target))), 4))

    out = Image.fromarray((x * 255).astype(np.uint8))
    out = out.filter(ImageFilter.UnsharpMask(radius=1.1, percent=112, threshold=2))
    out = ImageEnhance.Contrast(out).enhance(1.04)
    rec = {"t": int(time.time()), "steps": steps, "error_history": history,
           "note": "diffusion-INSPIRED iterative refinement (not a trained model)"}
    if apply:
        os.makedirs(os.path.dirname(DATA), exist_ok=True)
        json.dump(rec, open(DATA, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return out, rec


def run(photo_path=None, apply=True):
    if not photo_path:
        import free_image_sources as FIS
        im, credit = FIS.best("cinematic detailed landscape light", want_photo=True)
        if im is None:
            return {"ok": True, "skipped": True,
                    "note": "transient image-source miss; retry next pulse"}
    else:
        im = Image.open(photo_path).convert("RGB")
        credit = {"page": os.path.basename(photo_path)}
    out, rec = guided_refine(im, seed=abs(hash(str(credit.get("page", "")))) % 9999)
    p = os.path.join(ROOT, "media", "diffusion_like_%d.png" % int(time.time()))
    out.save(p)
    rec.update({"ok": True, "file": p, "credit": credit})
    if apply:
        os.makedirs(os.path.dirname(DATA), exist_ok=True)
        json.dump(rec, open(DATA, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return rec


if __name__ == "__main__":
    r = run()
    print(json.dumps({"ok": r.get("ok"), "file": r.get("file"),
                      "steps": r.get("steps")}, ensure_ascii=False))
