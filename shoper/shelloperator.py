#!/usr/bin/env python
"""
Simple shell operator module for Python.
https://github.com/dceoy/shoper
"""

import logging
import os
import subprocess
import sys
import time
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
        self.__open_proc_list = []
        if clear_log_txt:
            self._remove_existing_files(log_txt)

    def _remove_existing_files(self, paths):
        for p in self._args2list(paths):
            if os.path.exists(p):
                os.remove(p)
                self.__logger.debug('file removed: {}'.format(p))

    def run(self, args, input_files=None, output_files=None,
            output_validator=None, cwd=None, prompt=None, in_background=False,
            remove_if_failed=True, remove_previous=False, skip_if_exist=True):
        self.__logger.debug('input_files: {}'.format(input_files))
        input_found = {
            p: os.path.exists(p) for p in self._args2list(input_files)
        }
        self.__logger.debug('input_found: {}'.format(input_found))
        self.__logger.debug('output_files: {}'.format(output_files))
        output_found = {
            p: os.path.exists(p) for p in self._args2list(output_files)
        }
        self.__logger.debug('output_found: {}'.format(output_found))
        if input_files and not all(input_found.values()):
            raise FileNotFoundError(
                'input not found: {}'.format(
                    ', '.join([p for p, s in input_found.items() if not s])
                )
            )
        elif output_files and all(output_found.values()) and skip_if_exist:
            self.__logger.debug('skipped args: {}'.format(args))
        else:
            if remove_previous:
                self._remove_existing_files(output_files)
            pp = prompt or '[{}] $ '.format(cwd or os.getcwd())
            if in_background:
                self.__open_proc_list.append({
                    'output_files': output_files,
                    'output_validator': output_validator,
                    'remove_if_failed': remove_if_failed,
                    'procs': [
                        self._popen(arg=a, prompt=pp, cwd=cwd)
                        for a in self._args2list(args)
                    ]
                })
            else:
                try:
                    procs = [
                        self._shell_c(arg=a, prompt=pp, cwd=cwd)
                        for a in self._args2list(args)
                    ]
                except subprocess.CalledProcessError as e:
                    if output_files and remove_if_failed:
                        self._remove_existing_files(output_files)
                    raise e
                else:
                    self._validate_results(
                        procs=procs, output_files=output_files,
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
                    procs=d['procs'], output_files=d['output_files'],
                    output_validator=d['output_validator'],
                    remove_if_failed=d['remove_if_failed']
                )
            self.__open_proc_list = []
        else:
            self.__logger.debug('No backgroud process.')

    @staticmethod
    def _args2list(args):
        if isinstance(args, list):
            return args
        elif any([isinstance(args, c) for c in [tuple, set, dict]]):
            return list(args)
        elif args is None:
            return []
        else:
            return [args]

    def _popen(self, arg, prompt, cwd=None):
        self.__logger.debug('{0} <= {1}'.format(self.__executable, arg))
        command_line = prompt + arg
        self._print_line(command_line, stdout=self.__print_command)
        if self.__log_txt:
            if os.path.exists(self.__log_txt):
                with open(self.__log_txt, 'a') as f:
                    f.write(os.linesep + command_line + os.linesep)
            else:
                with open(self.__log_txt, 'w') as f:
                    f.write(command_line + os.linesep)
            fo = open(self.__log_txt, 'a')
        else:
            fo = open('/dev/null', 'w')
        return subprocess.Popen(
            arg, executable=self.__executable, stdout=fo, stderr=fo,
            shell=True, cwd=cwd
        )

    def _shell_c(self, arg, prompt, cwd=None):
        self.__logger.debug('{0} <= {1}'.format(self.__executable, arg))
        command_line = prompt + arg
        self._print_line(command_line, stdout=self.__print_command)
        if self.__log_txt:
            if os.path.exists(self.__log_txt):
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
            arg, executable=self.__executable, stdout=fw, stderr=fw,
            shell=True, cwd=cwd
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

    def _validate_results(self, procs, output_files=None,
                          output_validator=None, remove_if_failed=True):
        p_failed = [vars(p) for p in procs if p.returncode != 0]
        if p_failed:
            raise subprocess.SubprocessError(
                'Commands returned non-zero exit statuses:' + os.linesep +
                pformat(p_failed)
            )
        elif output_files:
            self._validate_outputs(
                files=output_files, func=output_validator,
                remove_if_failed=remove_if_failed
            )

    def _validate_outputs(self, files, func=None, remove_if_failed=True):
        f_all = self._args2list(files)
        f_found = {p for p in f_all if os.path.exists(p)}
        f_not_found = set(f_all).difference(f_found)
        if f_not_found:
            if remove_if_failed and f_found:
                self._remove_existing_files(f_found)
            raise FileNotFoundError(
                'output not found: {}'.format(f_not_found)
            )
        elif func:
            f_validated = {p for p in f_found if func(p)}
            f_not_validated = set(f_found).difference(f_validated)
            if f_not_validated:
                if remove_if_failed:
                    self._remove_existing_files(f_found)
                raise RuntimeError(
                    'output not validated with {0}: {1}'.format(
                        func, f_not_validated
                    )
                )
            else:
                self.__logger.debug(
                    'output validated with {0}: {1}'.format(
                        func, f_validated
                    )
                )
        else:
            self.__logger.debug('output validated: {}'.format(f_found))
