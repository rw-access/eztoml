from __future__ import unicode_literals
import re

NEWLINE = "\n"
DQ_MULTI = '"""'
DQ_INLINE = '"'
SQ_MULTI = "'''"
SQ_INLINE = "'"
NAN = float("NaN")
POS_INF = float("+inf")
NEG_INF = float("-inf")
RE_FLAGS = re.DOTALL | re.UNICODE | re.MULTILINE

# from https://github.com/toml-lang/toml
#
# \b         - backspace       (U+0008)
# \t         - tab             (U+0009)
# \n         - linefeed        (U+000A)
# \f         - form feed       (U+000C)
# \r         - carriage return (U+000D)
# \"         - quote           (U+0022)
# \\         - backslash       (U+005C)
# Any Unicode character may be used except those that must be escaped:
# - quotation mark
# - backslash
# - and the control characters other than tab (U+0000 to U+0008, U+000A to U+001F, U+007F).
CONTROL_CHARS = "".join([chr(u) for u in range(0x0, 0x8 + 1)] + [chr(u) for u in range(0xA, 0x1F)] + [chr(0x7F)])

TAB = "\t"
ESCAPES = {
    "b": "\b",
    "t": TAB,
    "n": NEWLINE,
    "f": "\f",
    "r": "\r",
    '"': '"',
    "\\": "\\",
}
UNESCAPES = {v: "\\" + k for k, v in ESCAPES.items()}
