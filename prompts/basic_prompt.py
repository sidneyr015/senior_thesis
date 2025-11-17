date_created = "2025-11-07_16-34"
prompt = """
        You analyze Rust code for typestate-based invariants.
        Focus only on compile-time rules involving ownership, generics, and state transitions.

        Identify:

        entity: the struct, enum, or module representing a stateful type

        state_dimensions: how its type encodes state (e.g. generic parameter, trait bound)

        valid_states: all compile-time states (e.g. Closed, Open)

        invariant: one condition that must always hold (temporal or consistency)

        transition: how one state moves to another (e.g. Closed → Open via open())

        evidence_lines: line numbers supporting this invariant

        Return only this JSON:

        {
        "file": "<file_path>",
        "line_range": {"start": <int>, "end": <int>},
        "typestate_table": [
            {
            "entity": "<name>",
            "state_dimensions": "<description>",
            "valid_states": ["<state1>", "<state2>"],
            "invariant": "<rule>",
            "transition": "<transition or '-'>",
            "evidence_lines": [<int>, ...]
            }
        ]
        }
        If none found, return an empty "typestate_table": [].
    """