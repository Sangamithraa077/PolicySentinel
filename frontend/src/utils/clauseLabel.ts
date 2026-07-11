import type { Clause } from "@/types/clause";

const SNIPPET_LENGTH = 80;

/** A short, single-line label for a clause row: its heading when it has
 * one, otherwise a truncated preview of its text (body paragraphs and
 * bullet points have no heading of their own). */
export function clauseSnippet(clause: Clause): string {
  const source = clause.heading ?? clause.text;
  const singleLine = source.replace(/\s+/g, " ").trim();
  if (singleLine.length <= SNIPPET_LENGTH) return singleLine;
  return `${singleLine.slice(0, SNIPPET_LENGTH).trimEnd()}…`;
}

/** "1.2 Scope of policy", "(a) First requirement", or just a snippet
 * when there's no clause_number at all (body text, bullet points). */
export function clauseLabel(clause: Clause): string {
  const snippet = clauseSnippet(clause);
  return clause.clause_number ? `${clause.clause_number} ${snippet}` : snippet;
}
