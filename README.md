# senior_thesis# Typestate Invariant Detection Agent

An automated agent that uses semantic search and LLM analysis to detect typestate invariants in Rust codebases.

## Overview

This agent combines code graph analysis with semantic search to identify enum-based typestate patterns in Rust code. It extracts typestate invariants, validates them against the codebase structure, and generates structured JSON output with qualified names from the code graph.

## Features

- **Automated Code Graph Generation**: Creates a knowledge graph of your Rust codebase
- **Semantic Search**: Finds enum declarations and typestate patterns
- **LLM-Powered Analysis**: Uses GPT-4o to extract typestate invariants from code snippets
- **Hallucination Correction**: Additional step to validate and fix LLM-generated results
- **Qualified Name Resolution**: Maps detected invariants to their fully qualified names from the code graph

## Prerequisites

- Python 3.11+
- OpenAI API key
- Rust codebase to analyze

## Installation

1. Clone the repository:
```bash
git clone <your-repo-url>
cd senior_thesis-1
```

2. Install dependencies:
```bash
pip install -r requirements.txt
# Universal install script (Linux, macOS, Windows)
curl -fsSL https://raw.githubusercontent.com/Muvon/octocode/master/install.sh | sh
octocode config \
  --code-embedding-model "openai:text-embedding-3-small" \
  --text-embedding-model "openai:text-embedding-3-small"

cd path/to/rust repo 
octocode index
```

4. Set your OpenAI API key:
```bash
export OPENAI_API_KEY=sk-your-openai-key

curl -fsSL https://raw.githubusercontent.com/Muvon/octocode/master/install.sh | sh

octocode config \
  --code-embedding-model "openai:text-embedding-3-small" \
  --text-embedding-model "openai:text-embedding-3-small"

cd path/to/rust repo 
octocode index
```

## Usage

### Basic Pipeline

Run the full typestate detection pipeline on a Rust repository:

```bash
cd senior_thesis-1
python final_agent.py /path/to/rust/repo
```

This will:
1. Generate a code graph (`my_graph.json`)
2. Search for typestate patterns
3. Extract typestate invariants using LLM analysis
4. Map results to qualified names
5. Save results to `results/<timestamp>/personal_once_cell.json`


## Project Structure

```
senior_thesis-1/
├── final_agent.py          # Main pipeline script
├── code_graph_rag/         # Code graph generation module
├── prompts/                # LLM prompts
│   ├── prompt_11_13.py     # Typestate extraction prompt
│   └── clean_up_prompt.py  # Hallucination fix prompt
├── tools/                  # Utility tools
│   ├── semantic_search_tool.py
│   └── code_snippet_tool.py
├── results/                # Output directory (auto-generated)
└── my_graph.json          # Generated code graph
```

## Output Format

Results are saved as JSON with the following structure:

```json
{
  "agent": "semantic_search_haluc_agent",
  "description": "Improvements for Semantic Search Haluc Agent...",
  "prompt": "<prompt used>",
  "results": [
    {
      "file": "src/lib.rs",
      "line_range": {"start": 42, "end": 68},
      "expanded_start_line": 35,
      "typestate_table": [
        {
          "state": "Uninitialized",
          "qualified_name": "once_cell::sync::OnceCell",
          "valid_methods": ["get", "set", "get_or_init"],
          "invalid_methods": []
        }
      ]
    }
  ],
  "token_usage": 15234,
  "timestamp": "2024-12-09T14:30:00.000000"
}
```

## Configuration

The agent uses the following models (configurable in code):

- **Orchestrator**: GPT-4o (for typestate extraction)
- **Cypher**: GPT-4o-mini (for code graph generation)

## Dependencies

Key dependencies include:
- `langchain-core` - LLM framework
- `langchain` - Chain orchestration
- `langgraph` - Graph-based workflows
- `langchain-openai` - OpenAI integration
- `codebase_rag` - Code graph generation

See `merged_two.txt` for complete list.
