#!/usr/bin/env python
# pyright: reportArgumentType=false
"""Simple shell operator module for Python.

https://github.com/dceoy/shoper
"""

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
    """Simple shell operator."""

    log_txt: Optional[Union[str, Path]] = None
    quiet: bool = False
    clear_log_txt: bool = False
    logger: logging.Logger = logger
    print_command: bool = True
    executable: str = "/bin/bash"

    def __post_init__(self) -> None:
        """Initialize."""
        self.__log_txt: Optional[Path] = (
            Path(self.log_txt) if isinstance(self.log_txt, str) else self.log_txt
        )
        self.__open_proc_list: list[dict[str, Any]] = []
        if self.clear_log_txt and self.__log_txt:
            self._remove_files_or_dirs(self.__log_txt)

    def _remove_files_or_dirs(self, paths: Any) -> None:
        """Remove files or directories.

        Args:
            paths: Files or directories.
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
        **popen_kwargs: Any,
    ) -> None:
        """Run shell commands.

        Args:
            args: Command line arguments.
            input_files_or_dirs: Input files or directories.
            output_files_or_dirs: Output files or directories.
            output_validator: Output validator.
            cwd: Current working directory.
            prompt: Prompt string.
            asynchronous: Run commands asynchronously.
            remove_if_failed: Remove output files or directories if failed.
            remove_previous: Remove previous output files or directories.
            skip_if_exist: Skip if output files or directories exist.
            popen_kwargs: Keyword arguments for subprocess.Popen.

        Raises:
            FileNotFoundError: If input files or directories are not found.
            subprocess.SubprocessError: If commands return non-zero exit statuses.
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
                + ", ".join([p for p, b in input_found.items() if not b])
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
        """Wait for all processes to finish."""
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

    def _args2pathlist(self, args: Any) -> list[Path]:
        """Convert arguments to a list of Path objects.

        Args:
            args: Arguments.

        Returns:
            list: List of Path objects.
        """
        return [Path(str(a)) for a in self._args2list(args=args)]

    @staticmethod
    def _args2list(args: Any) -> list[Any]:
        """Convert arguments to a list.

        Args:
            args: Arguments.

        Returns:
            list: List of arguments.
        """
        if isinstance(args, (str, Path)):
            return [args]
        elif isinstance(args, list):
            return args
        elif args is None:
            return []
        else:
            return list(args)

    def _popen(
        self, arg: str, prompt: str, cwd: Optional[str] = None, **popen_kwargs: Any
    ) -> subprocess.Popen[Any]:
        """Run a command asynchronously.

        Args:
            arg: Command line argument.
            prompt: Prompt string.
            cwd: Current working directory.
            popen_kwargs: Keyword arguments for subprocess.Popen:open.

        Returns:
            subprocess.Popen: Process.
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
            fo = Path("/dev/null").open(mode="w", encoding="utf-8")     # noqa: SIM115
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
        self, arg: str, prompt: str, cwd: Optional[str] = None, **popen_kwargs: Any
    ) -> subprocess.Popen[Any]:
        """Run a command synchronously.

        Args:
            arg: Command line argument.
            prompt: Prompt string.
            cwd: Current working directory.
            popen_kwargs: Keyword arguments for subprocess.Popen.

        Returns:
            subprocess.Popen: Process.
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
            fw = Path("/dev/null").open(mode="w", encoding="utf-8")     # noqa: SIM115
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
        """Print a line.

        Args:
            strings: Strings to print.
            stdout: Print to stdout.
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
        """Validate results.

        Args:
            procs: Processes.
            output_files_or_dirs: Output files or directories.
            output_validator: Output validator.
            remove_if_failed: Remove output files or directories if failed.

        Raises:
            subprocess.SubprocessError: If commands return non-zero exit statuses.
        """
        p_failed = [vars(p) for p in procs if p.returncode != 0]
        if p_failed:
            if output_files_or_dirs and remove_if_failed:
                self._remove_files_or_dirs(output_files_or_dirs)
            raise subprocess.SubprocessError(
                "Commands returned non-zero exit statuses:"
                + os.linesep
                + pformat(p_failed)
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
        """Validate output files or directories.

        Args:
            files_or_dirs: Output files or directories.
            func: Output validator.
            remove_if_failed: Remove output files or directories if failed.

        Raises:
            FileNotFoundError: If output files or directories are not found.
            RuntimeError: If output files or directories are not validated.
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
