#!/usr/bin/env python
"""
Simple shell operator module for Python.
https://github.com/dceoy/shoper
"""

import logging
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from pprint import pformat


class ShellOperator(object):
    """Simple shell operator."""

    def __init__(self, log_txt=None, quiet=False, clear_log_txt=False,
                 logger=None, print_command=True, executable='/bin/bash'):
        self.__logger = logger or logging.getLogger(__name__)
        self.__executable = executable
        self.__log_txt = log_txt
        self.__quiet = quiet
        self.__print_command = print_command
        self.__open_proc_list = list()
        if clear_log_txt:
            self._remove_files_or_dirs(log_txt)

    def _remove_files_or_dirs(self, paths):
        for p in self._args2list(paths):
            if Path(p).is_dir():
                shutil.rmtree(p)
                self.__logger.debug(f'directory removed: {p}')
            elif Path(p).exists():
                os.remove(p)
                self.__logger.debug(f'file removed: {p}')

    def run(self, args, input_files_or_dirs=None, output_files_or_dirs=None,
            output_validator=None, cwd=None, prompt=None, asynchronous=False,
            remove_if_failed=True, remove_previous=False, skip_if_exist=True,
            **popen_kwargs):
        self.__logger.debug(f'input_files_or_dirs: {input_files_or_dirs}')
        input_found = {
            p: Path(p).exists() for p in self._args2list(input_files_or_dirs)
        }
        self.__logger.debug(f'input_found: {input_found}')
        self.__logger.debug(f'output_files_or_dirs: {output_files_or_dirs}')
        output_found = {
            p: Path(p).exists() for p in self._args2list(output_files_or_dirs)
        }
        self.__logger.debug(f'output_found: {output_found}')
        if input_files_or_dirs and not all(input_found.values()):
            raise FileNotFoundError(
                'input not found: '
                + ', '.join([p for p, s in input_found.items() if not s])
            )
        elif (output_files_or_dirs and all(output_found.values())
              and skip_if_exist):
            self.__logger.debug(f'args skipped: {args}')
        else:
            if remove_previous:
                self._remove_files_or_dirs(output_files_or_dirs)
            pp = prompt or '[{}] $ '.format(cwd or os.getcwd())
            if asynchronous:
                self.__open_proc_list.append({
                    'output_files_or_dirs': output_files_or_dirs,
                    'output_validator': output_validator,
                    'remove_if_failed': remove_if_failed,
                    'procs': [
                        self._popen(arg=a, prompt=pp, cwd=cwd, **popen_kwargs)
                        for a in self._args2list(args)
                    ]
                })
            else:
                procs = list()
                for a in self._args2list(args):
                    try:
                        proc = self._shell_c(
                            arg=a, prompt=pp, cwd=cwd, **popen_kwargs
                        )
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

    def wait(self):
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
            self.__logger.debug('There is no process.')

    @staticmethod
    def _args2list(args):
        if isinstance(args, str):
            return [args]
        elif isinstance(args, list):
            return args
        elif args is None:
            return list()
        else:
            return list(args)

    def _popen(self, arg, prompt, cwd=None, **popen_kwargs):
        self.__logger.debug(f'{self.__executable} <- `{arg}`')
        command_line = prompt + arg
        self._print_line(command_line, stdout=self.__print_command)
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
            args=arg, executable=self.__executable, stdout=fo, stderr=fo,
            shell=True, cwd=cwd, **popen_kwargs
        )

    def _shell_c(self, arg, prompt, cwd=None, **popen_kwargs):
        self.__logger.debug(f'{self.__executable} <- `{arg}`')
        command_line = prompt + arg
        self._print_line(command_line, stdout=self.__print_command)
        if self.__log_txt:
            if Path(self.__log_txt).exists():
                with open(self.__log_txt, 'a') as f:
                    f.write(os.linesep + command_line + os.linesep)
            else:
                with open(self.__log_txt, 'w') as f:
                    f.write(command_line + os.linesep)
            fw = open(self.__log_txt, 'a')
        elif self.__quiet:
            fw = open('/dev/null', 'w')
        else:
            fw = None
        if self.__log_txt and not self.__quiet:
            fr = open(self.__log_txt, 'r')
            fr.read()
        else:
            fr = None
        p = subprocess.Popen(
            args=arg, executable=self.__executable, stdout=fw, stderr=fw,
            shell=True, cwd=cwd, **popen_kwargs
        )
        if fr:
            while p.poll() is None:
                sys.stdout.write(fr.read())
                sys.stdout.flush()
                time.sleep(0.1)
            sys.stdout.write(fr.read())
            sys.stdout.flush()
        else:
            p.wait()
        [f.close() for f in [fw, fr] if f]
        return p

    def _print_line(self, strings, stdout=True):
        if stdout:
            print(strings, flush=True)
        else:
            self.__logger.info(strings)

    def _validate_results(self, procs, output_files_or_dirs=None,
                          output_validator=None, remove_if_failed=True):
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

    def _validate_outputs(self, files_or_dirs, func=None,
                          remove_if_failed=True):
        f_all = self._args2list(files_or_dirs)
        f_found = {p for p in f_all if Path(p).exists()}
        f_not_found = set(f_all).difference(f_found)
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
                self.__logger.debug(
                    f'output validated with {func}: {f_validated}'
                )
        else:
            self.__logger.debug(f'output validated: {f_found}')
