from typing import List, Tuple, Union

from parsita import ParseError, TextParsers, reg, rep1, rep1sep

from .values import Assignment, Binding, Enum, Range, String, Value

__all__ = [
    "ParseError",
    "parse_template",
]


# TODO: introduce enum variants between "" to include unacceptable characters (|${}) due to parsing.
class TemplateParsers(TextParsers):  # type: ignore[misc]
    symbol = reg(r"[a-zA-Z][a-zA-Z-_0-9]+")
    integer = reg(r"[-+]?\d+") > int
    enum = rep1sep(reg(r"[^|${}]*"), "|") > (lambda l: Enum(set((s.strip() for s in l))))
    range = (integer << ".." & integer) > (lambda t: Range(t[0], t[1]))
    binding = ("$" >> symbol) > Binding
    placeholder = "{" >> (binding | range | enum) << "}"
    string = reg(r"[^{}]+") > String

    template = rep1(string | placeholder)

    assignment = (symbol << "=" & (range | enum)) > (lambda t: (t[0], t[1]))


def parse_template(s: str) -> List[Value]:
    return TemplateParsers.template.parse(s).or_die()


def parse_assignment(s: str) -> Assignment:
    return TemplateParsers.assignment.parse(s).or_die()
