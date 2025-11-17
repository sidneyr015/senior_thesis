date_created = "2025-11-07_16-34"
prompt = """
You analyze Rust code for typestate-based invariants.

Your task: extract one JSON entry per concrete state, not per entity.
If an entity has multiple states (e.g., Start, Headers), return one entry for each.

Definitions:

entity: the struct or type whose generic or marker parameter encodes state
state: the concrete compile-time state represented by a type (e.g., Start, Headers)
state_dimensions: how the state is encoded (generic S: State, PhantomData<S>, trait bound, enum variant, etc.)
invariants: rules that must always hold when the entity is in that state. These must come from compile-time structure: type availability, method restrictions, ownership, generic bounds
transitions: any method that consumes self and returns a value in a different state, written as A -> B via method()
evidence_lines: lines supporting invariants or transitions

Important rules:

Every valid state must appear as its own entry.

If a state has no transitions, still produce an entry with "transitions": [].

Only include compile-time typestate structure, not runtime logic.

If no typestate exists, return an empty typestate_table.

Output JSON only:

{
"file": "<file_path>",
"line_range": {"start": <int>, "end": <int>},
"typestate_table": [
{
"entity": "<name>",
"state": "<state_name>",
"state_dimensions": "<description>",
"invariants": ["<condition1>", "<condition2>"],
"transitions": ["<ThisState -> NextState via method()>", ...],
"evidence_lines": [<int>, ...]
}
]
}

Example:

Rust code:
struct HttpResponse<S: ResponseState> { ... }

enum Start {}
enum Headers {}

impl HttpResponse<Start> {
fn status_line(self, ...) -> HttpResponse<Headers> { ... }
}

impl HttpResponse<Headers> {
fn header(&mut self, ...) { ... }
fn body(self, ...) { ... }
}

Expected output:

{
"typestate_table": [
{
"entity": "HttpResponse",
"state": "Start",
"state_dimensions": "generic parameter S: ResponseState (PhantomData<S>)",
"invariants": [
"status line not yet parsed",
"no headers available"
],
"transitions": [
"Start -> Headers via status_line()"
],
"evidence_lines": [5, 8]
},
{
"entity": "HttpResponse",
"state": "Headers",
"state_dimensions": "generic parameter S: ResponseState (PhantomData<S>)",
"invariants": [
"status line already parsed",
"headers may be added",
"body not yet finalized"
],
"transitions": [
"Headers -> Finalized via body()"
],
"evidence_lines": [12, 15]
}
]
}

Return only the JSON.
"""