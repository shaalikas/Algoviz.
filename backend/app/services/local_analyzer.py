"""AlgoViz: a small, local code-to-architecture visualizer."""
from __future__ import annotations

import json
import os
import re
import shutil
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

SKIP = {"node_modules", ".git", "vendor", "dist", "build", "coverage", ".venv", "venv", "__pycache__"}
SOURCE = {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".py", ".java", ".go", ".rs", ".php", ".rb", ".cs", ".vue", ".svelte"}
MAX_FILES, MAX_BYTES = 3000, 30 * 1024 * 1024

def safe_extract(zf: zipfile.ZipFile, destination: Path) -> None:
    total = 0
    for member in zf.infolist():
        path = (destination / member.filename).resolve()
        if not path.is_relative_to(destination.resolve()):
            raise ValueError("The ZIP contains an unsafe file path.")
        total += member.file_size
        if total > MAX_BYTES:
            raise ValueError("ZIP expands beyond the 30 MB analysis limit.")
        if not member.is_dir():
            path.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(member) as src, path.open("wb") as out:
                shutil.copyfileobj(src, out)

def collect_files(folder: Path):
    found = []
    for directory, dirs, names in os.walk(folder):
        dirs[:] = [d for d in dirs if d not in SKIP and not d.startswith(".")]
        for name in names:
            path = Path(directory) / name
            if path.suffix.lower() in SOURCE or name in {"package.json", "requirements.txt", "pyproject.toml", "Cargo.toml", "go.mod", "pom.xml", "Dockerfile", "docker-compose.yml"}:
                found.append(path)
                if len(found) >= MAX_FILES: return found
    return found

def analyze(folder: Path, include_deps: bool = True):
    files = collect_files(folder)
    if not files: raise ValueError("No supported source files found in this repository.")
    root = folder
    while len(list(root.iterdir())) == 1 and next(root.iterdir()).is_dir(): root = next(root.iterdir())
    files = [p for p in files if root == p or root in p.parents]
    folders, edges, findings = Counter(), defaultdict(list), []
    total_loc, language = 0, Counter()
    all_paths = {str(p.relative_to(root)).replace("\\", "/") for p in files}
    for path in files:
        rel = str(path.relative_to(root)).replace("\\", "/")
        parts = rel.split("/")
        group = "/".join(parts[:-1]) or "Root"
        folders[group] += 1
        language[path.suffix.lower()] += 1
        try:
            if path.stat().st_size > 1_000_000: continue
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError: continue
        lines = content.splitlines()
        total_loc += len(lines)
        if path.suffix.lower() in SOURCE:
            for target in re.findall(r"(?:import\s+(?:[^'\"]*?\s+from\s+)?|require\s*\(|from\s+)[\"']([^\"']+)[\"']", content):
                if target.startswith("."):
                    base = (Path(rel).parent / target).as_posix()
                    candidates = [base, *(base + ext for ext in SOURCE), base + "/index.js", base + "/index.ts"]
                    match = next((p for p in candidates if p in all_paths), None)
                    if match: edges[rel].append(match)
        patterns = [(r"(?:api[_-]?key|secret|password|token)\s*[:=]\s*[\"'][^\"']{8,}[\"']", "Hardcoded secret", "High"),
                    (r"\beval\s*\(|\bexec\s*\(", "Dynamic code execution", "High"),
                    (r"rejectUnauthorized\s*:\s*false|verify\s*=\s*False", "TLS certificate verification disabled", "High"),
                    (r"\bhttps?://[^\s\"']+", "Plain HTTP URL", "Low")]
        for pattern, title, severity in patterns:
            for match in re.finditer(pattern, content, re.I):
                line = content.count("\n", 0, match.start()) + 1
                findings.append({"title": title, "severity": severity, "file": rel, "line": line, "detail": f"Review {rel}:{line} for {title.lower()} before deployment."})
                if len(findings) >= 80: break
    external = []
    if include_deps:
        for manifest in (root / "package.json", root / "requirements.txt", root / "pyproject.toml", root / "Cargo.toml", root / "go.mod"):
            if not manifest.exists(): continue
            try:
                if manifest.name == "package.json":
                    obj = json.loads(manifest.read_text(encoding="utf-8")); deps = {**obj.get("dependencies", {}), **obj.get("devDependencies", {})}
                    external.extend(list(deps)[:50])
                elif manifest.name == "requirements.txt": external.extend([x.strip().split("[="><!~;")[0] for x in manifest.read_text(encoding="utf-8").splitlines() if x.strip() and not x.startswith("#")][:50])
                else:
                    external.extend(re.findall(r"(?m)^(?:\s{2,})?([A-Za-z0-9_.-]+)\s*(?:=|[<>=])", manifest.read_text(encoding="utf-8"))[:50])
            except (OSError, ValueError): pass
    extensions = Counter(p.suffix.lower() for p in files)
    lang_names = {".js":"JavaScript", ".jsx":"JavaScript", ".ts":"TypeScript", ".tsx":"TypeScript", ".py":"Python", ".java":"Java", ".go":"Go", ".rs":"Rust", ".php":"PHP", ".rb":"Ruby", ".cs":"C#"}
    lang = lang_names.get(extensions.most_common(1)[0][0], "Mixed")
    top = sorted(folders.items(), key=lambda x: (-x[1], x[0]))[:8]
    modules = [{"name": name, "files": count, "sample": [p for p in sorted(all_paths) if ("/".join(p.split("/")[:-1]) or "Root") == name][:6]} for name, count in top]
    return {"name": root.name, "files": len(files), "loc": total_loc, "language": lang, "languages": dict(extensions), "modules": modules,
            "edges": [{"from": a, "to": b} for a, targets in edges.items() for b in targets[:8]][:100], "risks": findings,
            "external": sorted(set(external))[:50], "paths": sorted(all_paths)[:500], "entry": next((p for p in sorted(all_paths) if Path(p).name.lower() in {"index.js", "index.ts", "main.py", "app.py", "main.go", "main.rs", "app.js"}), sorted(all_paths)[0]),
            "about": "Codebase architecture and dependency summary generated from source imports and package manifests."}
