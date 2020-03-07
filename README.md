shoper
======

Simple shell operator module for Python

[![wercker status](https://app.wercker.com/status/276fcd7ab51e9ef282981a6f38fd2020/s/master "wercker status")](https://app.wercker.com/project/byKey/276fcd7ab51e9ef282981a6f38fd2020)

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
