PAIRWISE_PROMPT = """
You are a typestate equivalence judge.

Given two typestate entries:

ENTRY A:
{A}

ENTRY B:
{B}

Decide if they describe the same semantic typestate.

Return one word:
"same"       if the entries describe the same semantic state
"different"  otherwise

Rules:
- Ignore naming differences (Populated vs Initialized).
- Compare invariants by meaning, not wording.
- Ignore evidence_lines.
- Ignore comment fields.
- Only judge equivalence; do not rewrite or modify entries.
"""
