"""Easy TOML."""
from eztoml.encoder import Encoder
from .decoder import Decoder
from .errors import EzTomlDecodeError, EzTomlEncodeError
from .tz import EzTomlTz

__version__ = "0.0.1.dev0"


def loads(src, **kwargs):
    return Decoder(**kwargs).decode(src)


def load(f, **kwargs):
    return loads(f.read(), **kwargs)


def dumps(document, **kwargs):
    if not isinstance(document, dict):
        raise EzTomlEncodeError("Unable to encode non-dictionary type: {}".format(type(src)))

    return Encoder(**kwargs).encode(document)


def dump(document, fileobj, **kwargs):
    fileobj.write(dumps(document, **kwargs))
