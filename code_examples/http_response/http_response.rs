// S is the state parameter. We require it to impl
// our ResponseState trait (below) to prevent users
// from trying weird types like HttpResponse<u8>.
struct HttpResponse<S: ResponseState> {
    // This is the same field as in the previous example.
    state: Box<ActualResponseState>,
    // This reassures the compiler that the parameter
    // gets used.
    marker: std::marker::PhantomData<S>,
}

// State type options.
enum Start {} // expecting status line
enum Headers {} // expecting headers or body

trait ResponseState {}
impl ResponseState for Start {}
impl ResponseState for Headers {}

/// Operations that are valid only in Start state.
impl HttpResponse<Start> {
    fn new() -> Self {
        // ...
    }

    fn status_line(self, code: u8, message: &str)
        -> HttpResponse<Headers>
    {
        // ...
    }
}

/// Operations that are valid only in Headers state.
impl HttpResponse<Headers> {
    fn header(&mut self, key: &str, value: &str) {
        // ...
    }

    fn body(self, contents: &str) {
        // ...
    }
}