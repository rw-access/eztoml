from __future__ import unicode_literals

import re  # noqa: F401

from .errors import EzTomlDecodeError


class Source(object):
    def __init__(self, text):  # type: (str) -> None
        self.text = text
        self.size = len(self.text)
        self.pos = 0
        self.line = 0
        self.column = 0

    def copy(self):
        copied = type(self)(self.text)
        copied.pos = self.pos
        copied.line = self.line
        copied.column = self.column

    def reset(self):
        self.pos = 0
        self.line = 0
        self.column = 0

    @property
    def eof(self):
        return self.size == self.pos

    @property
    def remaining(self):
        return self.text[self.pos :]

    @property
    def remaining_line(self):
        remaining, _, _ = self.remaining.partition("\n")
        return remaining.strip()

    def peek(self, num_chars=1):
        if self.pos < self.size:
            return self.text[self.pos : self.pos + num_chars]

    def peek_match(self, regex):  # type: (re.Pattern) -> str
        matched = regex.match(self.remaining)
        if matched is not None:
            return self.text[self.pos + matched.start() : self.pos + matched.end()]

    def take_match(self, regex):  # type: (re.Pattern) -> str
        matched = regex.match(self.remaining)
        assert matched is not None
        return self.take(matched.end() - matched.start())

    def advance_line(self):
        try:
            self.pos = self.text.index("\n", self.pos) + 1
            self.line += 1
            self.column = 0
        except ValueError:
            self.column += self.size - self.pos
            self.pos = self.size

    def search(self, substring):
        try:
            return self.text.index(substring, self.pos) - self.pos
        except ValueError:
            return None

    def has_prefix(self, prefix):
        return self.peek(len(prefix)) == prefix

    def remove_prefix(self, prefix):
        if self.text[self.pos : self.pos + len(prefix)] == prefix:
            self.take(len(prefix))
            return True
        return False

    def take(self, num_chars=1):
        taken = self.text[self.pos : self.pos + num_chars]
        size = len(taken)
        assert size == num_chars
        self.pos += size
        num_lines = taken.count("\n")
        if num_lines == 0:
            self.column += size
        else:
            self.line += num_lines
            self.column = (size - 1) - taken.rindex("\n")

        return taken

    def eat_inline_ws(self):
        while not self.eof and self.text[self.pos] in " \t":
            self.pos += 1
            self.column += 1

    def eat_ws(self, must_advance=False):
        start_line = self.line

        while not self.eof:
            char = self.text[self.pos]
            if char == "#":
                self.advance_line()
                continue
            elif char == "\n":
                self.line += 1
                self.column = 0
            elif self.text[self.pos] in " \t\r":
                self.column += 1
            else:
                break

            self.pos += 1

        # if the line hasn't advanced, then we have too much content on a single line
        if must_advance and self.line == start_line and not self.eof:
            raise EzTomlDecodeError("Unexpected content in line: {}".format(self.remaining_line))
