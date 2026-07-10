# docker/frontend/ — React Container

`Dockerfile` is a multi-stage build with three stages and two runnable targets:

| Stage/Target | Used by | Behavior |
|---|---|---|
| `development` | `docker-compose.yml` | Runs the Vite dev server with HMR; source is bind-mounted from `../frontend` |
| `build` | (intermediate only) | Runs `npm run build`, producing `/app/dist` |
| `production` | `docker-compose.prod.yml` | Serves the static `dist/` output via `nginx` using `nginx.conf` |

Build context is the **repo root** so the production stage can pull `docker/frontend/nginx.conf` in the same build without crossing outside the Docker build context.

`nginx.conf` handles SPA fallback routing (`try_files ... /index.html`) and reverse-proxies `/api/` to the `backend` container by Docker Compose service name — no application logic, routing config only.

Base image: `node:22-alpine` (matches React 19 / Vite 8 tooling requirements). Uses `npm ci` against the committed `package-lock.json` for reproducible installs.
