"""Shoper: A simple shell operator module for Python.

This module provides a clean interface for executing shell commands with features
like input/output file tracking, asynchronous execution, and validation.

The main class ShellOperator wraps subprocess operations with additional
functionality for logging, error handling, and file management.

Example:
    Basic usage of ShellOperator:

    >>> from shoper import ShellOperator
    >>> shell_op = ShellOperator(log_txt="commands.log")
    >>> shell_op.run("echo 'Hello World'")

Attributes:
    __version__ (str): The version string of the package.
"""

# pyright: reportUnusedImport=false

from .shelloperator import ShellOperator  # noqa: F401

__version__ = "v1.4.3"
