# AlgoViz — Codebase Architecture Visualizer

AlgoViz helps developers understand an unfamiliar codebase. Submit a public GitHub repository or upload a ZIP to see a generated architecture view, file tree, dependency links, risk findings, and a plain-language summary.

## What the project includes

| Area | Contents |
|---|---|
| `frontend/` | Browser interface: landing page, repository and ZIP input, analysis views, diagrams, file tree, insights, and demo history/dashboard screens. |
| `backend/` | FastAPI API that accepts GitHub URLs and ZIP files, analyzes supported source files and manifests, then formats results for the interface. |
| `ai-engine/` | Separate FastAPI service that turns analysis metadata into an onboarding explanation with Groq, or uses a local fallback. |
| `docker-compose.yml` | Connects the three services for local full-stack development. |
| `render.yaml` | Describes the three services for a Render Blueprint deployment. |

## How an analysis works

1. The frontend sends a public GitHub URL or ZIP upload to the backend through its `/api` proxy.
2. The backend clones the public repository or safely extracts the ZIP in a temporary directory.
3. The source analyzer identifies supported source files, import links, package manifests, approximate lines of code, and configured risk patterns.
4. The backend sends a compact metadata summary to the AI engine. It does not send raw source files to the AI service.
5. The frontend displays the analysis, including an architecture diagram, file tree, dependency hotspots, risk findings, and AI explanation.

## Main capabilities

- Analyze public GitHub repositories or ZIP uploads (up to 30 MB).
- Inspect supported JavaScript, TypeScript, Python, Java, Go, Rust, PHP, Ruby, C#, Vue, and Svelte source files.
- View architecture and dependency relationships, detected risk patterns, package information, and repository metadata.
- Download the generated diagram as SVG or Mermaid text and copy the file tree as text.
- Use the AI explanation when configured, with a deterministic local explanation when the AI service is unavailable.

The analyzer is a lightweight static scan, not a full compiler or security audit. Its diagrams and findings are inferred from the files and patterns it recognizes.

## Frontend demo screens

The interface includes Analyze, History, Dashboard, and Admin screens. Login, registration, history, and dashboard data currently use browser local storage; they are demonstration UI, not server-side authentication or shared user storage. The Admin view is also a demo feature.

## Run the full application locally

With Docker Desktop installed, open PowerShell in the project root and run:

```powershell
Copy-Item .env.example .env
docker compose up --build
```

Open <http://localhost:8080>. Add `GROQ_API_KEY` to the local `.env` file if you want Groq-generated explanations; without it, the local explanation fallback is used. Keep `.env` private and out of Git.

## API overview

| Service | Endpoint | Purpose |
|---|---|---|
| Backend | `POST /api/analyze` | Analyze a public GitHub repository URL. |
| Backend | `POST /api/analyze/upload` | Analyze an uploaded ZIP file. |
| Backend | `GET /api/health` | Backend health check. |
| AI engine | `POST /analyze` | Generate an explanation from analysis metadata. |
| AI engine | `GET /health` | AI engine health check. |

The backend also provides interactive API documentation at `/docs` when accessed directly.

## Deployment

`render.yaml` configures the frontend as the public web service and the backend and AI engine as private services. Publish the project to GitHub, then create a Blueprint from the repository in Render. Set `GROQ_API_KEY` in Render's environment settings; do not commit the secret. Check Render's plan and cost information before creating the services.

