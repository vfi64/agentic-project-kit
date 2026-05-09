# Design Notes

## Goal

The package generates project skeletons that are immediately usable for human-AI development workflows.

## Design Principles

- generate a fresh repository, never copy private history
- keep stable rules separate from volatile state
- use outcome evidence instead of output claims
- make documentation checkable
- make TODOs machine-readable
- make logs useful for agents but safe to handle
- use GitHub CLI for repository creation instead of storing tokens

## MVP Scope

Version 0.1.0 intentionally focuses on:

- project generation
- agent documentation
- TODO schema
- documentation checks
- TODO checks
- optional GitHub repository creation through `gh`

Risk-register and debt-marker checks are planned for a later version.
