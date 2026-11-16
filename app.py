"""Zyphere local server: เปิดเว็บ + เสียงพูดไทยคุณภาพสูง (Microsoft Edge neural) ใช้ได้ทุกเบราว์เซอร์
ติดตั้ง:  pip install edge-tts      รัน:  python app.py      แล้วเปิด http://localhost:8000
"""
import asyncio, http.server, socketserver, urllib.parse, webbrowser
try:
    import edge_tts
except ImportError:
    edge_tts = None
PORT = 8000
VOICES = {"th": "th-TH-NiwatNeural", "en": "en-GB-RyanNeural"}

async def synth(text, voice, rate):
    com = edge_tts.Communicate(text, voice, rate=rate, pitch="-8Hz")
    out = b""
    async for c in com.stream():
        if c["type"] == "audio":
            out += c["data"]
    return out

class H(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        if u.path != "/tts":
            return super().do_GET()
        q = urllib.parse.parse_qs(u.query)
        try:
            if edge_tts is None:
                raise RuntimeError("ยังไม่ได้ติดตั้ง edge-tts (pip install edge-tts)")
            text = q.get("text", [""])[0][:1000]
            voice = VOICES.get(q.get("lang", ["th"])[0], VOICES["th"])
            pct = int(q.get("rate", ["0"])[0])
            data = asyncio.run(synth(text, voice, f"{pct:+d}%"))
            self.send_response(200)
            self.send_header("Content-Type", "audio/mpeg")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(data)
        except Exception as e:
            self.send_error(500, str(e))

class S(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True

if __name__ == "__main__":
    with S(("", PORT), H) as s:
        print(f"Zyphere: http://localhost:{PORT}")
        webbrowser.open(f"http://localhost:{PORT}")
        s.serve_forever()
