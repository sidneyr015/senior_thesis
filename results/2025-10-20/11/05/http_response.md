Here's a markdown table detailing the typestate invariants present in the provided Rust code:

| Entity                | State Dimensions | Valid States | Invariants                                                                 | Transitions                               |
|-----------------------|------------------|--------------|---------------------------------------------------------------------------|-------------------------------------------|
| HttpResponse<Start>   | S: ResponseState | Start        | - Initialized with `HttpResponse::new()`                                   | `status_line(self) -> HttpResponse<Headers>` |
|                       |                  |              | - `state` is in start condition                                           |                                           |
|                       |                  |              | - No headers or body added yet                                            |                                           |
|                       |                  |              | - `marker` enforces start state                                           |                                           |
| HttpResponse<Headers> | S: ResponseState | Headers      | - Can add headers with `header()`                                         | `body(self) ->` No transition (final state) |
|                       |                  |              | - Status line has been set (transitioned from Start state)                |                                           |
|                       |                  |              | - `state` in headers condition                                            |                                           |
|                       |                  |              | - Transition to body is possible                                          |                                           |

These rows represent the concrete states that `HttpResponse` can be in, describing what operations are valid and what invariants hold true for each state.