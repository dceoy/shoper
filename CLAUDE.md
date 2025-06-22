# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Shoper is a simple shell operator module for Python that provides a clean interface for executing shell commands with features like input/output file tracking, asynchronous execution, and validation. The main class `ShellOperator` wraps subprocess operations with additional functionality for logging, error handling, and file management.

## Architecture

The project consists of a single main module:

- `shoper/shelloperator.py`: Contains the `ShellOperator` class with methods for running shell commands synchronously or asynchronously
- `shoper/__init__.py`: Exports the main class and defines the package version

Key architectural patterns:
- Uses dataclasses for configuration
- Implements both synchronous (`_shell_c`) and asynchronous (`_popen`) execution modes
- Provides file/directory validation before and after command execution
- Supports chaining commands with input/output dependencies

## Development Commands

### Environment Setup
```bash
uv sync                         # Install dependencies and sync environment
```

### Linting and Type Checking
```bash
uv run ruff check .             # Run linter
uv run ruff check . --fix       # Auto-fix linting issues
uv run pyright                  # Run type checker
```

### Testing
```bash
uv run pytest                   # Run tests (if available)
```
There are no formal unit tests. Testing is done via:
- GitHub Actions workflow that installs the package and runs basic functionality tests
- Manual testing using the examples from README.md

### Pre-commit Workflow
**IMPORTANT: Always run these commands before committing:**
```bash
# Run linter and fix issues
uv run ruff check . --fix

# Run type checker
uv run pyright

# Run tests (if available)
uv run pytest
```
All commands must pass before committing changes.

### Building and Installation
```bash
uv sync                         # Install dependencies in sync
uv pip install -e .             # Install in development mode (alternative)
```

## Code Style

- Uses ruff for linting with extensive rule coverage (see pyproject.toml)
- Follows Google docstring convention
- Type hints are required (pyright in strict mode)
- Line length: 88 characters
- Uses dataclasses for configuration objects

## Key Components

### ShellOperator Class
The main class accepts configuration parameters:
- `log_txt`: Optional log file path
- `quiet`: Suppress output
- `executable`: Shell executable (defaults to /bin/bash)
- `print_command`: Whether to print commands before execution

### Core Methods
- `run()`: Execute shell commands with extensive configuration options
- `wait()`: Wait for asynchronous processes to complete
- `_validate_results()`: Validate command execution and outputs