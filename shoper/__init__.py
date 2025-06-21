"""Structural Data Extractor using LLMs (sdeul) package.

This package provides functionality for extracting structured JSON data from
unstructured text using various Language Learning Models (LLMs) including
OpenAI, Google, Groq, Amazon Bedrock, Ollama, and local models via llama.cpp.

The package includes:
- CLI interface for data extraction and JSON validation
- REST API for data extraction and validation
- Support for multiple LLM providers
- JSON Schema validation
- Text extraction from various sources
"""

from importlib.metadata import version

__version__ = version(__package__) if __package__ else None

__all__ = ["__version__"]
