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

## Web Search Instructions

For tasks requiring web search, always use `gemini` command instead of the built-in web search tool.

### Usage

```sh
# Basic search query
gemini --sandbox --prompt "WebSearch: <query>"

# Example: Search for latest news
gemini --sandbox --prompt "WebSearch: What are the latest developments in AI?"
```

### Policy

When users request information that requires web search:

1. Use `gemini --sandbox --prompt` command via terminal
2. Parse and present the Gemini response appropriately

This ensures consistent and reliable web search results through the Gemini API.

## Development Methodology

This section combines essential guidance from Martin Fowler's refactoring, Kent Beck's tidying, and t_wada's TDD approaches.

### Core Philosophy

- **Small, safe, behavior-preserving changes** - Every change should be tiny, reversible, and testable
- **Separate concerns** - Never mix adding features with refactoring/tidying
- **Test-driven workflow** - Tests provide safety net and drive design
- **Economic justification** - Only refactor/tidy when it makes immediate work easier

### The Development Cycle

1. **Red** - Write a failing test first (TDD)
2. **Green** - Write minimum code to pass the test
3. **Refactor/Tidy** - Clean up without changing behavior
4. **Commit** - Separate commits for features vs refactoring

### Essential Practices

#### Before Coding

- Create TODO list for complex tasks
- Ensure test coverage exists
- Identify code smells (long functions, duplication, etc.)

#### While Coding

- **Test-First**: Write the test before the implementation
- **Small Steps**: Each change should be easily reversible
- **Run Tests Frequently**: After each small change
- **Two Hats**: Either add features OR refactor, never both

#### Refactoring Techniques

1. **Extract Function/Variable** - Improve readability
2. **Rename** - Use meaningful names
3. **Guard Clauses** - Replace nested conditionals
4. **Remove Dead Code** - Delete unused code
5. **Normalize Symmetries** - Make similar code consistent

#### TDD Strategies

1. **Fake It** - Start with hardcoded values
2. **Obvious Implementation** - When solution is clear
3. **Triangulation** - Multiple tests to find general solution

### When to Apply

- **Rule of Three**: Refactor on third duplication
- **Preparatory**: Before adding features to messy code
- **Comprehension**: As you understand code better
- **Opportunistic**: Small improvements during daily work

### Key Reminders

- One assertion per test
- Commit refactoring separately from features
- Delete redundant tests
- Focus on making code understandable to humans

Quote: "Make the change easy, then make the easy change." - Kent Beck
