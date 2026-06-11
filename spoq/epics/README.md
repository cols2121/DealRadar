# Epic Definitions

This directory contains SPOQ epic definitions.

## Structure

Each epic is a directory containing:
```
epic-name/
├── EPIC.md         # Epic overview, architecture, waves
└── tasks/          # Task YAML files
    ├── 01-task.yml
    ├── 02-task.yml
    └── ...
```

## Creating an Epic

```bash
/epic-planning "Your feature description"
```

## Running an Epic

```bash
# Validate first
/epic-validation @spoq/epics/active/your-epic

# Then execute
/agent-execution @spoq/epics/active/your-epic
```

## Examples

See `example-config-validator/` for a complete working example.
