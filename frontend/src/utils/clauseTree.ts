import type { Clause } from "@/types/clause";

export interface ClauseTreeNode extends Clause {
  children: ClauseTreeNode[];
}

/**
 * Groups a flat, order_index-sorted clause list (exactly what
 * GET /clauses returns) into a parent/child tree, without re-sorting —
 * a child's order_index always follows its parent's, so appending each
 * node to its parent's `children` array in input order reproduces
 * document order at every level for free.
 *
 * A clause whose `parent_clause_id` isn't present in `clauses` (e.g. a
 * page of results that starts partway through the document) is treated
 * as a root, so nothing silently disappears from the tree.
 */
export function buildClauseTree(clauses: Clause[]): ClauseTreeNode[] {
  const nodesById = new Map<string, ClauseTreeNode>(
    clauses.map((clause) => [clause.id, { ...clause, children: [] }]),
  );

  const roots: ClauseTreeNode[] = [];
  for (const clause of clauses) {
    const node = nodesById.get(clause.id)!;
    const parent = clause.parent_clause_id ? nodesById.get(clause.parent_clause_id) : undefined;
    if (parent) {
      parent.children.push(node);
    } else {
      roots.push(node);
    }
  }
  return roots;
}

/** Every id of a node that has at least one child — used to know which
 * rows need an expand/collapse toggle at all. */
export function collectParentIds(clauses: Clause[]): Set<string> {
  const parentIds = new Set<string>();
  for (const clause of clauses) {
    if (clause.parent_clause_id) parentIds.add(clause.parent_clause_id);
  }
  return parentIds;
}

/** Walks parent_clause_id from `clauseId` up to the root, returning
 * ancestors ordered outermost-first — the "section hierarchy" breadcrumb
 * for a single clause. */
export function getAncestors(clauseId: string, clausesById: Map<string, Clause>): Clause[] {
  const ancestors: Clause[] = [];
  let current = clausesById.get(clauseId);
  while (current?.parent_clause_id) {
    const parent = clausesById.get(current.parent_clause_id);
    if (!parent) break;
    ancestors.unshift(parent);
    current = parent;
  }
  return ancestors;
}
