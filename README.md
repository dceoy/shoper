# Shoper

A robust Python module for executing shell commands with advanced features including input/output file tracking, asynchronous execution, logging, and validation.

[![Test](https://github.com/dceoy/shoper/actions/workflows/test.yml/badge.svg)](https://github.com/dceoy/shoper/actions/workflows/test.yml)
[![Upload Python Package](https://github.com/dceoy/shoper/actions/workflows/python-package-release-on-pypi-and-github.yml/badge.svg)](https://github.com/dceoy/shoper/actions/workflows/python-package-release-on-pypi-and-github.yml)
[![Python Versions](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

- **Robust command execution**: Both synchronous and asynchronous shell command execution
- **File validation**: Automatic validation of input and output files/directories
- **Comprehensive logging**: Optional command logging to file with execution history
- **Process management**: Track and manage multiple asynchronous processes
- **Error handling**: Detailed error reporting and validation
- **Flexible configuration**: Customizable shell executable, output suppression, and more
- **Zero dependencies**: No external dependencies required

## Installation

```bash
pip install -U shoper
```

## Quick Start

### Basic Usage

```python
from shoper import ShellOperator

# Simple command execution
sh = ShellOperator()
sh.run('ls -la')
```

### With Logging

```python
from shoper import ShellOperator

# Execute commands with logging
sh = ShellOperator(log_txt='commands.log', quiet=False)
sh.run('echo "Hello World"')
```

### File Validation

```python
from shoper import ShellOperator

sh = ShellOperator()

# Validate input files exist and output files are created
sh.run(
    args='sort input.txt > output.txt',
    input_files_or_dirs=['input.txt'],
    output_files_or_dirs=['output.txt']
)
```

## Advanced Examples

### Chained Commands with File Dependencies

```python
from shoper import ShellOperator

sh = ShellOperator(log_txt='workflow.log')

# Generate random numbers
sh.run(
    args=[
        'echo ${RANDOM} | tee random0.txt',
        'echo ${RANDOM} | tee random1.txt', 
        'echo ${RANDOM} | tee random2.txt'
    ],
    output_files_or_dirs=['random0.txt', 'random1.txt', 'random2.txt']
)

# Sort the generated numbers
sh.run(
    args='sort random[012].txt | tee sorted.txt',
    input_files_or_dirs=['random0.txt', 'random1.txt', 'random2.txt'],
    output_files_or_dirs='sorted.txt'
)
```

### Asynchronous Execution

```python
from shoper import ShellOperator

sh = ShellOperator()

# Start multiple long-running processes
sh.run('sleep 10 && echo "Task 1 done"', asynchronous=True)
sh.run('sleep 15 && echo "Task 2 done"', asynchronous=True)
sh.run('sleep 5 && echo "Task 3 done"', asynchronous=True)

# Wait for all processes to complete
sh.wait()
print("All tasks completed!")
```

### Custom Configuration

```python
from shoper import ShellOperator

# Advanced configuration
sh = ShellOperator(
    log_txt='detailed.log',
    quiet=True,                    # Suppress command output
    print_command=False,           # Don't print commands before execution
    executable='/bin/zsh',         # Use zsh instead of bash
    clear_log_txt=True            # Clear log file on initialization
)

sh.run('complex_command --with-args')
```

### Error Handling and Validation

```python
from shoper import ShellOperator

sh = ShellOperator()

try:
    sh.run(
        args='process_data input.csv',
        input_files_or_dirs=['input.csv'],
        output_files_or_dirs=['output.csv'],
        remove_previous_outputs=True  # Clean up before execution
    )
except Exception as e:
    print(f"Command failed: {e}")
```

## Configuration Options

The `ShellOperator` class supports the following configuration parameters:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `log_txt` | `str`, `Path` or `None` | `None` | Path to log file for command output |
| `quiet` | `bool` | `False` | Suppress command output to stdout |
| `clear_log_txt` | `bool` | `False` | Clear log file on initialization |
| `print_command` | `bool` | `True` | Print commands before execution |
| `executable` | `str` | `/bin/bash` | Shell executable to use |

## Method Reference

### `run(args, **kwargs)`

Execute shell commands with extensive configuration options.

**Parameters:**
- `args`: Command string or list of commands to execute
- `input_files_or_dirs`: Files/directories that must exist before execution
- `output_files_or_dirs`: Files/directories expected after execution
- `asynchronous`: Execute command asynchronously (default: `False`)
- `remove_previous_outputs`: Remove output files before execution
- `cwd`: Working directory for command execution
- Additional subprocess parameters supported

### `wait()`

Wait for all asynchronous processes to complete.

## Requirements

- Python 3.9 or higher
- POSIX-compatible operating system (Linux, macOS)
- No external dependencies

## Development

### Setup Development Environment

```bash
git clone https://github.com/dceoy/shoper.git
cd shoper
pip install -e .
```

### Code Quality

```bash
# Linting
ruff check .
ruff check . --fix

# Type checking  
pyright
```

### Testing

Testing is performed via GitHub Actions with package installation and basic functionality verification.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Author

Daichi Narushima ([@dceoy](https://github.com/dceoy))

## Links

- [GitHub Repository](https://github.com/dceoy/shoper)
- [PyPI Package](https://pypi.org/project/shoper/)
- [Issues](https://github.com/dceoy/shoper/issues)
