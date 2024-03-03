shoper
======

Simple shell operator module for Python

[![Test](https://github.com/dceoy/shoper/actions/workflows/test.yml/badge.svg)](https://github.com/dceoy/shoper/actions/workflows/test.yml)
[![Upload Python Package](https://github.com/dceoy/shoper/actions/workflows/python-package-release-on-pypi-and-github.yml/badge.svg)](https://github.com/dceoy/shoper/actions/workflows/python-package-release-on-pypi-and-github.yml)

Installation
------------

```sh
$ pip install -U shoper
```

Example
-------

List directory contents with `ls`.

```py
from shoper.shelloperator import ShellOperator

sh = ShellOperator()
sh.run('ls -l')
```

Write and sort random numbers.

```py
from shoper.shelloperator import ShellOperator

sh = ShellOperator()
sh.run(
    args=[
        'echo ${RANDOM} | tee random0.txt',
        'echo ${RANDOM} | tee random1.txt',
        'echo ${RANDOM} | tee random2.txt'
    ],
    output_files_or_dirs=['random0.txt', 'random1.txt', 'random2.txt']
)
sh.run(
    args='sort random[012].txt | tee sorted.txt',
    input_files_or_dirs=['random0.txt', 'random1.txt', 'random2.txt'],
    output_files_or_dirs='sorted.txt'
)
```
