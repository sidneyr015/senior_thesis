date_created = "2025-11-13_10-13"
prompt = """
You analyze Rust code for typestate-based and invariant-based behavior.

Your task: extract one JSON entry per state. A "state" may be:
1. an explicit typestate encoded at compile time
2. an implicit conceptual state implied by temporal order or state-consistency rules in the API.

Definitions:

entity: the struct or type whose behavior exhibits state-dependent invariants.
state: either a concrete compile-time state (e.g., Start, Headers) OR an implicit runtime state inferred from method sequencing (e.g., "uninitialized", "opened", "closed").
state_dimensions: how the state is encoded or inferred (generic S: State, PhantomData<S>, trait bound, enum variant, method availability pattern, required ownership, etc.)

temporal_invariant: a rule that constrains the legal order of operations, even if not encoded with types. Example: “open must be called before read”.

state_consistency_invariant: a rule that constrains which operations are valid in a given state. Example: “cannot write after finalized()”.

implicit_state: a conceptual state inferred from signatures, mutability, consumption of self, or method availability, even if not represented in types.

invariants: rules that must always hold when the entity is in that state. These may come from explicit typestate structure OR implicit temporal/state-consistency analysis.

transitions: any method that consumes self and returns a value in a different state. For implicit cases, transitions come from method behavior patterns (e.g., self-consuming patterns, disabling operations, or producing new capability sets).

implicit_invariants: temporal or state-consistency conditions inferred even when types do not encode them explicitly.

evidence_lines: lines supporting invariants or transitions.

Important rules:

Every valid state — explicit or implicit — must appear as its own entry.

If a state has no transitions, still produce an entry with "transitions": [].

Include:
1. explicit typestate structure (generics, PhantomData, marker types)
2. implicit invariants about temporal order and state consistency drawn from API structure

Do NOT include:
- value-dependent runtime logic
- unrelated control-flow behavior

If no explicit typestate exists, still extract implicit states or invariant groups whenever temporal or state-consistency rules appear. If absolutely no such structure exists, return an empty typestate_table.

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
"implicit_invariants": ["<temporal rule>", "<state-consistency rule>"],
"transitions": ["<ThisState -> NextState via method()>", ...],
"evidence_lines": [<int>, ...]
}
]
}

Explicit Typestate Examples:

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

Implicit Example: 

Rust code:

pub struct FileHandle {
    fd: i32,
    is_open: bool,
}

impl FileHandle {
    pub fn open(path: &str) -> FileHandle {
        FileHandle { fd: 3, is_open: true }
    }

    pub fn read(&self) -> Result<Vec<u8>, &'static str> {
        if !self.is_open { return Err("closed") }
        Ok(vec![1, 2, 3])
    }

    pub fn close(mut self) -> Result<(), &'static str> {
        if !self.is_open { return Err("already closed") }
        self.is_open = false;
        Ok(())
    }
{
  "file": "<file_path>",
  "line_range": { "start": 1, "end": 34 },
  "typestate_table": [
    {
      "entity": "FileHandle",
      "state": "Open",
      "state_dimensions": "implicit state inferred from method requirements and self-consuming close()",
      "invariants": [
        "file descriptor is valid",
        "resource is open",
        "read() operations are valid"
      ],
      "transitions": [
        "Open -> Closed via close()"
      ],
      "evidence_lines": [8, 13, 19]
    },
    {
      "entity": "FileHandle",
      "state": "Closed",
      "state_dimensions": "implicit state inferred from invalidity of read() and post-close behavior",
      "invariants": [
        "resource is closed",
        "read() operations are invalid",
        "no legal transitions remain"
      ],
      "transitions": [],
      "evidence_lines": [10, 20, 22]
    }
  ]
}
}


"""