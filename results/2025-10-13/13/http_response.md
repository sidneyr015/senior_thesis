```markdown
| Entity | State Dimensions | Valid States | Invariants | Transitions |
|---|---|---|---|---|
| `HttpResponse<S>` | `S: ResponseState` | `HttpResponse<Start>` |  - The response is in the initial state.  - No status line or headers have been written. | `status_line(Self) -> HttpResponse<Headers>` |
| `HttpResponse<S>` | `S: ResponseState` | `HttpResponse<Headers>` | - The status line has been written. - Headers may or may not have been written.  - The body has not been written. | `header(&mut Self)` , `body(Self)` |
```