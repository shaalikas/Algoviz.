# AlgoViz Frontend

The frontend is the browser-facing part of AlgoViz. It uses plain HTML, CSS, and JavaScript, and is served by Nginx. Nginx also forwards `/api/` requests to the backend, so the browser talks to the frontend origin while the backend stays private.

## What is included

- `index.html` — product landing page, feature overview, sample links, and theme toggle.
- `app.html` — analysis workspace and demo account screens.
- `css/app.css` and `css/landing.css` — workspace and landing-page styles, including light/dark themes.
- `js/api.js` — sends GitHub URL and ZIP-upload requests to the backend.
- `js/app.js` — analysis workflow, result views, diagram rendering/export, file-tree display, and browser-local demo history/dashboard/admin behavior.
- `js/landing.js` — landing-page interactions.
- `js/util.js` — shared frontend utilities.
- `assets/favicon.svg` — application icon.
- `nginx.conf` — static-file serving and backend API proxy configuration.
- `Dockerfile` — packages the static site and Nginx configuration for deployment.

## Screens and analysis views

The landing page introduces the product and links to the analyzer. The app workspace accepts a public GitHub repository URL or a ZIP file, then displays:

- Architecture overview and system dependency diagram.
- Inferred session lifecycle and resource-flow views.
- Expandable file tree with a copy-as-text option.
- Repository information, dependency hotspots, and detected risk findings.
- AI summary or local fallback explanation.
- Diagram export as SVG or Mermaid text.

The interface also has Analyze, History, Dashboard, and Admin screens. Login, registration, user roles, and saved analysis history are currently stored in the browser's local storage. These are demo interactions only; the frontend does not implement server authentication or shared account data.

## How it connects to the backend

`js/api.js` sends:

- `POST /api/analyze` with a GitHub URL for repository analysis.
- `POST /api/analyze/upload` as multipart form data for ZIP analysis.

In the combined deployment, Nginx proxies those paths to the backend service. `BACKEND_HOSTPORT` supplies the backend host and port to the Nginx template. The frontend container listens on port `10000`.

## Local use

For a complete working application, start all three services from the project root using Docker Compose. Then open <http://localhost:8080>. See the root README for the full project flow and configuration.

For a UI-only preview, serve this directory with any static web server. Analysis actions require a reachable backend API; opening the HTML files directly may not provide the API proxy.

