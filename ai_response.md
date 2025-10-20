## Typestate Invariants

| Entity | State Dimensions | Valid States | Invariants | Transitions |
|---|---|---|---|---|
| `HttpResponse<S>` | `S: ResponseState` | `Start`, `Headers` | The `HttpResponse` object is in a specific state as defined by the `S` generic parameter, enforcing a specific set of allowed operations. | N/A |
| `HttpResponse<Start>` |  `S` | `Start` | Only `status_line` can be called. The response expects a status line. | `status_line(self, code: u8, message: &str) -> HttpResponse<Headers>` |
| `HttpResponse<Headers>` | `S` | `Headers` | Only `header` and `body` can be called. The response expects headers or a body. | `body(self, contents: &str)` |