"""Restricted execution of AI-written code.

Layers: (1) AST allowlist check, (2) separate Python process in isolated mode with a scrubbed environment and an
empty temp cwd, (3) restricted builtins + import allowlist, (4) CPU/memory/file/process rlimits, (5) wall-clock
timeout and output cap.

This is defence in depth for *pure computation helpers*, not a security boundary against a determined attacker.
Code that needs files, network or hardware must go through the approval-gated device layer instead.
"""
import ast
import json
import os
import subprocess
import sys
import tempfile
from typing import Dict

ALLOWED_IMPORTS = {
    "math", "cmath", "statistics", "json", "re", "itertools", "functools", "collections", "datetime", "decimal",
    "fractions", "random", "string", "textwrap", "heapq", "bisect", "dataclasses", "typing", "operator", "enum",
}
BANNED_NAMES = {
    "eval", "exec", "compile", "open", "__import__", "globals", "locals", "vars", "getattr", "setattr", "delattr",
    "input", "breakpoint", "help", "exit", "quit", "memoryview", "dir", "type", "super", "object", "classmethod",
    "staticmethod", "property", "id",
}
SAFE_BUILTIN_NAMES = [
    "abs", "all", "any", "bin", "bool", "bytes", "callable", "chr", "complex", "dict", "divmod", "enumerate",
    "filter", "float", "format", "frozenset", "hash", "hex", "int", "isinstance", "issubclass", "iter", "len",
    "list", "map", "max", "min", "next", "oct", "ord", "pow", "print", "range", "repr", "reversed", "round", "set",
    "slice", "sorted", "str", "sum", "tuple", "zip", "ValueError", "TypeError", "KeyError", "IndexError",
    "ZeroDivisionError", "ArithmeticError", "AssertionError", "Exception", "StopIteration", "RuntimeError",
    "True", "False", "None", "NotImplementedError", "OverflowError", "AttributeError", "bytearray",
]
MAX_CODE_CHARS = 20_000
MAX_OUTPUT = 20_000
TIMEOUT_S = 8


class SandboxViolation(Exception):
    pass


def validate(source: str) -> None:
    """Raise SandboxViolation if the source uses anything outside the allowlist."""
    if len(source) > MAX_CODE_CHARS:
        raise SandboxViolation("โค้ดยาวเกินไป")
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        raise SandboxViolation(f"syntax error: {e.msg} (line {e.lineno})")
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                if a.name.split(".")[0] not in ALLOWED_IMPORTS:
                    raise SandboxViolation(f"import '{a.name}' ไม่อยู่ในรายการที่อนุญาต")
        elif isinstance(node, ast.ImportFrom):
            if node.level or (node.module or "").split(".")[0] not in ALLOWED_IMPORTS:
                raise SandboxViolation(f"import from '{node.module}' ไม่อยู่ในรายการที่อนุญาต")
        elif isinstance(node, ast.Attribute):
            if node.attr.startswith("_"):
                raise SandboxViolation(f"การเข้าถึง attribute '{node.attr}' ถูกห้าม")
        elif isinstance(node, ast.Name):
            if node.id in BANNED_NAMES or node.id.startswith("__"):
                raise SandboxViolation(f"การใช้ '{node.id}' ถูกห้าม")
        elif isinstance(node, ast.Constant) and isinstance(node.value, str) and "__" in node.value:
            raise SandboxViolation("สตริงที่มี '__' ถูกห้าม")
        elif isinstance(node, (ast.Global, ast.Nonlocal, ast.AsyncFunctionDef, ast.Await, ast.Yield, ast.YieldFrom)):
            raise SandboxViolation(f"{type(node).__name__} ไม่รองรับ")


_RUNNER = r'''
import sys, json, io, builtins, resource, contextlib, traceback
def _limits():
    resource.setrlimit(resource.RLIMIT_CPU, (5, 5))
    resource.setrlimit(resource.RLIMIT_AS, (512*1024*1024, 512*1024*1024))
    resource.setrlimit(resource.RLIMIT_FSIZE, (0, 0))
    try: resource.setrlimit(resource.RLIMIT_NPROC, (0, 0))
    except Exception: pass
req = json.loads(sys.stdin.read())
allowed = set(req["allowed_imports"])
real_import = builtins.__import__
def safe_import(name, globals=None, locals=None, fromlist=(), level=0):
    if level or name.split(".")[0] not in allowed:
        raise ImportError("import blocked: " + name)
    return real_import(name, globals, locals, fromlist, level)
safe = {n: getattr(builtins, n) for n in req["safe_builtins"] if hasattr(builtins, n)}
safe["__import__"] = safe_import
safe["__build_class__"] = builtins.__build_class__   # needed for dataclass/enum helpers
ns = {"__builtins__": safe, "__name__": "skill"}
out = io.StringIO()
res = {"ok": False, "stdout": "", "error": ""}
_limits()
try:
    with contextlib.redirect_stdout(out):
        exec(compile(req["code"], "<skill>", "exec"), ns)
        if req.get("snippet"):
            exec(compile(req["snippet"], "<snippet>", "exec"), ns)
    res["ok"] = True
except AssertionError as e:
    res["error"] = "AssertionError: " + str(e)
except BaseException as e:
    res["error"] = type(e).__name__ + ": " + str(e)
res["stdout"] = out.getvalue()[:req["max_output"]]
sys.__stdout__.write(json.dumps(res))
'''


def run_code(code: str, snippet: str = "") -> Dict[str, object]:
    """Returns {"ok": bool, "stdout": str, "error": str}. Never raises."""
    try:
        validate(code)
        if snippet:
            validate(snippet)
    except SandboxViolation as e:
        return {"ok": False, "stdout": "", "error": f"Blocked by sandbox: {e}"}

    payload = json.dumps({"code": code, "snippet": snippet, "allowed_imports": sorted(ALLOWED_IMPORTS),
                          "safe_builtins": SAFE_BUILTIN_NAMES, "max_output": MAX_OUTPUT})
    with tempfile.TemporaryDirectory() as tmp:
        try:
            p = subprocess.run([sys.executable, "-I", "-c", _RUNNER], input=payload, capture_output=True, text=True,
                               timeout=TIMEOUT_S, cwd=tmp, env={"PATH": os.environ.get("PATH", "/usr/bin")})
        except subprocess.TimeoutExpired:
            return {"ok": False, "stdout": "", "error": f"Timeout: เกิน {TIMEOUT_S} วินาที"}
        except Exception as e:  # pragma: no cover
            return {"ok": False, "stdout": "", "error": f"Sandbox failure: {type(e).__name__}"}
    try:
        res = json.loads(p.stdout)
        return {"ok": bool(res["ok"]), "stdout": str(res["stdout"]), "error": str(res["error"])}
    except (json.JSONDecodeError, KeyError):
        err = (p.stderr or "").strip().splitlines()
        return {"ok": False, "stdout": "", "error": "Process failed: " + (err[-1] if err else f"exit {p.returncode}")}
