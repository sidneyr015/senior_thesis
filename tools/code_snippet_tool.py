def get_code_snippet(file: str, start: int = None, end: int = None, lines: list[int] = None) -> str:
    """
    Return specific lines from a source file.

    Args:
        file: Path to the file.
        start: Start line number (1-indexed).
        end: End line number (inclusive).
        lines: Optional explicit list of line numbers.

    Returns:
        A formatted string of code lines with their line numbers.
    """
    try:
        with open(file, "r") as f:
            all_lines = f.readlines()
    except FileNotFoundError:
        return f"Error: file not found - {file}"

    if lines:
        # handle explicit list of line numbers
        indices = [i - 1 for i in lines if 0 < i <= len(all_lines)]
    elif start is not None and end is not None:
        indices = list(range(start - 1, min(end, len(all_lines))))
    else:
        return "Error: must provide either 'lines' or both 'start' and 'end'."

    snippet = [f"{i+1:>4}: {all_lines[i].rstrip()}" for i in indices]
    return "\n".join(snippet)