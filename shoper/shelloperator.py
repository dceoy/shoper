#!/usr/bin/env python
"""
Simple shell operator module for Python.
https://github.com/dceoy/shoper
"""

import logging
import os
import shutil
import subprocess  # nosec B404
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from pprint import pformat
from typing import Any, Callable, Dict, List, Optional, Union


@dataclass
class ShellOperator(object):
    """Simple shell operator."""
    log_txt: Optional[Union[str, Path]] = None
    quiet: bool = False
    clear_log_txt: bool = False
    logger: logging.Logger = logging.getLogger(__name__)
    print_command: bool = True
    executable: str = '/bin/bash'

    def __post_init__(self) -> None:
        self.__log_txt: Optional[Path] = (
            Path(self.log_txt) if isinstance(self.log_txt, str)
            else self.log_txt
        )
        self.__open_proc_list: List[Dict[str, Any]] = list()
        if self.clear_log_txt and self.__log_txt:
            self._remove_files_or_dirs(self.__log_txt)

    def _remove_files_or_dirs(self, paths: Any) -> None:
        for p in self._args2pathlist(paths):
            if p.is_dir():
                shutil.rmtree(str(p))
                self.logger.warning(f'directory removed: {p}')
            elif p.exists():
                os.remove(str(p))
                self.logger.warning(f'file removed: {p}')

    def run(
        self, args: Union[str, List[str], Path, List[Path]],
        input_files_or_dirs:
        Optional[Union[str, Path, List[Union[str, Path]]]] = None,
        output_files_or_dirs:
        Optional[Union[str, Path, List[Union[str, Path]]]] = None,
        output_validator: Optional[Callable[[str], bool]] = None,
        cwd: Optional[Union[str, Path]] = None, prompt: Optional[str] = None,
        asynchronous: bool = False,
        remove_if_failed: bool = True, remove_previous: bool = False,
        skip_if_exist: bool = True, **popen_kwargs
    ) -> None:
        self.logger.debug(f'input_files_or_dirs: {input_files_or_dirs}')
        input_found = {
            str(p): p.exists()
            for p in self._args2pathlist(input_files_or_dirs)
        }
        self.logger.debug(f'input_found: {input_found}')
        self.logger.debug(f'output_files_or_dirs: {output_files_or_dirs}')
        output_found = {
            str(p): p.exists()
            for p in self._args2pathlist(output_files_or_dirs)
        }
        self.logger.debug(f'output_found: {output_found}')
        if input_files_or_dirs and not all(input_found.values()):
            raise FileNotFoundError(
                'input not found: '
                + ', '.join([p for p, b in input_found.items() if not b])
            )
        elif (output_files_or_dirs and all(output_found.values())
              and skip_if_exist):
            self.logger.debug(f'args skipped: {args}')
        else:
            if remove_previous:
                self._remove_files_or_dirs(output_files_or_dirs)
            common_kwargs = {
                'prompt': (prompt or '[{}] $ '.format(cwd or os.getcwd())),
                'cwd': (str(cwd) if cwd else None), **popen_kwargs
            }
            if asynchronous:
                self.__open_proc_list.append({
                    'output_files_or_dirs': output_files_or_dirs,
                    'output_validator': output_validator,
                    'remove_if_failed': remove_if_failed,
                    'procs': [
                        self._popen(arg=a, **common_kwargs)
                        for a in self._args2list(args)
                    ]
                })
            else:
                procs = list()
                for a in self._args2list(args):
                    try:
                        proc = self._shell_c(arg=a, **common_kwargs)
                    except subprocess.SubprocessError as e:
                        if output_files_or_dirs and remove_if_failed:
                            self._remove_files_or_dirs(output_files_or_dirs)
                        raise e
                    else:
                        procs.append(proc)
                self._validate_results(
                    procs=procs, output_files_or_dirs=output_files_or_dirs,
                    output_validator=output_validator,
                    remove_if_failed=remove_if_failed
                )

    def wait(self) -> None:
        if self.__open_proc_list:
            for d in self.__open_proc_list:
                for p in d['procs']:
                    p.wait()
                    [f.close() for f in [p.stdout, p.stderr] if f]
                self._validate_results(
                    procs=d['procs'],
                    output_files_or_dirs=d['output_files_or_dirs'],
                    output_validator=d['output_validator'],
                    remove_if_failed=d['remove_if_failed']
                )
            self.__open_proc_list = list()
        else:
            self.logger.debug('There is no process.')

    def _args2pathlist(self, args: Any) -> List[Path]:
        return [Path(str(a)) for a in self._args2list(args=args)]

    @staticmethod
    def _args2list(args: Any) -> List[Any]:
        if isinstance(args, (str, Path)):
            return [args]
        elif isinstance(args, list):
            return args
        elif args is None:
            return list()
        else:
            return list(args)

    def _popen(
        self, arg: str, prompt: str, cwd: Optional[str] = None, **popen_kwargs
    ) -> subprocess.Popen:
        self.logger.debug(f'{self.executable} <- `{arg}`')
        command_line = prompt + arg
        self._print_line(command_line, stdout=self.print_command)
        if self.__log_txt:
            if Path(self.__log_txt).exists():
                with open(self.__log_txt, 'a') as f:
                    f.write(os.linesep + command_line + os.linesep)
            else:
                with open(self.__log_txt, 'w') as f:
                    f.write(command_line + os.linesep)
            fo = open(self.__log_txt, 'a')
        else:
            fo = open('/dev/null', 'w')
        return subprocess.Popen(
            args=arg, executable=self.executable, stdout=fo, stderr=fo,
            shell=True, cwd=cwd, **popen_kwargs
        )

    def _shell_c(
        self, arg: str, prompt: str, cwd: Optional[str] = None, **popen_kwargs
    ) -> subprocess.Popen:
        self.logger.debug(f'{self.executable} <- `{arg}`')
        command_line = prompt + arg
        self._print_line(command_line, stdout=self.print_command)
        if self.__log_txt:
            if Path(self.__log_txt).exists():
                with open(self.__log_txt, 'a') as f:
                    f.write(os.linesep + command_line + os.linesep)
            else:
                with open(self.__log_txt, 'w') as f:
                    f.write(command_line + os.linesep)
            fw = open(self.__log_txt, 'a')
        elif self.quiet:
            fw = open('/dev/null', 'w')
        else:
            fw = None
        if self.__log_txt and not self.quiet:
            fr = open(self.__log_txt, 'r')
            fr.read()
        else:
            fr = None
        p = subprocess.Popen(
            args=arg, executable=self.executable, stdout=fw, stderr=fw,
            shell=True, cwd=cwd, **popen_kwargs
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
        self.logger.info(strings)
        if stdout:
            print(strings, flush=True)

    def _validate_results(
        self, procs: List[subprocess.Popen],
        output_files_or_dirs:
        Optional[Union[str, Path, List[Union[str, Path]]]] = None,
        output_validator: Optional[Callable[[str], bool]] = None,
        remove_if_failed: bool = True
    ) -> None:
        p_failed = [vars(p) for p in procs if p.returncode != 0]
        if p_failed:
            if output_files_or_dirs and remove_if_failed:
                self._remove_files_or_dirs(output_files_or_dirs)
            raise subprocess.SubprocessError(
                'Commands returned non-zero exit statuses:' + os.linesep +
                pformat(p_failed)
            )
        elif output_files_or_dirs:
            self._validate_outputs(
                files_or_dirs=output_files_or_dirs, func=output_validator,
                remove_if_failed=remove_if_failed
            )

    def _validate_outputs(
        self, files_or_dirs: Union[str, Path, List[Union[str, Path]]],
        func: Optional[Callable[[str], bool]] = None,
        remove_if_failed: bool = True
    ) -> None:
        f_all = {str(p) for p in self._args2list(files_or_dirs)}
        f_found = {p for p in f_all if Path(p).exists()}
        f_not_found = f_all.difference(f_found)
        if f_not_found:
            if remove_if_failed and f_found:
                self._remove_files_or_dirs(f_found)
            raise FileNotFoundError(f'output not found: {f_not_found}')
        elif func:
            f_validated = {p for p in f_found if func(p)}
            f_not_validated = set(f_found).difference(f_validated)
            if f_not_validated:
                if remove_if_failed:
                    self._remove_files_or_dirs(f_found)
                raise RuntimeError(
                    f'output not validated with {func}: {f_not_validated}'
                )
            else:
                self.logger.debug(
                    f'output validated with {func}: {f_validated}'
                )
        else:
            self.logger.debug(f'output validated: {f_found}')
