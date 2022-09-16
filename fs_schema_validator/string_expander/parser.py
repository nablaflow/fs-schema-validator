from typing import List, Tuple, Union

from parsita import ParseError, TextParsers, reg, rep1, rep1sep

from .values import Assignment, Binding, Enum, Range, String, Value

__all__ = [
    "ParseError",
    "parse_template",
]


class TemplateParsers(TextParsers):  # type: ignore[misc]
    symbol = reg(r"[a-zA-Z][a-zA-Z-_0-9]+")
    integer = reg(r"\d+") > int
    enum = rep1sep(symbol, "|") > (lambda l: Enum(set(l)))
    range = (integer << ".." & integer) > (lambda t: Range(t[0], t[1]))
    binding = ("$" >> symbol) > (lambda s: Binding(s))
    placeholder = "{" >> (enum | range | binding) << "}"
    string = reg(r"[^{}]+") > (lambda s: String(s))
    template = rep1(string | placeholder)

    assignment = (symbol << "=" & (enum | range | string)) > (lambda t: (t[0], t[1]))


def parse_template(s: str) -> List[Value]:
    return TemplateParsers.template.parse(s).or_die()


def parse_assignment(s: str) -> Assignment:
    return TemplateParsers.assignment.parse(s).or_die()
