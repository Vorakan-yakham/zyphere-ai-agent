"""Zyphere in-house advanced image filters (Pillow + maths only).

NO external image API, NO network, NO dependencies beyond Pillow.
Every routine is deterministic for a given integer ``seed``.

Passes
  1. multi-scale local contrast  - Gaussian difference / unsharp at 3 scales
  2. edge-aware smoothing        - median blur blended through an edge mask
  3. colour harmony              - subtle temperature/tint from the palette
  4. procedural texture          - flow-field lines + recursive fractal circles
  5. sharpness metric            - Laplacian variance proxy (before / after)

The module is intentionally self-contained so own_image_lab.py can compose the
passes without disturbing its original twelve engineer modules.
"""
import math
import random

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageStat

PASSES = (
    "13 edge-aware smoothing",
    "14 colour harmony",
    "15 flow-field + fractal texture",
    "16 multi-scale local contrast",
    "17 sharpness metric",
)

# signed Laplacian, biased to 128 so the response stays inside L-mode range
_LAPLACIAN = ImageFilter.Kernel(
    (3, 3), (0, 1, 0, 1, -4, 1, 0, 1, 0), scale=1, offset=128
)


def _clamp(v, lo=0, hi=255):
    return max(lo, min(hi, v))


def sharpness_metric(img):
    """Laplacian variance proxy: higher means more local high-frequency detail."""
    gray = img.convert("L").filter(ImageFilter.GaussianBlur(0.6))
    response = gray.filter(_LAPLACIAN)
    # Pillow kernels treat outside pixels as zero; drop that border ring so a
    # perfectly flat image scores ~0 instead of inheriting border artifacts.
    margin = 3
    if response.width > 2 * margin and response.height > 2 * margin:
        response = response.crop((margin, margin,
                                  response.width - margin, response.height - margin))
    return round(float(ImageStat.Stat(response).var[0]), 3)


def multiscale_local_contrast(img, seed=0, strength=0.55):
    """Unsharp masking at fine/medium/broad scales (Gaussian-blur difference)."""
    rnd = random.Random(seed)
    out = img.convert("RGB")
    jitter = rnd.uniform(0.92, 1.08)
    for radius, weight in ((1.2, 0.50), (4.0, 0.32), (11.0, 0.18)):
        blurred = out.filter(ImageFilter.GaussianBlur(radius))
        # 128 + (out - blurred): a signed detail layer without clipping losses
        detail = ImageChops.subtract(out, blurred, offset=128)
        sharpened = ImageChops.add(out, detail, offset=-128)
        amount = min(0.9, max(0.0, strength * weight * jitter))
        out = Image.blend(out, sharpened, amount)
    return out


def edge_aware_smooth(img, seed=0, strength=0.30):
    """Bilateral-like approximation: median smoothing only away from edges."""
    rnd = random.Random(seed)
    img = img.convert("RGB")
    ksize = 3 if rnd.random() < 0.75 else 5
    smoothed = img.filter(ImageFilter.MedianFilter(ksize))

    edges = img.convert("L").filter(ImageFilter.FIND_EDGES)
    # flat areas -> 255 (take smoothed), strong edges -> 0 (keep original)
    mask = edges.point(lambda v: _clamp(255 - v * 4))
    mask = mask.filter(ImageFilter.GaussianBlur(1))
    selective = Image.composite(smoothed, img, mask)
    return Image.blend(img, selective, max(0.0, min(1.0, strength)))


def colour_harmony(img, palette=None, seed=0, strength=1.0):
    """Nudge white balance/tint toward the palette accent (subtle, deterministic)."""
    rnd = random.Random(seed)
    img = img.convert("RGB")
    if palette and palette.get("accent"):
        accent = tuple(int(c) for c in palette["accent"][0])
    else:
        accent = tuple(int(c) for c in ImageStat.Stat(img).mean)

    warmth = _clamp((accent[0] - accent[2]) / 255.0, -1.0, 1.0)
    tint = _clamp((accent[1] - (accent[0] + accent[2]) / 2.0) / 128.0, -1.0, 1.0)
    mag = rnd.uniform(0.65, 1.0) * strength
    shifts = (
        int(round(5.0 * warmth * mag)),
        int(round(3.0 * tint * mag)),
        int(round(-5.0 * warmth * mag)),
    )

    channels = []
    for channel, shift in zip(img.split(), shifts):
        channels.append(channel.point([_clamp(i + shift) for i in range(256)]))
    return Image.merge("RGB", channels)


def procedural_texture(img, seed=0, palette=None, density=1.0):
    """Deterministic flow-field strokes + recursive fractal-like circles."""
    rnd = random.Random(seed)
    img = img.convert("RGB")
    w, h = img.size
    scale = max(1, min(w, h))
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)

    if palette and palette.get("accent"):
        base = tuple(int(c) for c in palette["accent"][0])
        second = tuple(int(c) for c in palette["accent"][-1])
    else:
        mean = ImageStat.Stat(img).mean
        base = (_clamp(int(mean[0]) + 70), _clamp(int(mean[1]) + 70),
                _clamp(int(mean[2]) + 70))
        second = base

    # --- flow-field lines -------------------------------------------------
    n_lines = max(18, int(w * h / 14000 * density))
    for _ in range(n_lines):
        x, y = rnd.uniform(0, w), rnd.uniform(0, h)
        phase = rnd.uniform(0, 2 * math.pi)
        alpha = rnd.randrange(12, 30)
        pts = []
        for _ in range(rnd.randrange(7, 16)):
            pts.append((x, y))
            angle = (math.sin(y / scale * 4.0 + phase)
                     + math.cos(x / scale * 3.0 - phase) + phase * 0.15)
            step = scale * rnd.uniform(0.006, 0.014)
            x += step * math.cos(angle)
            y += step * math.sin(angle)
            if x < 0 or x >= w or y < 0 or y >= h:
                break
        if len(pts) > 1:
            draw.line(pts, fill=(*base, alpha), width=1)

    # --- fractal-like circles ---------------------------------------------
    def circles(cx, cy, radius, depth):
        if depth <= 0 or radius < 2.0:
            return
        draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius),
                     outline=(*second, rnd.randrange(10, 22)), width=1)
        for _ in range(3):
            a = rnd.uniform(0, 2 * math.pi)
            dist = radius * rnd.uniform(0.55, 0.90)
            circles(cx + dist * math.cos(a), cy + dist * math.sin(a),
                    radius * rnd.uniform(0.25, 0.45), depth - 1)

    n_clusters = max(3, int(6 * density))
    for _ in range(n_clusters):
        circles(rnd.uniform(0, w), rnd.uniform(0, h),
                scale * rnd.uniform(0.03, 0.08), 3)

    return Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB")


def apply_pipeline(img, seed=0, palette=None):
    """Run every pass in an art-directed order; return image + before/after metrics."""
    before = sharpness_metric(img)
    out = edge_aware_smooth(img, seed=seed, strength=0.30)
    out = colour_harmony(out, palette=palette, seed=seed)
    out = procedural_texture(out, seed=seed, palette=palette)
    out = multiscale_local_contrast(out, seed=seed, strength=0.55)
    after = sharpness_metric(out)
    return out, {"before": before, "after": after,
                 "delta": round(after - before, 3), "passes": list(PASSES)}
