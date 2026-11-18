"""Tests for the in-house advanced_filters pipeline (Pillow only, no network)."""
import ast
import os
import unittest

from PIL import Image

import advanced_filters as af
import own_image_lab as lab

ROOT = os.path.dirname(os.path.abspath(__file__))
SEED = 2026
PROMPT = "Zyphere สายลมสร้างสรรค์"
FORBIDDEN_MODULES = {
    "socket", "urllib", "requests", "http", "httpx", "aiohttp",
    "ftplib", "telnetlib", "smtplib", "xmlrpc",
}
FORBIDDEN_CALLS = ("urlopen(", "requests.get", "requests.post", "socket.socket",
                   "http.client", "urllib.request")


def make_sample(seed=SEED, w=420, h=520):
    """A real sample produced by the lab's original engineer modules, small for tests."""
    p = lab.parse_prompt(PROMPT)
    pal = lab.palette(p["mood"], seed)
    img = lab.mesh(w, h, pal)
    img = lab.texture(img, seed)
    img = lab.depth(img, pal)
    img = lab.silhouette(img, pal)
    img = lab.ornaments(img, pal)
    img = lab.typography(img, PROMPT, pal)
    img = lab.finish(img)
    return img, pal


class TestAdvancedFilters(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sample, cls.palette = make_sample()
        cls.before = af.sharpness_metric(cls.sample)

    def test_sharpness_metric_detects_detail(self):
        blank = af.sharpness_metric(Image.new("RGB", (120, 120), (10, 20, 30)))
        self.assertLess(blank, 1.0)
        self.assertGreater(self.before, blank)

    def test_multiscale_contrast_does_not_regress(self):
        out = af.multiscale_local_contrast(self.sample, seed=SEED)
        after = af.sharpness_metric(out)
        self.assertEqual(out.size, self.sample.size)
        self.assertGreaterEqual(after, self.before)
        print("\n[local contrast] before=%.3f after=%.3f" % (self.before, after))

    def test_pipeline_metrics_improve(self):
        out, metrics = af.apply_pipeline(self.sample, seed=SEED, palette=self.palette)
        self.assertEqual(out.mode, "RGB")
        self.assertEqual(out.size, self.sample.size)
        self.assertEqual(metrics["before"], self.before)
        self.assertGreater(metrics["after"], metrics["before"])
        self.assertEqual(metrics["delta"],
                         round(metrics["after"] - metrics["before"], 3))
        print("[pipeline sample] before=%.3f after=%.3f delta=%+.3f"
              % (metrics["before"], metrics["after"], metrics["delta"]))

    def test_individual_passes_deterministic(self):
        stages = {
            "contrast": lambda: af.multiscale_local_contrast(self.sample, seed=SEED),
            "smooth": lambda: af.edge_aware_smooth(self.sample, seed=SEED),
            "harmony": lambda: af.colour_harmony(self.sample, self.palette, SEED),
            "texture": lambda: af.procedural_texture(self.sample, SEED, self.palette),
        }
        for name, fn in stages.items():
            a, b = fn(), fn()
            self.assertEqual(a.tobytes(), b.tobytes(), name)

    def test_pipeline_deterministic(self):
        a, ma = af.apply_pipeline(self.sample, seed=SEED, palette=self.palette)
        b, mb = af.apply_pipeline(self.sample, seed=SEED, palette=self.palette)
        self.assertEqual(a.tobytes(), b.tobytes())
        self.assertEqual(ma, mb)

    def test_no_network_imports_or_calls(self):
        for name in ("advanced_filters.py", "own_image_lab.py"):
            with open(os.path.join(ROOT, name), "r", encoding="utf-8") as fh:
                source = fh.read()
            roots = set()
            for node in ast.walk(ast.parse(source)):
                if isinstance(node, ast.Import):
                    roots.update(a.name.split(".")[0] for a in node.names)
                elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                    roots.add(node.module.split(".")[0])
            self.assertFalse(roots & FORBIDDEN_MODULES, "%s imports network modules" % name)
            for call in FORBIDDEN_CALLS:
                self.assertNotIn(call, source, "%s contains %s" % (name, call))

    def test_lab_generate_uses_new_passes(self):
        w0, h0 = lab.W, lab.H
        lab.W, lab.H = 360, 450
        try:
            result = lab.generate(PROMPT, apply=False)
        finally:
            lab.W, lab.H = w0, h0
        self.assertIn("advanced_filters", result)
        metrics = result["advanced_filters"]
        self.assertEqual(len(metrics["passes"]), 5)
        self.assertGreaterEqual(metrics["after"], metrics["before"])
        original = ["01 parse", "02 palette", "03 lighting", "04 texture", "05 depth",
                    "06 subject", "07 ornament", "08 layout", "09 type", "10 finish",
                    "11 critique", "12 export"]
        self.assertEqual(result["engines"][:12], original)
        print("[lab generate] before=%.3f after=%.3f delta=%+.3f"
              % (metrics["before"], metrics["after"], metrics["delta"]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
