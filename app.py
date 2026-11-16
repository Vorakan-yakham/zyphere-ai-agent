"""เปิด Zyphere ในเครื่อง: python app.py แล้วเข้า http://localhost:8000"""
import http.server, socketserver, webbrowser
PORT = 8000
with socketserver.TCPServer(("", PORT), http.server.SimpleHTTPRequestHandler) as s:
    print(f"Zyphere: http://localhost:{PORT}")
    webbrowser.open(f"http://localhost:{PORT}")
    s.serve_forever()
