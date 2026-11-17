"""Simple in-memory rate limiter for public API endpoints."""
import time, threading

class RateLimit:
    def __init__(self):
        self.hits = {}
        self.lock = threading.RLock()

    def allow(self, key, limit=20, window=60):
        now = time.time()
        with self.lock:
            arr = [t for t in self.hits.get(key, []) if now - t < window]
            if len(arr) >= limit:
                self.hits[key] = arr
                return False
            arr.append(now)
            self.hits[key] = arr
            return True

    def remaining(self, key, limit=20, window=60):
        now = time.time()
        with self.lock:
            return max(0, limit - len([t for t in self.hits.get(key, []) if now - t < window]))
