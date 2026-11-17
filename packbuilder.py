"""Zyphere Pack-Builder - turn knowledge + media into a SELLABLE download pack.

Per Zyphere's income plan: bundle ready-to-use digital assets (video/audio/
music/subtitle) + a quote sheet into a single .zip the customer downloads from
our OWN /media/ link (no Google Drive / no OTP / free). This is the 'factory'
that makes income real: knowledge -> deliverable product.

HONEST: assembles files we actually have; no fake assets, no auto-posting
(needs owner account/OTP). No gambling/illegal.
"""
import os, json, time, threading, zipfile, io


class PackBuilder:
    def __init__(self, media_dir, out_dir):
        self.media_dir = media_dir
        self.out_dir = out_dir
        self.lock = threading.RLock()
        self.packs = []
        self._load()

    def _load(self):
        try:
            p = os.path.join(self.out_dir, "packs.json")
            self.packs = json.load(open(p, encoding="utf-8")).get("packs", [])
        except Exception:
            pass

    def save(self):
        with self.lock:
            try:
                os.makedirs(self.out_dir, exist_ok=True)
                json.dump({"packs": self.packs[-1000:]},
                          open(os.path.join(self.out_dir, "packs.json"), "w", encoding="utf-8"),
                          ensure_ascii=False, indent=2)
            except Exception:
                pass

    def quote_sheet(self, title, price, items):
        """A plain-text quote sheet (PromptPay terms) - no fake PDF library."""
        lines = [
            "ใบเสนอราคา / QUOTE — Zyphere", "=" * 40,
            "รายการ: " + str(title)[:120],
            "ราคา: %s บาท" % price,
            "ชำระผ่าน: PromptPay 0941939686",
            "- วางเงินแล้วแจ้งสลิป/รหัสอ้างอิง",
            "- ระบบยืนยันแล้วส่งลิงก์ดาวน์โหลด (Delivery Link)",
            "", "รายการในแพ็ก:",
        ]
        for i, it in enumerate(items or [], 1):
            lines.append("  %d. %s" % (i, str(it)[:120]))
        lines += ["", "หมายเหตุ: ผลงานผลิตโดย Zyphere · ลิขสิทธิ์ตามเงื่อนไขที่ตกลง",
                  "งดเว็บพนัน/สิ่งผิดกฎหมายทุกประเภท"]
        return "\n".join(lines)

    def build(self, title="แพ็กสื่อ Zyphere", price=999, files=None, note=""):
        """Bundle existing media files + quote sheet into a downloadable zip."""
        files = [f for f in (files or []) if f]
        os.makedirs(self.out_dir, exist_ok=True)
        safe = "".join(c for c in str(title)[:40] if c.isalnum() or c in "-_ " ).strip().replace(" ", "_") or "pack"
        name = safe + "_" + str(int(time.time())) + ".zip"
        path = os.path.join(self.out_dir, name)
        included = []
        try:
            with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
                z.writestr("QUOTE.txt", self.quote_sheet(title, price, files))
                for f in files:
                    fp = f if os.path.isabs(f) else os.path.join(self.media_dir, f)
                    if os.path.exists(fp):
                        z.write(fp, os.path.basename(fp))
                        included.append(os.path.basename(fp))
        except Exception as e:
            return {"ok": False, "error": str(e)[:200]}
        rec = {"ok": True, "id": "p_" + str(int(time.time() * 1000)),
               "title": str(title)[:120], "price": price, "file": name,
               "url": "/media/" + name, "included": included, "note": str(note or "")[:200],
               "t": int(time.time())}
        with self.lock:
            self.packs.append(rec)
        self.save()
        return rec

    def list_packs(self):
        with self.lock:
            return list(reversed(self.packs[-50:]))

    def stats(self):
        with self.lock:
            return {"packs": len(self.packs), "potential_revenue": sum(p.get("price", 0) for p in self.packs)}

    def snapshot(self):
        with self.lock:
            return {"packs": self.packs[-1000:]}

    def restore(self, data):
        with self.lock:
            if isinstance(data, dict) and "packs" in data:
                self.packs = data.get("packs", [])
                self.save()
                return True
        return False
