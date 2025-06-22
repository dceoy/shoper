"""Simple shell operator module for Python.

This module provides the ShellOperator class which wraps subprocess operations
with additional functionality for logging, error handling, and file management.
It supports both synchronous and asynchronous command execution with extensive
validation and configuration options.

For more information, visit: https://github.com/dceoy/shoper

Example:
    Basic usage:
        >>> from shoper.shelloperator import ShellOperator
        >>> shell_op = ShellOperator(log_txt="commands.log", quiet=True)
        >>> # shell_op.run("echo 'Hello'")
"""

# pyright: reportArgumentType=false

import logging
import os
import shutil
import subprocess  # noqa: S404
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from pprint import pformat
from typing import Any, Callable, Optional, Union

logger = logging.getLogger(__name__)


@dataclass
class ShellOperator:
    """Simple shell operator for executing shell commands with advanced features.

    This class provides a robust interface for running shell commands with support
    for input/output file validation, asynchronous execution, logging, and error
    handling. It wraps subprocess operations with additional functionality for
    better control and monitoring of command execution.

    Attributes:
        log_txt: Optional path to log file for command output and execution history.
        quiet: If True, suppresses command output to stdout.
        clear_log_txt: If True, clears the log file on initialization.
        logger: Logger instance for debug and info messages.
        print_command: If True, prints commands before execution.
        executable: Shell executable to use for command execution (default: /bin/bash).

    Example:
        Basic usage:
            >>> shell_op = ShellOperator(log_txt="commands.log", quiet=True)
            >>> # shell_op.run("echo 'Hello World'")

        Asynchronous execution:
            >>> shell_op = ShellOperator(quiet=True)
            >>> # shell_op.run("sleep 1", asynchronous=True)
            >>> # shell_op.wait()  # Wait for completion
    """

    log_txt: Optional[Union[str, Path]] = None
    quiet: bool = False
    clear_log_txt: bool = False
    logger: logging.Logger = logger
    print_command: bool = True
    executable: str = "/bin/bash"

    def __post_init__(self) -> None:
        """Initialize the ShellOperator instance after dataclass construction.

        This method is automatically called after the dataclass __init__ method.
        It performs additional setup including path normalization, process list
        initialization, and optional log file clearing.

        Side Effects:
            - Converts string log_txt to Path object if needed
            - Initializes empty process list for asynchronous operations
            - Clears log file if clear_log_txt is True and log_txt is set
        """
        self.__log_txt: Optional[Path] = (
            Path(self.log_txt) if isinstance(self.log_txt, str) else self.log_txt
        )
        self.__open_proc_list: list[dict[str, Any]] = []
        if self.clear_log_txt and self.__log_txt:
            self._remove_files_or_dirs(self.__log_txt)

    def _remove_files_or_dirs(
        self,
        paths: Union[str, Path, list[Union[str, Path]], None],
    ) -> None:
        """Remove files or directories from the filesystem.

        This method safely removes files and directories, handling both individual
        paths and collections of paths. It logs warnings for each removed item.

        Args:
            paths: Files or directories to remove. Can be a single path or a
                collection of paths (strings, Path objects, or mixed).

        Note:
            - Directories are removed recursively using shutil.rmtree
            - Files are removed using Path.unlink
            - Non-existent paths are silently ignored
            - Warnings are logged for each removed item
        """
        for p in self._args2pathlist(paths):
            if p.is_dir():
                shutil.rmtree(str(p))
                self.logger.warning("directory removed: %s", p)
            elif p.exists():
                Path(str(p)).unlink()
                self.logger.warning("file removed: %s", p)

    def run(
        self,
        args: Union[str, list[str], Path, list[Path]],
        input_files_or_dirs: Optional[Union[str, Path, list[Union[str, Path]]]] = None,
        output_files_or_dirs: Optional[Union[str, Path, list[Union[str, Path]]]] = None,
        output_validator: Optional[Callable[[str], bool]] = None,
        cwd: Optional[Union[str, Path]] = None,
        prompt: Optional[str] = None,
        asynchronous: bool = False,
        remove_if_failed: bool = True,
        remove_previous: bool = False,
        skip_if_exist: bool = True,
        **popen_kwargs: Any,  # noqa: ANN401
    ) -> None:
        """Execute shell commands with comprehensive validation and error handling.

        This is the main method for executing shell commands. It supports both
        synchronous and asynchronous execution with extensive validation of input
        and output files/directories. The method handles command chaining, output
        validation, and cleanup on failure.

        Args:
            args: Command line arguments to execute. Can be a single command string,
                list of command strings, Path object, or list of Path objects.
            input_files_or_dirs: Input files or directories that must exist before
                command execution. Commands are skipped if inputs don't exist.
            output_files_or_dirs: Expected output files or directories. Used for
                validation after command execution and cleanup on failure.
            output_validator: Optional callable that takes a file path string and
                returns True if the output is valid. Used for custom validation.
            cwd: Current working directory for command execution. Defaults to
                current directory if not specified.
            prompt: Custom prompt string for command logging. Defaults to
                "[{cwd}] $ " format.
            asynchronous: If True, runs commands asynchronously without waiting
                for completion. Use wait() method to wait for completion.
            remove_if_failed: If True, removes output files/directories when
                command execution fails or validation fails.
            remove_previous: If True, removes existing output files/directories
                before command execution.
            skip_if_exist: If True, skips command execution if all output
                files/directories already exist.
            **popen_kwargs: Additional keyword arguments passed to subprocess.Popen.

        Raises:
            FileNotFoundError: If required input files or directories are not found,
                or if expected output files are not created after command execution.
            subprocess.SubprocessError: If any command returns a non-zero exit status.

        Example:
            >>> shell_op = ShellOperator(quiet=True)
            >>> # Example: compile a C program
            >>> # shell_op.run(
            >>> #     "gcc -o program source.c",
            >>> #     input_files_or_dirs=["source.c"],
            >>> #     output_files_or_dirs=["program"],
            >>> #     remove_if_failed=True
            >>> # )

        Note:
            - Commands are executed in the order provided
            - Input validation occurs before any command execution
            - Output validation occurs after all commands complete
            - Asynchronous commands are tracked and can be waited on with wait()
        """
        self.logger.debug("input_files_or_dirs: %s", input_files_or_dirs)
        input_found = {
            str(p): p.exists() for p in self._args2pathlist(input_files_or_dirs)
        }
        self.logger.debug("input_found: %s", input_found)
        self.logger.debug("output_files_or_dirs: %s", output_files_or_dirs)
        output_found = {
            str(p): p.exists() for p in self._args2pathlist(output_files_or_dirs)
        }
        self.logger.debug("output_found: %s", output_found)
        if input_files_or_dirs and not all(input_found.values()):
            raise FileNotFoundError(
                "input not found: "
                + ", ".join([p for p, b in input_found.items() if not b]),
            )
        elif output_files_or_dirs and all(output_found.values()) and skip_if_exist:
            self.logger.debug("args skipped: %s", args)
        else:
            if remove_previous:
                self._remove_files_or_dirs(output_files_or_dirs)
            common_kwargs = {
                "prompt": (prompt or f"[{cwd or Path.cwd()}] $ "),
                "cwd": (str(cwd) if cwd else None),
                **popen_kwargs,
            }
            if asynchronous:
                self.__open_proc_list.append({
                    "output_files_or_dirs": output_files_or_dirs,
                    "output_validator": output_validator,
                    "remove_if_failed": remove_if_failed,
                    "procs": [
                        self._popen(arg=a, **common_kwargs)
                        for a in self._args2list(args)
                    ],
                })
            else:
                try:
                    procs = [
                        self._shell_c(arg=a, **common_kwargs)
                        for a in self._args2list(args)
                    ]
                except subprocess.SubprocessError:
                    if output_files_or_dirs and remove_if_failed:
                        self._remove_files_or_dirs(output_files_or_dirs)
                    raise
                self._validate_results(
                    procs=procs,
                    output_files_or_dirs=output_files_or_dirs,
                    output_validator=output_validator,
                    remove_if_failed=remove_if_failed,
                )

    def wait(self) -> None:
        """Wait for all asynchronous processes to complete and validate results.

        This method blocks until all processes started with asynchronous=True
        have completed. It then validates the results of all processes, including
        checking return codes and validating output files if specified.

        The method processes all pending asynchronous operations in the order
        they were started, ensuring proper cleanup of file handles and validation
        of outputs according to the parameters specified in the original run() calls.


        Note:
            - This method must be called after running commands with asynchronous=True
            - File handles (stdout, stderr) are properly closed after process completion
            - Output validation is performed according to original run() parameters
            - The internal process list is cleared after all processes complete

        Example:
            >>> shell_op = ShellOperator(quiet=True)
            >>> # Example: run multiple async commands
            >>> # shell_op.run("sleep 1", asynchronous=True)
            >>> # shell_op.run("sleep 1", asynchronous=True)
            >>> # shell_op.wait()  # Wait for both commands to complete
        """
        if self.__open_proc_list:
            for d in self.__open_proc_list:
                for p in d["procs"]:
                    p.wait()
                    [f.close() for f in [p.stdout, p.stderr] if f]
                self._validate_results(
                    procs=d["procs"],
                    output_files_or_dirs=d["output_files_or_dirs"],
                    output_validator=d["output_validator"],
                    remove_if_failed=d["remove_if_failed"],
                )
            self.__open_proc_list = []
        else:
            self.logger.debug("There is no process.")

    def _args2pathlist(self, args: Any) -> list[Path]:  # noqa: ANN401
        """Convert various argument types to a list of Path objects.

        This utility method normalizes different input types (strings, Path objects,
        lists, None) into a consistent list of Path objects for internal processing.

        Args:
            args: Arguments to convert. Can be:
                - str: Single file path string
                - Path: Single Path object
                - list: List of strings and/or Path objects
                - None: Returns empty list
                - Any iterable: Converted to list then processed

        Returns:
            List of Path objects corresponding to the input arguments.
            Empty list if args is None or empty.

        Example:
            >>> shell_op = ShellOperator()
            >>> paths = shell_op._args2pathlist(["file1.txt", Path("file2.txt")])
            >>> isinstance(paths[0], Path)
            True
        """
        return [Path(str(a)) for a in self._args2list(args=args)]

    @staticmethod
    def _args2list(args: Any) -> list[Any]:  # noqa: ANN401
        """Convert various argument types to a list.

        This static utility method normalizes different input types into a
        consistent list format for internal processing. It handles single
        values, existing lists, and iterables.

        Args:
            args: Arguments to convert. Can be:
                - str or Path: Single item, returned as single-item list
                - list: Returned as-is
                - None: Returns empty list
                - Any other iterable: Converted to list

        Returns:
            List containing the input arguments. Empty list if args is None.

        Example:
            >>> ShellOperator._args2list("single_command")
            ['single_command']
            >>> ShellOperator._args2list(["cmd1", "cmd2"])
            ['cmd1', 'cmd2']
            >>> ShellOperator._args2list(None)
            []
        """
        if isinstance(args, (str, Path)):
            return [args]
        elif isinstance(args, list):
            return args  # type: ignore[reportUnknownVariableType]
        elif args is None:
            return []
        else:
            return list(args)

    def _popen(
        self,
        arg: str,
        prompt: str,
        cwd: Optional[str] = None,
        **popen_kwargs: Any,  # noqa: ANN401
    ) -> subprocess.Popen[Any]:
        """Execute a command asynchronously using subprocess.Popen.

        This method starts a command in the background without waiting for it
        to complete. Output is redirected to the log file if specified, or to
        /dev/null otherwise. The command and prompt are logged and optionally
        printed to stdout.

        Args:
            arg: Command line string to execute.
            prompt: Prompt string to prepend to the command in logs and output.
            cwd: Current working directory for command execution. Uses current
                directory if not specified.
            **popen_kwargs: Additional keyword arguments passed directly to
                subprocess.Popen (e.g., env, stdin, etc.).

        Returns:
            subprocess.Popen object representing the running process.
            The caller is responsible for waiting on this process and closing
            file handles.

        Note:
            - stdout and stderr are redirected to log file or /dev/null
            - Command is executed using the configured shell (default: /bin/bash)
            - Log file is created if it doesn't exist, appended to if it does
            - Process runs in background - use wait() or process.wait() to wait

        Example:
            >>> shell_op = ShellOperator(
            ...     log_txt="commands.log", quiet=True, print_command=False
            ... )
            >>> process = shell_op._popen("echo 'async test'", "[test] $ ")
            >>> # Process is running in background
            >>> exit_code = process.wait()  # Wait for completion
            >>> exit_code
            0
        """
        self.logger.debug("%s <- `%s`", self.executable, arg)
        command_line = prompt + arg
        self._print_line(command_line, stdout=self.print_command)
        if self.__log_txt:
            if Path(self.__log_txt).exists():
                with Path(self.__log_txt).open(mode="a", encoding="utf-8") as f:
                    f.write(os.linesep + command_line + os.linesep)
            else:
                with Path(self.__log_txt).open(mode="w", encoding="utf-8") as f:
                    f.write(command_line + os.linesep)
            fo = Path(self.__log_txt).open(mode="a", encoding="utf-8")  # noqa: SIM115
        else:
            fo = Path("/dev/null").open(mode="w", encoding="utf-8")  # noqa: SIM115
        return subprocess.Popen(
            args=arg,
            executable=self.executable,
            stdout=fo,
            stderr=fo,
            shell=True,
            cwd=cwd,
            **popen_kwargs,
        )

    def _shell_c(
        self,
        arg: str,
        prompt: str,
        cwd: Optional[str] = None,
        **popen_kwargs: Any,  # noqa: ANN401
    ) -> subprocess.Popen[Any]:
        """Execute a command synchronously with real-time output handling.

        This method runs a command and waits for it to complete, providing
        real-time output streaming when logging is enabled. Output can be
        directed to a log file, suppressed entirely (quiet mode), or streamed
        to stdout with real-time updates.

        Args:
            arg: Command line string to execute.
            prompt: Prompt string to prepend to the command in logs and output.
            cwd: Current working directory for command execution.
            **popen_kwargs: Additional keyword arguments passed to subprocess.Popen.

        Returns:
            subprocess.Popen object representing the completed process.
            The process will have finished execution (returncode is set).

        Note:
            - Blocks until command completion
            - Provides real-time output streaming when log file is used
            - Handles output redirection based on quiet and log_txt settings
            - Command is executed using the configured shell executable
            - File handles are properly closed after completion

        Behavior:
            - If log_txt is set and quiet=False: Output streamed to both log and stdout
            - If log_txt is set and quiet=True: Output only to log file
            - If quiet=True and no log_txt: Output suppressed (/dev/null)
            - Otherwise: Output goes to stdout/stderr directly

        Example:
            >>> shell_op = ShellOperator(
            ...     log_txt="commands.log", quiet=True, print_command=False
            ... )
            >>> process = shell_op._shell_c("echo 'test'", "[test] $ ")
            >>> print(f"Command completed with code: {process.returncode}")
            Command completed with code: 0
        """
        self.logger.debug("%s <- `%s`", self.executable, arg)
        command_line = prompt + arg
        self._print_line(command_line, stdout=self.print_command)
        if self.__log_txt:
            if Path(self.__log_txt).exists():
                with Path(self.__log_txt).open(mode="a", encoding="utf-8") as f:
                    f.write(os.linesep + command_line + os.linesep)
            else:
                with Path(self.__log_txt).open(mode="w", encoding="utf-8") as f:
                    f.write(command_line + os.linesep)
            fw = Path(self.__log_txt).open(mode="a", encoding="utf-8")  # noqa: SIM115
        elif self.quiet:
            fw = Path("/dev/null").open(mode="w", encoding="utf-8")  # noqa: SIM115
        else:
            fw = None
        if self.__log_txt and not self.quiet:
            fr = Path(self.__log_txt).open(mode="r", encoding="utf-8")  # noqa: SIM115
            fr.read()
        else:
            fr = None
        p = subprocess.Popen(
            args=arg,
            executable=self.executable,
            stdout=fw,
            stderr=fw,
            shell=True,
            cwd=cwd,
            **popen_kwargs,
        )
        if fr:
            while p.poll() is None:
                sys.stdout.write(fr.read())
                sys.stdout.flush()
                time.sleep(0.1)
            sys.stdout.write(fr.read())
            sys.stdout.flush()
            fr.close()
        else:
            p.wait()
        if fw:
            fw.close()
        return p

    def _print_line(self, strings: str, stdout: bool = True) -> None:
        """Print a line to logger and optionally to stdout.

        This utility method provides consistent logging and output handling
        throughout the class. It always logs at INFO level and optionally
        prints to stdout with immediate flushing.

        Args:
            strings: String content to log and print.
            stdout: If True, prints to stdout in addition to logging.
                If False, only logs the content.

        Note:
            - Always logs at INFO level using the configured logger
            - stdout output is flushed immediately for real-time display
            - Typically used for command execution logging and prompts

        Example:
            >>> shell_op = ShellOperator(quiet=True)
            >>> shell_op._print_line("Executing command...", stdout=False)
        """
        self.logger.info(strings)
        if stdout:
            print(strings, flush=True)  # noqa: T201

    def _validate_results(
        self,
        procs: list[subprocess.Popen[Any]],
        output_files_or_dirs: Optional[Union[str, Path, list[Union[str, Path]]]] = None,
        output_validator: Optional[Callable[[str], bool]] = None,
        remove_if_failed: bool = True,
    ) -> None:
        """Validate command execution results and output files.

        This method performs comprehensive validation of command execution results,
        including checking process return codes and validating output files or
        directories. It handles cleanup of failed outputs when requested.

        Args:
            procs: List of completed subprocess.Popen objects to validate.
                All processes should have finished execution (returncode set).
            output_files_or_dirs: Expected output files or directories to validate.
                Can be None if no output validation is required.
            output_validator: Optional callable that takes a file path string and
                returns True if the output is valid. Used for custom validation
                beyond existence checking.
            remove_if_failed: If True, removes output files/directories when
                validation fails or processes have non-zero return codes.

        Raises:
            subprocess.SubprocessError: If any process has a non-zero return code.
                The exception message includes details of all failed processes.

        Note:
            - Process validation occurs before output validation
            - Failed outputs are cleaned up if remove_if_failed=True
            - Custom validators receive file path strings, not Path objects
            - All processes in the list are checked, not just the first failure

        Example:
            >>> shell_op = ShellOperator()
            >>> # Example: validate command results
            >>> # shell_op._validate_results(
            >>> #     procs=[completed_process],
            >>> #     output_files_or_dirs=["output.txt"],
            >>> #     output_validator=lambda p: Path(p).stat().st_size > 0
            >>> # )
        """
        p_failed = [vars(p) for p in procs if p.returncode != 0]
        if p_failed:
            if output_files_or_dirs and remove_if_failed:
                self._remove_files_or_dirs(output_files_or_dirs)
            raise subprocess.SubprocessError(
                "Commands returned non-zero exit statuses:"
                + os.linesep
                + pformat(p_failed),
            )
        elif output_files_or_dirs:
            self._validate_outputs(
                files_or_dirs=output_files_or_dirs,
                func=output_validator,
                remove_if_failed=remove_if_failed,
            )

    def _validate_outputs(
        self,
        files_or_dirs: Union[str, Path, list[Union[str, Path]]],
        func: Optional[Callable[[str], bool]] = None,
        remove_if_failed: bool = True,
    ) -> None:
        """Validate the existence and quality of output files or directories.

        This method checks that all expected output files or directories exist
        and optionally validates their content or properties using a custom
        validator function. It handles cleanup of invalid outputs when requested.

        Args:
            files_or_dirs: Expected output files or directories to validate.
                Can be a single path (str/Path) or list of paths.
            func: Optional validation function that takes a file path string
                and returns True if the output is valid. Called for each
                existing output file/directory.
            remove_if_failed: If True, removes all output files/directories
                if any validation step fails.

        Raises:
            FileNotFoundError: If any expected output file or directory is
                not found after command execution.
            RuntimeError: If the custom validator function returns False
                for any output file or directory.


        Note:
            - Validator function receives file path as string, not Path object
            - If remove_if_failed=True, ALL outputs are removed on any failure
            - Missing outputs are checked before custom validation
            - Successful validation is logged at DEBUG level

        Example:
            >>> shell_op = ShellOperator()
            >>> # Example: validate output files
            >>> # shell_op._validate_outputs(
            >>> #     files_or_dirs=["output1.txt", "output2.txt"],
            >>> #     func=lambda p: Path(p).stat().st_size > 0,
            >>> #     remove_if_failed=True
            >>> # )
        """
        f_all = {str(p) for p in self._args2list(files_or_dirs)}
        f_found = {p for p in f_all if Path(p).exists()}
        f_not_found = f_all.difference(f_found)
        if f_not_found:
            if remove_if_failed and f_found:
                self._remove_files_or_dirs(f_found)
            error_message = f"output not found: {f_not_found}"
            raise FileNotFoundError(error_message)
        elif func:
            f_validated = {p for p in f_found if func(p)}
            f_not_validated = set(f_found).difference(f_validated)
            if f_not_validated:
                if remove_if_failed:
                    self._remove_files_or_dirs(f_found)
                error_message = f"output not validated with {func}: {f_not_validated}"
                raise RuntimeError(error_message)
            else:
                self.logger.debug("output validated with %s: %s", func, f_validated)
        else:
            self.logger.debug("output validated: %s", f_found)
