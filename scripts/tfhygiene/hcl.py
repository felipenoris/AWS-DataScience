"""Reading HCL native syntax far enough to find a block and the literal text of an argument.

The reader tokenises a whole ``.tf`` file - quoted strings with their escapes and their ``${...}``
and ``%{...}`` sequences, heredocs, the three comment forms - and returns each body as its
arguments and blocks, in source order. It evaluates nothing: an argument's value stays a list of
tokens, so the one question it answers about a value is whether it is a single string, and if so
which parts of it are literal text.

Text it cannot tokenise raises :class:`HclError` with the line: a reader that skipped what it
could not parse would report the same "nothing found" over a clean file and an unread one
(Lesson 13).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# A template part is literal text, a ${...} sequence, which substitutes a value, or a %{...}
# directive (if, for), which decides whether and how often the literal text around it appears.
LITERAL = "literal"
INTERPOLATION = "interpolation"
DIRECTIVE = "directive"

_ESCAPES = {"n": "\n", "r": "\r", "t": "\t", '"': '"', "\\": "\\"}
_IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_-]*")
_NUMBER = re.compile(r"[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?")
_HEREDOC = re.compile(r"<<(-?)([A-Za-z_][A-Za-z0-9_-]*)[ \t]*\r?\n")
_HEX = frozenset("0123456789abcdefABCDEF")
# The operators longer than one character, matched before the single ones: `==` is one token and
# never two `=`, and `=>` is never an argument's `=`.
_OPERATORS = ("...", "==", "!=", "<=", ">=", "&&", "||", "=>")
_OPEN = frozenset("([{")
_CLOSE = frozenset(")]}")


class HclError(Exception):
    """Text the reader cannot tokenise or parse; the message starts with its line."""


@dataclass
class Token:
    kind: str  # ident, number, string, punct, newline or eof
    text: str  # the source text; a string's includes its quotes or its heredoc markers
    line: int
    start: int
    end: int
    parts: list = field(default_factory=list)  # a string's (kind, text) template parts


@dataclass
class Argument:
    name: str
    line: int
    value: list  # the expression's tokens, newlines dropped
    source: str  # the expression as written

    def string_parts(self) -> list | None:
        """The template parts when the value is one string, else None."""
        if len(self.value) == 1 and self.value[0].kind == "string":
            return self.value[0].parts
        return None


@dataclass
class Block:
    type: str
    labels: list
    line: int
    body: list  # Argument and Block items, in source order

    def argument(self, name: str) -> Argument | None:
        for item in self.body:
            if isinstance(item, Argument) and item.name == name:
                return item
        return None

    def blocks(self, type_: str | None = None) -> list:
        return [b for b in self.body if isinstance(b, Block) and type_ in (None, b.type)]


def parse(text: str) -> list:
    """A file's top-level body: its arguments and blocks, in source order."""
    return _Parser(text, _Lexer(text).tokens()).body(nested=False)


class _Lexer:
    def __init__(self, text: str, line: int = 1):
        self.text = text
        self.i = 0
        self.line = line

    def tokens(self) -> list:
        out = self._tokens(until_close=False)
        out.append(Token("eof", "", self.line, self.i, self.i))
        return out

    def _tokens(self, until_close: bool) -> list:
        """Tokens to the end of the text, or to the ``}`` that closes a ``${`` or ``%{``."""
        s, out, depth = self.text, [], 0
        while self.i < len(s):
            c, start = s[self.i], self.i
            if c == "\n":
                out.append(Token("newline", c, self.line, start, start + 1))
                self.i += 1
                self.line += 1
            elif c in " \t\r":
                self.i += 1
            elif c == "#" or s.startswith("//", start):
                end = s.find("\n", start)
                self.i = len(s) if end < 0 else end
            elif s.startswith("/*", start):
                end = s.find("*/", start + 2)
                if end < 0:
                    raise HclError(f"line {self.line}: a /* comment is never closed")
                self.line += s.count("\n", start, end)
                self.i = end + 2
            elif c == '"':
                line = self.line
                self.i += 1
                parts = self._template(quoted=True, line=line)
                out.append(Token("string", s[start : self.i], line, start, self.i, parts))
            elif c == "<" and _HEREDOC.match(s, start):
                out.append(self._heredoc())
            else:
                m = _IDENT.match(s, start) or _NUMBER.match(s, start)
                if m:
                    kind, text = ("ident" if m.re is _IDENT else "number"), m.group(0)
                else:
                    kind = "punct"
                    text = next((op for op in _OPERATORS if s.startswith(op, start)), c)
                if until_close and kind == "punct":
                    if text in _OPEN:
                        depth += 1
                    elif text in _CLOSE:
                        if depth == 0 and text == "}":
                            self.i += 1
                            return out
                        depth -= 1
                out.append(Token(kind, text, self.line, start, start + len(text)))
                self.i += len(text)
        if until_close:
            raise HclError(f"line {self.line}: a ${{...}} or %{{...}} sequence is never closed")
        return out

    def _template(self, quoted: bool, line: int) -> list:
        """A template's parts, from here to its closing quote or, in a heredoc, to the end.

        A quoted template takes backslash escapes and a heredoc does not; both read ``$${`` and
        ``%%{`` as the literal ``${`` and ``%{``.
        """
        s, parts, buf = self.text, [], []
        while True:
            if self.i >= len(s) or (quoted and s[self.i] == "\n"):
                if quoted:
                    raise HclError(f"line {line}: a string is never closed")
                break
            c = s[self.i]
            if quoted and c == '"':
                self.i += 1
                break
            if quoted and c == "\\":
                buf.append(self._escape())
            elif s.startswith(("$${", "%%{"), self.i):
                buf.append(s[self.i + 1 : self.i + 3])
                self.i += 3
            elif s.startswith(("${", "%{"), self.i):
                if buf:
                    parts.append((LITERAL, "".join(buf)))
                    buf = []
                start = self.i
                self.i += 2
                self._tokens(until_close=True)
                kind = INTERPOLATION if c == "$" else DIRECTIVE
                parts.append((kind, s[start : self.i]))
            else:
                if c == "\n":
                    self.line += 1
                buf.append(c)
                self.i += 1
        if buf:
            parts.append((LITERAL, "".join(buf)))
        return parts

    def _escape(self) -> str:
        s, i = self.text, self.i
        code = s[i + 1 : i + 2]
        if code in _ESCAPES:
            self.i += 2
            return _ESCAPES[code]
        width = {"u": 4, "U": 8}.get(code, 0)
        digits = s[i + 2 : i + 2 + width]
        if not width or len(digits) != width or not set(digits) <= _HEX:
            raise HclError(f"line {self.line}: an invalid escape \\{code}")
        self.i += 2 + width
        return chr(int(digits, 16))

    def _heredoc(self) -> Token:
        s, start, line = self.text, self.i, self.line
        m = _HEREDOC.match(s, start)
        flush, marker = m.group(1) == "-", m.group(2)
        self.i = m.end()
        self.line += 1
        rows = []
        while True:
            if self.i >= len(s):
                raise HclError(f"line {line}: the heredoc {marker} is never closed")
            end = s.find("\n", self.i)
            end = len(s) if end < 0 else end
            row = s[self.i : end]
            if row.strip() == marker:
                # The newline after the marker stays a token: it is what ends the argument.
                self.i += len(row.rstrip())
                break
            rows.append(row + "\n")
            self.i = end + 1
            self.line += 1
        if flush:
            indent = min((len(r) - len(r.lstrip(" \t")) for r in rows if r.strip()), default=0)
            rows = [r[indent:] if r.strip() else r.lstrip(" \t") for r in rows]
        parts = _Lexer("".join(rows), line + 1)._template(quoted=False, line=line)
        return Token("string", s[start : self.i], line, start, self.i, parts)


class _Parser:
    def __init__(self, text: str, tokens: list):
        self.text = text
        self.tokens = tokens
        self.i = 0

    def body(self, nested: bool) -> list:
        items = []
        while True:
            tok = self.tokens[self.i]
            if tok.kind == "newline":
                self.i += 1
            elif tok.kind == "eof":
                if nested:
                    raise HclError(f"line {tok.line}: a block is never closed")
                return items
            elif nested and tok.kind == "punct" and tok.text == "}":
                self.i += 1
                return items
            elif tok.kind == "ident":
                self.i += 1
                items.append(self._item(tok))
            else:
                raise HclError(
                    f"line {tok.line}: expected an argument or a block, not {tok.text!r}"
                )

    def _item(self, name: Token) -> Argument | Block:
        tok = self.tokens[self.i]
        if tok.kind == "punct" and tok.text == "=":
            self.i += 1
            return self._argument(name)
        labels = []
        while self.tokens[self.i].kind in ("ident", "string"):
            label = self.tokens[self.i]
            labels.append(label.text if label.kind == "ident" else _literal(label))
            self.i += 1
        tok = self.tokens[self.i]
        if not (tok.kind == "punct" and tok.text == "{"):
            raise HclError(f"line {tok.line}: expected = or {{ after {name.text}")
        self.i += 1
        return Block(name.text, labels, name.line, self.body(nested=True))

    def _argument(self, name: Token) -> Argument:
        """An argument's value: its tokens up to a newline outside any bracket."""
        value, depth = [], 0
        while True:
            tok = self.tokens[self.i]
            if tok.kind == "eof" or (tok.kind == "newline" and depth == 0):
                break
            if tok.kind == "punct" and tok.text in _OPEN:
                depth += 1
            elif tok.kind == "punct" and tok.text in _CLOSE:
                if depth == 0:
                    break  # the } closing a one-line block, `ingress { description = "..." }`
                depth -= 1
            if tok.kind != "newline":
                value.append(tok)
            self.i += 1
        if not value:
            raise HclError(f"line {name.line}: {name.text} = has no value")
        source = self.text[value[0].start : value[-1].end]
        return Argument(name.text, name.line, value, source)


def _literal(token: Token) -> str:
    """A block label's text: a quoted string with no sequence in it."""
    if any(kind != LITERAL for kind, _ in token.parts):
        raise HclError(f"line {token.line}: a block label cannot carry {token.text}")
    return "".join(text for _, text in token.parts)
