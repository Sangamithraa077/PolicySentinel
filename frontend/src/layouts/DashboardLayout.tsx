import { Outlet } from "react-router-dom";

import { Sidebar } from "@/components/layout/Sidebar";
import { Topbar } from "@/components/layout/Topbar";

/**
 * Structural shell for all authenticated/dashboard routes. Placeholder
 * only — no data fetching or business logic; renders the sidebar, topbar,
 * and the active page via <Outlet />.
 */
export function DashboardLayout() {
  return (
    <div className="flex h-screen bg-surface-muted dark:bg-neutral-950">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <Topbar />
        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
