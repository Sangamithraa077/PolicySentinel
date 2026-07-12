import {
  BarChart3,
  FileText,
  LayoutDashboard,
  ListTree,
  Settings,
  ShieldCheck,
  Upload,
  AlertTriangle,
  Sparkles,
  Activity,
} from "lucide-react";
import { NavLink } from "react-router-dom";

const navItems = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/executive-dashboard", label: "Executive Summary", icon: Activity, end: false },
  { to: "/policies", label: "Policies", icon: FileText, end: false },
  { to: "/upload", label: "Upload", icon: Upload, end: false },
  { to: "/clauses", label: "Clauses", icon: ListTree, end: false },
  { to: "/obligations", label: "Obligations", icon: ShieldCheck, end: false },
  { to: "/conflicts", label: "Conflicts", icon: AlertTriangle, end: false },
  { to: "/recommendations", label: "Recommendations", icon: Sparkles, end: false },
  { to: "/relationships", label: "Relationships", icon: ListTree, end: false },
  { to: "/reports", label: "Reports", icon: BarChart3, end: false },
  { to: "/settings", label: "Settings", icon: Settings, end: false },
] as const;

export function Sidebar() {
  return (
    <aside className="flex h-full w-60 shrink-0 flex-col border-r border-border bg-surface dark:border-neutral-800 dark:bg-neutral-900">
      <div className="flex h-16 items-center gap-2 px-5">
        <ShieldCheck className="h-6 w-6 text-brand-600" />
        <span className="text-lg font-semibold tracking-tight">PolicySentinel</span>
      </div>

      <nav className="flex-1 space-y-1 px-3 py-2">
        {navItems.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              `flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                isActive
                  ? "bg-brand-50 text-brand-700 dark:bg-brand-500/15 dark:text-brand-100"
                  : "text-neutral-500 hover:bg-surface-muted hover:text-foreground dark:text-neutral-400 dark:hover:bg-neutral-800 dark:hover:text-neutral-100"
              }`
            }
          >
            <Icon className="h-4 w-4" />
            {label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
