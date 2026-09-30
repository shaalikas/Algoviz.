import asyncio
import json
import subprocess
import tempfile
import zipfile
from io import BytesIO
from pathlib import Path
from urllib.parse import urlsplit
from fastapi import APIRouter, File, Form, UploadFile
from fastapi.responses import JSONResponse
from app.services.local_analyzer import analyze, safe_extract
from app.config.settings import get_settings
from app.services.engine_client import EngineClient, EngineFailure, EngineTimeout, EngineUnavailable

router = APIRouter(prefix="/api")


def error(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"success": False, "error": {"code": code, "message": message}})


async def to_ui(raw: dict) -> dict:
    """Adapt analyzer output for the UI and request its metadata-based explanation."""
    modules = raw["modules"]
    names = [module["name"] for module in modules]
    entry = raw["entry"]
    nodes = [[f"N{i}", ("Entry: " if name == entry else "") + name, "api" if name == entry else "core"]
             for i, name in enumerate(names)]
    by_name = {name: f"N{i}" for i, name in enumerate(names)}
    edges = [[by_name[a], by_name[b]] for edge in raw["edges"]
             for a, b in [(str(Path(edge["from"]).parent.as_posix() or "Root"), str(Path(edge["to"]).parent.as_posix() or "Root"))]
             if a in by_name and b in by_name and a != b]
    tree = {}
    for path in raw["paths"]:
        parts = path.split("/")
        current = tree
        for folder in parts[:-1]:
            current = current.setdefault(folder, {})
        current[parts[-1]] = "api" if path == entry else "core"
    hot_counts = {}
    for edge in raw["edges"]:
        hot_counts[edge["from"]] = hot_counts.get(edge["from"], 0) + 1
    risks = [[r["severity"], r["title"], f"{r['detail']} ({r['file']}:{r['line']})"] for r in raw["risks"]]
    if not risks: risks = [["Info", "No common risk patterns found", "The source scan did not match its configured risk patterns."]]
    metadata = {
        "repository": {"name": raw["name"], "language": raw["language"], "description": raw["about"], "entry_points": [entry]},
        "name": raw["name"], "language": raw["language"],
        "files": [{"path": path} for path in raw["paths"][:200]],
        "dependencies": raw["external"],
        "architecture": {"components": names, "layers": ["API entry point", "Core modules"],
                          "data_flow": raw["edges"][:80]},
        "detected_risks": [{"name": risk["title"], "description": risk["detail"],
                             "severity": risk["severity"], "file": risk["file"], "line": risk["line"]}
                            for risk in raw["risks"]],
        "circular_dependencies": [],
    }
    try:
        settings = get_settings()
        ai_result = await EngineClient(settings.ai_engine_url, settings.ai_engine_timeout_seconds).analyze(metadata)
        ai_text, ai_source = ai_result["explanation"], ai_result.get("source", "AI engine")
    except (EngineUnavailable, EngineTimeout, EngineFailure):
        ai_text = f"{raw['name']} contains {raw['files']} supported source and manifest files across {raw['language']} code. The detected entry point is {entry}. The analyzer mapped {len(modules)} major folders and {len(raw['edges'])} file dependency links. {len(raw['external'])} external dependencies were found. The AI service was unavailable for this analysis."
        ai_source = "Local fallback"
    return {"name": raw["name"], "lang": raw["language"], "files": raw["files"], "loc": raw["loc"],
            "about": raw["about"], "nodes": nodes, "edges": edges, "tree": tree,
            "hot": [[path, count] for path, count in sorted(hot_counts.items(), key=lambda x: -x[1])[:10]],
            "cyc": [], "risks": risks,
            "ai": ai_text, "ai_source": ai_source}


def analyze_checkout(folder: Path, include_dependencies: bool = True) -> dict:
    return analyze(folder, include_dependencies)


@router.post("/analyze")
async def analyze_repository(body: dict):
    url = str(body.get("url", "")).strip()
    parsed = urlsplit(url)
    parts = [p for p in parsed.path.strip("/").split("/") if p]
    if parsed.scheme != "https" or parsed.hostname != "github.com" or parsed.username or parsed.password or len(parts) != 2:
        return error(422, "INVALID_REPOSITORY_URL", "Enter a public GitHub URL, such as https://github.com/user/repo.")
    url = f"https://github.com/{parts[0]}/{parts[1].removesuffix('.git')}"
    try:
        with tempfile.TemporaryDirectory(prefix="algoviz-") as temp:
            checkout = Path(temp) / "repo"
            await asyncio.to_thread(subprocess.run, ["git", "clone", "--depth", "1", "--filter=blob:none", url, str(checkout)],
                                    capture_output=True, text=True, timeout=90, check=True)
            result = await asyncio.to_thread(analyze_checkout, checkout, bool(body.get("includeDependencies", True)))
            result["name"] = f"{parts[0]}/{parts[1].removesuffix('.git')}"
            return await to_ui(result)
    except subprocess.TimeoutExpired:
        return error(504, "CLONE_TIMEOUT", "Repository download timed out. Try a smaller repository or upload a ZIP.")
    except subprocess.CalledProcessError:
        return error(400, "CLONE_FAILED", "Could not clone that repository. Check the URL and make sure it is public.")
    except ValueError as exc:
        return error(400, "ANALYSIS_FAILED", str(exc))


@router.post("/analyze/upload")
async def analyze_upload(file: UploadFile = File(...), options: str = Form("{}")):
    if not file.filename or not file.filename.lower().endswith(".zip"):
        return error(400, "INVALID_ZIP", "Upload a ZIP file")
    try:
        parsed_options = json.loads(options)
        if not isinstance(parsed_options, dict): raise ValueError
    except (ValueError, TypeError):
        return error(422, "INVALID_REQUEST", "Options must be a valid JSON object")
    content = await file.read(30 * 1024 * 1024 + 1)
    if len(content) > 30 * 1024 * 1024:
        return error(413, "FILE_TOO_LARGE", "ZIP upload exceeds the configured size limit")
    try:
        with zipfile.ZipFile(BytesIO(content)) as archive, tempfile.TemporaryDirectory(prefix="algoviz-") as temp:
            if archive.testzip() is not None: return error(400, "INVALID_ZIP", "ZIP archive is corrupt")
            root = Path(temp) / "repo"
            root.mkdir()
            safe_extract(archive, root)
            result = await asyncio.to_thread(analyze_checkout, root, bool(parsed_options.get("includeDependencies", True)))
            return await to_ui(result)
    except (zipfile.BadZipFile, OSError):
        return error(400, "INVALID_ZIP", "Upload a valid ZIP archive")
    except ValueError as exc:
        return error(400, "ANALYSIS_FAILED", str(exc))
