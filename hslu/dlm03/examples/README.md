# Examples

Small code bases used by the notebooks.

- `autofix_project/`: a tiny Python project containing linting issues on purpose. It is used by the
  "Auto-fix", "Agent" and "MCP" notebooks of Week 02. The notebooks never modify it directly: they first copy
  it into the git-ignored `workspace/` folder at the root of the repository and work on that copy, so you can
  re-run them as many times as you want.
