"""Easy TOML."""
from __future__ import print_function

from eztoml.encoder import Encoder
from .decoder import Decoder
from .errors import EzTomlDecodeError, EzTomlEncodeError, EzTomlError
from .tz import EzTomlTz

__version__ = "0.0.1.dev3"


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


def lint_files(args=None):
    import io
    import fnmatch
    import glob
    import os
    import sys

    from argparse import ArgumentParser

    parser = ArgumentParser("toml-lint")
    parser.add_argument("paths", metavar="file_or_directory", nargs="+")
    parser.add_argument("-r", "--recursive", action="store_true")
    parser.add_argument("--sort-keys", dest="sort_keys", action="store_true")
    parser.add_argument("--preserve-style", dest="preserve_style", action="store_true")
    parsed = parser.parse_args(args)

    matches = []

    for path in parsed.paths:
        if os.path.isfile(path):
            matches.append(path)
        elif os.path.isdir(path):
            if parsed.recursive:
                for root, _, files in os.walk(path):
                    for filename in fnmatch.filter(files, '*.toml'):
                        matches.append(os.path.join(root, filename))
            else:
                matches.extend(glob.glob(os.path.join(path, "*.toml")))

    for path in matches:
        print(path)

        try:
            with io.open(path, "rt", encoding="utf-8") as infile:
                decoded = load(infile, preserve_style=parsed.preserve_style)

            # load to an intermediate variable, so that we don't wipe out the file
            # if there's an error after the handle is opened
            encoded = dumps(decoded, sort_keys=parsed.sort_keys, preserve_style=parsed.preserve_style)

            with io.open(path, "wt", encoding="utf-8") as outfile:
                outfile.write(encoded)

        except EzTomlError as exc:
            print(exc, file=sys.stderr)
