# Project Guidelines

## SPOQ Methodology

This project uses [SPOQ](https://spoqpaper.com) (Specialist Orchestrated Queuing) for multi-agent development.

### Common Commands

```bash
# Plan an epic
/epic-planning "Feature description"

# Validate an epic
/epic-validation @spoq/epics/active/epic-name

# Execute an epic
/agent-execution @spoq/epics/active/epic-name

# Execute with agent teams (persona-specialized)
/team-execution @spoq/epics/active/epic-name

# Validate completed work
/agent-validation

# Plan a multi-epic program
/epic-planning --map "Program name"
```

### Validation Thresholds

- **Planning**: 95 avg / 90 min
- **Code**: 95 avg / 80 min

### Repository Structure

- `.claude/skills/` - SPOQ skill definitions
- `code/` - Application source code
- `documents/` - Documentation
- `spoq/epics/` - Epic and task definitions
- `spoq/maps/` - Multi-epic program maps
- `infrastructure/` - Docker and Terraform configs
- `tests/` - Integration and end-to-end tests
- `journal.md` - Development journal
- `TODO.yml` - Time-boxed task tracker

### MCP Server

The SPOQ MCP server provides tools for epic, map, and task management.
Configure in `.mcp.json`:

```json
{
  "mcpServers": {
    "spoq": {
      "command": "spoq",
      "args": ["mcp"]
    }
  }
}
```

### Workflow

1. **Plan** — `/epic-planning` decomposes goals into atomic tasks
2. **Validate** — `/epic-validation` scores against 10 quality metrics
3. **Execute** — `/agent-execution` dispatches parallel agent swarms
4. **Verify** — `/agent-validation` scores delivered code

### Git Operations

- NEVER create commits automatically - user handles git
- Update journal.md when completing significant work
