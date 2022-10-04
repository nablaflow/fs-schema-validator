import itertools
from typing import Iterator

from .parser import parse_template
from .values import Bindings, Expandable


def expand(
    s: str, bindings: Bindings = {}, leave_unbound_vars_in: bool = False
) -> Iterator[str]:
    values = parse_template(s)

    return map(
        lambda it: "".join(it),
        itertools.product(
            *[value.expand(bindings, leave_unbound_vars_in) for value in values]
        ),
    )
