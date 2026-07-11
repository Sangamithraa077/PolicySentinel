import { ChevronDown, ChevronRight } from "lucide-react";

import { clauseLabel } from "@/utils/clauseLabel";
import type { ClauseTreeNode } from "@/utils/clauseTree";

interface ClauseTreeRowProps {
  node: ClauseTreeNode;
  depth: number;
  selectedId: string | null;
  collapsedIds: Set<string>;
  onSelect: (id: string) => void;
  onToggle: (id: string) => void;
}

/** One clause + (if expanded) its children, recursively — depth drives
 * indentation via inline style since Tailwind can't generate arbitrary
 * dynamic utility classes from a runtime number. */
export function ClauseTreeRow({
  node,
  depth,
  selectedId,
  collapsedIds,
  onSelect,
  onToggle,
}: ClauseTreeRowProps) {
  const hasChildren = node.children.length > 0;
  const isCollapsed = collapsedIds.has(node.id);
  const isSelected = node.id === selectedId;

  return (
    <li>
      <div
        role="button"
        tabIndex={0}
        onClick={() => onSelect(node.id)}
        onKeyDown={(event) => {
          if (event.key !== "Enter" && event.key !== " ") return;
          event.preventDefault();
          onSelect(node.id);
        }}
        style={{ paddingLeft: `${depth * 1.25 + 0.5}rem` }}
        className={`flex cursor-pointer items-center gap-1.5 rounded-md py-1.5 pr-2 text-sm transition-colors ${
          isSelected
            ? "bg-brand-50 font-medium text-brand-700 dark:bg-brand-500/15 dark:text-brand-100"
            : "text-neutral-600 hover:bg-surface-muted dark:text-neutral-300 dark:hover:bg-neutral-800"
        }`}
      >
        {hasChildren ? (
          <button
            type="button"
            onClick={(event) => {
              event.stopPropagation();
              onToggle(node.id);
            }}
            aria-label={isCollapsed ? "Expand" : "Collapse"}
            className="shrink-0 rounded p-0.5 text-neutral-400 hover:text-neutral-600 dark:hover:text-neutral-200"
          >
            {isCollapsed ? (
              <ChevronRight className="h-3.5 w-3.5" />
            ) : (
              <ChevronDown className="h-3.5 w-3.5" />
            )}
          </button>
        ) : (
          <span className="w-4 shrink-0" aria-hidden="true" />
        )}
        <span className="truncate">{clauseLabel(node)}</span>
      </div>

      {hasChildren && !isCollapsed && (
        <ul>
          {node.children.map((child) => (
            <ClauseTreeRow
              key={child.id}
              node={child}
              depth={depth + 1}
              selectedId={selectedId}
              collapsedIds={collapsedIds}
              onSelect={onSelect}
              onToggle={onToggle}
            />
          ))}
        </ul>
      )}
    </li>
  );
}
