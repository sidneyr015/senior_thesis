import mcp


client = Client(
    "octocode",
    ["mcp", "--path", "/Users/sidneyrichardson/senior_thesis-1/code_examples/http_response"]
)
result = client.call_tool("graphrag", 
                          {
                              "operation": "search", 
                              "query": "invariants"
                          })