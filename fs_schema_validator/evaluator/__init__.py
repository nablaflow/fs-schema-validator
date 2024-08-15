import itertools
from collections.abc import Iterator

from .parser import parse_expression, parse_template
from .values import Bindings, EvaluationResult


def expand(
    s: str, bindings: Bindings | None = None, leave_unbound_vars_in: bool = False
) -> Iterator[str]:
    if bindings is None:
        bindings = {}

    values = parse_template(s)

    return (
        "".join(it)
        for it in itertools.product(
            *(value.expand(bindings, leave_unbound_vars_in) for value in values)
        )
    )


def evaluate(s: str, bindings: Bindings | None = None) -> EvaluationResult:
    if bindings is None:
        bindings = {}

    return parse_expression(s).eval(bindings)
