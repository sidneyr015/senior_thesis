def get_code_snippet(file: str, start: int = None, end: int = None, lines: list[int] = None) -> str:
    """
    Return specific lines from a source file, automatically expanding upward
    to include leading Rust comments and doc comments.

    Args:
        file: Path to the file.
        start: Start line number (1-indexed).
        end: End line number (inclusive).
        lines: Optional explicit list of line numbers.

    Returns:
        A formatted string of code lines with their line numbers included.
    """
    try:
        with open(file, "r") as f:
            all_lines = f.readlines()
    except FileNotFoundError:
        return f"Error: file not found - {file}"

    # If explicit list of lines provided, skip expansion logic
    if lines:
        indices = [i - 1 for i in lines if 0 < i <= len(all_lines)]
        snippet = [f"{i+1:>4}: {all_lines[i].rstrip()}" for i in indices]
        return "\n".join(snippet)

    # Must have both start and end
    if start is None or end is None:
        return "Error: must provide either 'lines' or both 'start' and 'end'."

    # Convert to zero-based
    original_start_idx = start - 1
    end_idx = min(end - 1, len(all_lines) - 1)

    # Expand upward to include doc comments and line comments
    expanded_start_idx = original_start_idx
    i = original_start_idx - 1

    while i >= 0:
        line = all_lines[i].rstrip()

        # Comment or doc comment?
        if (
            line.strip().startswith("//") or
            line.strip().startswith("///") or
            line.strip().startswith("//!") or
            line.strip().startswith("/*") or
            line.strip().startswith("*/")
        ):
            expanded_start_idx = i
            i -= 1
            continue

        # Allow blank lines **inside** comment blocks
        if line.strip() == "":
            expanded_start_idx = i
            i -= 1
            continue

        # Stop once we hit actual code
        break

    # Build the final snippet
    indices = range(expanded_start_idx, end_idx + 1)
    snippet = [f"{i+1:>4}: {all_lines[i].rstrip()}" for i in indices]

    return "\n".join(snippet)
