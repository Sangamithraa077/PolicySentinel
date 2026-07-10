# reasoning/ — Infrastructure/Domain Support: Formal Reasoning Engine

Encapsulates the Z3 solver integration used for formal, provable detection of policy conflicts (e.g. logically contradictory rules) as opposed to purely LLM-inferred similarity. Translates policy rules into logical constraints and interprets solver output (SAT/UNSAT + counterexamples) back into domain-meaningful conflict explanations.

Kept separate from `ai/` because it is a deterministic symbolic-reasoning engine, not a probabilistic LLM call — the two are complementary detection strategies.
