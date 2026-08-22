import { fileURLToPath, URL } from "node:url";

import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import { defineConfig } from "vite";

// https://vite.dev/config/
export default defineConfig({
  envDir: "../",
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
  },
  server: {
    host: true,
    port: 3000,
    // Docker Desktop bind mounts (esp. from a Windows host) don't reliably
    // forward inotify events into the container, so chokidar's default
    // watcher silently misses file edits — polling is the standard
    // workaround for dev servers running against a bind-mounted volume.
    watch: {
      usePolling: true,
      interval: 300,
    },
  },
});
