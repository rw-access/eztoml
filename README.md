# eztoml

[![PyPI](https://img.shields.io/pypi/v/eztoml.svg)](https://pypi.python.org/pypi/eztoml)
![Python package](https://github.com/rw-access/eztoml/workflows/Python%20package/badge.svg)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Python drop-in replacement for parsing [TOML](https://github.com/toml-lang/toml) with pretty printing.

Similar to `json`, use `loads` to read from a string and `load` to read from a file-like object.
```python
import eztoml as toml

toml.loads(r"""
repo = "eztoml"

[meta]
version = "0.0.1.dev0"
dependencies = []
""")

# {'repo': 'eztoml', 'meta': {'version': '0.0.1.dev0', 'dependencies': []}}
```

Similar to `json`, use `dumps` to output a string and `dump` to read from a file-like object.
```python
import eztoml as toml

data = {'repo': 'eztoml', 'meta': {'version': '0.0.1.dev0', 'dependencies': []}}

print(toml.dumps(data))

# repo = "eztoml"
#
# [meta]
# version = "0.0.1.dev0"
# dependencies = []
```

`eztoml.dumps` has additional parameters for better formatting and indenting, similar to JSON:
```python
def dumps(obj, sort_keys=False, nl="\n", indent=2, wrap=120, preserve_cr=False):
  ...
```