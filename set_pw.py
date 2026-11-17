import json, os
path = r"C:\Users\vornl\Documents\zyphere\data\credentials.json"
os.makedirs(os.path.dirname(path), exist_ok=True)
d = {}
try:
    with open(path, "r", encoding="utf-8") as f:
        d = json.load(f)
except Exception:
    pass
d["email"] = "vorayakham@gmail.com"
d["password"] = "Sasan!!1975"
with open(path, "w", encoding="utf-8") as f:
    json.dump(d, f, ensure_ascii=False, indent=2)
print("saved to data/credentials.json (gitignored: data/)")
