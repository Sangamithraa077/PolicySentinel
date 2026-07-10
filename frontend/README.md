# frontend/ — React Frontend

React 19 + TypeScript + Vite frontend for PolicySentinel.

**Tech stack:** React Router (routing), TanStack Query (server state), Axios (HTTP client), Tailwind CSS v4 (styling, CSS-first config — no `tailwind.config.js`), Lucide React (icons).

## Structure (`src/`)
- `components/` — reusable UI building blocks (`common/`, `layout/` — currently `Sidebar`/`Topbar` shell pieces)
- `pages/` — route-level views (`Dashboard`, `Policies`, `Upload`, `Reports`, `Settings` — placeholders only)
- `layouts/` — page shell templates (`DashboardLayout` — sidebar + topbar + `<Outlet />`)
- `hooks/` — custom React hooks (`useTheme`)
- `contexts/` — React Context providers (`ThemeContext` — light/dark mode)
- `services/` — `apiClient.ts` (shared Axios instance) and `queryClient.ts` (shared TanStack Query client)
- `utils/` — stateless helper functions (none yet)
- `types/` — shared TypeScript types, mirroring backend `schemas/`
- `assets/` — bundled static assets (none yet)
- `styles/` — `globals.css` — Tailwind import + theme tokens + dark-mode variant
- `public/` — unprocessed static files served at root

## Status

Foundation only: routing, layout shell, theme toggle, Axios/TanStack Query wiring, and five placeholder pages. No business logic, data fetching, or non-placeholder UI has been implemented.

## Running locally (without Docker)

```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:3000`. Requires `VITE_API_BASE_URL` in the root `.env` (see `.env.example`) — falls back to `undefined` if unset, since no API calls are made yet.

## Scripts
- `npm run dev` — Vite dev server with HMR
- `npm run build` — typecheck (`tsc -b`) then production build
- `npm run preview` — preview the production build locally
- `npm run lint` — ESLint (flat config, typescript-eslint + react-hooks + react-refresh)
- `npm run typecheck` — `tsc -b --noEmit`

## Running via Docker

See root `docker-compose.yml` — `docker compose up frontend` builds the `development` target (Vite dev server) automatically.
