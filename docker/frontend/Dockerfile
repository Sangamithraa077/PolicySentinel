# syntax=docker/dockerfile:1
#
# Multi-stage Dockerfile for the React frontend.
# Build context is the REPO ROOT (see docker-compose.yml: context: .),
# so all COPY paths below are prefixed with frontend/, and the production
# stage can also pull nginx.conf from docker/frontend/.
#
# Runs the Vite + React app in frontend/ (see frontend/README.md).
#
# Build targets:
#   development — Vite dev server with HMR, source mounted as a bind volume
#   production  — static build served by nginx
#
# Usage (from repo root):
#   docker build -f docker/frontend/Dockerfile --target development .
#   docker build -f docker/frontend/Dockerfile --target production  .

# ---------------------------------------------------------------------------
# base: shared Node setup
# ---------------------------------------------------------------------------
FROM node:22-alpine AS base
WORKDIR /app

# ---------------------------------------------------------------------------
# dependencies: install node_modules (cached layer)
# ---------------------------------------------------------------------------
FROM base AS dependencies

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

# ---------------------------------------------------------------------------
# development: Vite dev server, source provided via bind mount in compose
# ---------------------------------------------------------------------------
FROM dependencies AS development

ENV NODE_ENV=development

# Source is bind-mounted by docker-compose.yml for live reload; COPY here
# only covers the initial build so the image is runnable standalone.
COPY frontend/ .

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000 || exit 1

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3000"]

# ---------------------------------------------------------------------------
# build: produce the static production bundle
# ---------------------------------------------------------------------------
FROM dependencies AS build

COPY frontend/ .
RUN npm run build

# ---------------------------------------------------------------------------
# production: static bundle served by nginx
# ---------------------------------------------------------------------------
FROM nginx:1.27-alpine AS production

COPY --from=build /app/dist /usr/share/nginx/html
COPY docker/frontend/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:80 || exit 1

CMD ["nginx", "-g", "daemon off;"]
