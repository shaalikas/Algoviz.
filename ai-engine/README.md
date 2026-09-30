# AlgoViz AI Engine

The AI engine is a standalone FastAPI service that writes a plain-language explanation of an AlgoViz repository analysis. The backend sends it compact metadata—such as repository details, file paths, dependencies, architecture relationships, and risk findings. It does not receive repository source code.

## What it contains

- `api.py` — FastAPI service with `POST /analyze` and `GET /health`.
- `ai/analyzer.py` — bounds and prepares metadata, calls Groq when configured, and validates the model result.
- `ai/prompts.py` — instructions for producing an explanation grounded in the supplied metadata.
- `ai/fallback.py` — deterministic explanation used when Groq is not configured or unavailable.
- `sample_data/sample_metadata.json` — example input for standalone use.
- `main.py` — simple command-line example that runs an analysis on the sample metadata.
- `Dockerfile` and `requirements.txt` — container and runtime dependencies.

## Role in AlgoViz

The backend owns repository retrieval and source analysis. It sends the resulting metadata to this service, then returns the explanation alongside the architecture and risk results to the frontend. Diagram generation and repository scanning are handled by the backend/frontend, not by this AI service.

```text
GitHub URL or ZIP → Backend source analyzer → metadata → AI engine → explanation
                                                     └──────────────→ Frontend results
```

If Groq is not configured, the service still responds using its local metadata-based fallback. If the engine itself cannot be reached, the backend also has a local explanation fallback.

## API

### `GET /health`

Returns a small health response so the combined deployment can check that the service is running.

### `POST /analyze`

Request body:

```json
{
  "metadata": {
    "repository": { "name": "Example", "language": "Python" },
    "files": [{ "path": "app.py" }],
    "dependencies": ["fastapi"],
    "architecture": { "components": ["API", "service"] },
    "detected_risks": []
  }
}
```

The response contains an `explanation`, a `source` label indicating AI or fallback output, and the compact metadata used to generate it.

## Configuration

| Variable | Description |
|---|---|
| `GROQ_API_KEY` | Optional Groq API key. Set as a secret environment variable in deployment; never commit it to Git. |

The default model and API request settings are configured in `ai/analyzer.py`. The service uses Groq's OpenAI-compatible chat-completions API. Without a key, the local fallback is used.

## Run the service by itself

From this directory in PowerShell:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn api:app --host 0.0.0.0 --port 8100
```

To use Groq in the current PowerShell session, set the key before starting the service:

```powershell
$env:GROQ_API_KEY="your_key_here"
```

For the complete AlgoViz application, use the root README's Docker Compose instructions. Render receives the key through its service environment settings.

