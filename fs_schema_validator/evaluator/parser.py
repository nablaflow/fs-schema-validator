from typing import List, Tuple, Union

from parsita import ParseError, TextParsers, lit, opt, reg, rep1, rep1sep
from pydantic import parse_obj_as
from sortedcontainers import SortedSet

from .values import (
    Assignment,
    Binding,
    BooleanExpr,
    Enum,
    Expansion,
    Expression,
    Operator,
    Range,
    String,
    Template,
)

__all__ = [
    "ParseError",
    "parse_template",
]


# TODO: introduce enum variants between "" to include unacceptable characters (|${}) due to parsing.
class TemplateParsers(TextParsers):  # type: ignore[misc]
    symbol = reg(r"[a-zA-Z][a-zA-Z-_0-9]+")
    integer = reg(r"[-+]?\d+") > int
    enum = rep1sep(reg(r"[^:|${}]*"), "|") > (
        lambda l: Enum(SortedSet((s.strip() for s in l)))
    )
    range = (integer << ".." & integer) > (lambda t: Range(t[0], t[1]))
    binding = ("$" >> symbol) > Binding
    py_format = ":" >> reg(r"[^{}]+")
    expansion = ("{" >> (binding | range | enum) & opt(py_format) << "}") > (
        lambda t: Expansion(t[0], format=t[1][0] if len(t[1]) != 0 else None)
    )
    string = reg(r"[^{}]+") > String
    escaped_expansion = ("{{" >> string << "}}") > (lambda s: String(f"{{{s.string}}}"))

    template = rep1(string | expansion | escaped_expansion) | (
        lit("") > (lambda s: [String(s)])
    )

    op = (lit("==") | lit("!=")) > Operator
    boolean_op = (binding & op & string) > (lambda t: BooleanExpr(t[0], t[1], t[2]))
    expression = boolean_op

    assignment = (symbol << "=" & (range | enum)) > (lambda t: (t[0], t[1]))


def parse_template(s: str) -> Template:
    return parse_obj_as(Template, TemplateParsers.template.parse(s).or_die())


def parse_expression(s: str) -> Expression:
    return parse_obj_as(Expression, TemplateParsers.expression.parse(s).or_die())


def parse_assignment(s: str) -> Assignment:
    return parse_obj_as(Assignment, TemplateParsers.assignment.parse(s).or_die())
