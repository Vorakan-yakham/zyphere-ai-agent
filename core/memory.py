import json
import os

MEMORY_FILE = "memory/memory.json"

def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"owner": "Vorakan Yakham", "facts": []}

def save_fact(fact: str):
    data = load_memory()
    data["facts"].append(fact)
    os.makedirs("memory", exist_ok=True)
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
