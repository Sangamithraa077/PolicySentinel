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
  FileWarning,
  Share2,
  Play,
} from "lucide-react";
import { NavLink } from "react-router-dom";

interface NavItem {
  to: string;
  label: string;
  icon: typeof LayoutDashboard;
  end?: boolean;
}

interface NavGroup {
  label: string;
  items: NavItem[];
}

const navGroups: NavGroup[] = [
  {
    label: "Overview",
    items: [
      { to: "/", label: "Dashboard", icon: LayoutDashboard, end: true },
      { to: "/reports", label: "Reports", icon: BarChart3 },
    ],
  },
  {
    label: "Policy library",
    items: [
      { to: "/policies", label: "Policies", icon: FileText },
      { to: "/upload", label: "Upload", icon: Upload },
      { to: "/clauses", label: "Clauses", icon: ListTree },
      { to: "/obligations", label: "Obligations", icon: ShieldCheck },
    ],
  },
  {
    label: "Analysis",
    items: [
      { to: "/conflicts", label: "Conflicts", icon: AlertTriangle },
      { to: "/recommendations", label: "Recommendations", icon: Sparkles },
      { to: "/relationships", label: "Relationships", icon: ListTree },
      { to: "/findings", label: "Advanced Findings", icon: FileWarning },
      { to: "/regulatory-dashboard", label: "Regulatory Dashboard", icon: ShieldCheck },
      { to: "/knowledge-graph", label: "Knowledge Graph", icon: Share2 },
    ],
  },
  {
    label: "Workspace",
    items: [
      { to: "/demo-mode", label: "Guided Demo", icon: Play },
      { to: "/settings", label: "Settings", icon: Settings },
    ],
  },
];

export function Sidebar() {
  return (
    <aside className="flex h-full w-64 shrink-0 flex-col bg-neutral-950 text-neutral-300">
      <div className="flex h-16 items-center gap-2.5 px-5">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-600 shadow-lg shadow-brand-600/30">
          <ShieldCheck className="h-4.5 w-4.5 text-white" />
        </div>
        <span className="text-[15px] font-semibold tracking-tight text-white">PolicySentinel</span>
      </div>

      <nav className="flex-1 space-y-5 overflow-y-auto px-3 pb-4 pt-1">
        {navGroups.map((group) => (
          <div key={group.label}>
            <div className="mb-1.5 px-3 text-[10px] font-bold uppercase tracking-wider text-neutral-600">
              {group.label}
            </div>
            <div className="space-y-0.5">
              {group.items.map(({ to, label, icon: Icon, end }) => (
                <NavLink
                  key={to}
                  to={to}
                  end={end}
                  className={({ isActive }) =>
                    `group relative flex items-center gap-3 rounded-md py-2 pl-3 pr-3 text-sm font-medium transition-colors ${
                      isActive
                        ? "bg-white/10 text-white"
                        : "text-neutral-400 hover:bg-white/5 hover:text-neutral-100"
                    }`
                  }
                >
                  {({ isActive }) => (
                    <>
                      <span
                        className={`absolute left-0 top-1/2 h-4 w-0.5 -translate-y-1/2 rounded-r-full bg-brand-500 transition-opacity ${
                          isActive ? "opacity-100" : "opacity-0"
                        }`}
                      />
                      <Icon
                        className={`h-4 w-4 shrink-0 ${isActive ? "text-brand-400" : "text-neutral-500 group-hover:text-neutral-300"}`}
                      />
                      {label}
                    </>
                  )}
                </NavLink>
              ))}
            </div>
          </div>
        ))}
      </nav>
    </aside>
  );
}
