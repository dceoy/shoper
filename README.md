shopy
=====

Simple shell operator module for Python

Example
-------

```py
sh = ShellOperator(log_txt='log.txt', executable='/bin/bash')
sh.run(
    'a=0 && echo ${a}; b=1 && echo ${b};'
    'for i in $(seq 3 20); do'
    '  c=$((${a} + ${b})) && echo ${c} && a=${b} && b=${c};'
    'done;'
)
```
