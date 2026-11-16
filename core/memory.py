import json, os
MEMORY_FILE = "memory/memory.json"
def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"owner": "Vorakan Yakham", "facts": []}
