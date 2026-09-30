# AlgoViz Backend

The backend is the HTTP API and static-analysis service behind AlgoViz. It accepts a public GitHub repository URL or a ZIP upload, inspects supported source files and package manifests, and returns structured analysis results for the frontend. It also calls the separate AI engine with compact metadata to generate an explanation.

## Request flow

1. Validate the submitted public GitHub URL or ZIP request.
2. Clone a public GitHub repository into a temporary directory, or safely extract an uploaded ZIP into a temporary directory.
3. Scan supported source and manifest files for languages, imports, module relationships, package dependencies, line counts, and configured risk patterns.
4. Send analysis metadata (not raw source files) to the AI engine.
5. Shape the analyzer and explanation output into the format used by the frontend.

Temporary checkouts and extracted files are discarded after each request.

## API endpoints

| Method and path | Input | Purpose |
|---|---|---|
| `POST /api/analyze` | JSON containing a public GitHub `url`; optional `includeDependencies` | Clone and analyze a public repository. |
| `POST /api/analyze/upload` | Multipart `file` (`.zip`) and optional JSON `options` | Safely extract and analyze a ZIP upload. |
| `GET /api/health` | None | Return backend health status. |
| `/docs` | Browser | FastAPI interactive API documentation. |

The service accepts ZIP files up to 30 MB and analyzes a bounded set of source files. It skips common generated, vendor, and virtual-environment folders. The scan is heuristic and should not be treated as a complete security audit.

## Code layout

```text
app/
├── api/analysis.py          # HTTP routes, input handling, and UI result adaptation
├── config/settings.py      # Environment-based service configuration
├── schemas/analysis.py     # Request and response schema definitions
├── services/local_analyzer.py # File collection, import links, manifests, and risk patterns
├── services/engine_client.py  # HTTP client for the separate AI engine
└── main.py                 # FastAPI app, health endpoint, and error responses
```

## Configuration

| Variable | Default | Description |
|---|---|---|
| `BACKEND_HOST` | `0.0.0.0` | Address the API server binds to. |
| `BACKEND_PORT` | `8000` | Backend port. |
| `AI_ENGINE_URL` | `http://localhost:8100` | Base URL of the AI explanation service. |
| `AI_ENGINE_TIMEOUT_SECONDS` | `35` | Timeout for AI-engine requests. |

If the AI engine is unavailable or returns an error, the backend returns a local metadata-based explanation with the analysis.

## Run the API by itself

Python 3.12 and Git are needed for GitHub URL analysis. From this directory in PowerShell:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:AI_ENGINE_URL="http://localhost:8100"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Run the AI engine separately for AI-generated explanations. For normal app use, start all three services from the project root with Docker Compose; see the root README.

