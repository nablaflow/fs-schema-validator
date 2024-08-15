import enum
from collections.abc import Iterator
from typing import Any, NewType

from pydantic import ConfigDict, field_validator
from pydantic.dataclasses import dataclass
from sortedcontainers import SortedSet

from .errors import CoercionError, UnboundSymbolError


@dataclass(frozen=True, config=ConfigDict(validate_assignment=True))
class String:
    string: str

    def expand(
        self,
        _bindings: "Bindings",
        _leave_unbound_vars_in: bool = False,
        _format: str | None = None,
    ) -> Iterator[str]:
        return iter([self.string])

    def eval(self, _bindings: "Bindings") -> str:
        return self.string

    def __str__(self) -> str:
        return self.string

    def coerce_to_string(self) -> "String":
        return self


@dataclass(frozen=True, config=ConfigDict(validate_assignment=True))
class Binding:
    ident: str

    def expand(
        self,
        bindings: "Bindings",
        leave_unbound_vars_in: bool = False,
        format: str | None = None,
    ) -> Iterator[str]:
        return self._lookup(bindings).expand(bindings, leave_unbound_vars_in, format)

    def eval(self, bindings: "Bindings") -> "Expandable":
        return self._lookup(bindings)

    def _lookup(self, bindings: "Bindings") -> "Expandable":
        try:
            return bindings[self.ident]
        except KeyError as ex:
            raise UnboundSymbolError(f"no value provided for binding `{self.ident}`") from ex

    def __str__(self) -> str:
        return f"${self.ident}"


@dataclass(frozen=True, config=ConfigDict(validate_assignment=True, arbitrary_types_allowed=True))
class Enum:
    variants: SortedSet

    @field_validator("variants", mode="before")
    @classmethod
    def coerce_into_sorted_set(cls, v: Any) -> Any:
        if isinstance(v, set):
            return SortedSet(v)

        return v

    def expand(
        self,
        _bindings: "Bindings",
        _leave_unbound_vars_in: bool = False,
        format: str | None = None,
    ) -> Iterator[str]:
        return (_format(s, format) for s in self.variants)

    def __str__(self) -> str:
        return "|".join(self.variants)

    def coerce_to_string(self) -> String:
        if len(self.variants) == 1:
            return String(self.variants[0])

        raise CoercionError(f"cannot coerce enum {{{self}}} into String: variants > 1")


@dataclass(frozen=True, config=ConfigDict(validate_assignment=True))
class Range:
    start: int
    end: int

    def expand(
        self,
        _bindings: "Bindings",
        _leave_unbound_vars_in: bool = False,
        format: str | None = None,
    ) -> Iterator[str]:
        return (_format(n, format) for n in range(self.start, self.end + 1))

    def __str__(self) -> str:
        return f"{self.start}..{self.end}"

    def coerce_to_string(self) -> String:
        raise CoercionError(f"cannot coerce range {{{self}}} into String")


@dataclass(frozen=True, config=ConfigDict(validate_assignment=True))
class Expansion:
    value: Binding | Range | Enum
    format: str | None = None

    def expand(
        self,
        bindings: "Bindings",
        leave_unbound_vars_in: bool = False,
    ) -> Iterator[str]:
        try:
            return self.value.expand(bindings, leave_unbound_vars_in, self.format)
        except UnboundSymbolError as ex:
            if not leave_unbound_vars_in:
                raise ex

            return iter([f"{self}"])

    def __str__(self) -> str:
        if self.format is None:
            return f"{{{self.value}}}"

        return f"{{{self.value}:{self.format}}}"


def _format(v: Any, format: str | None = None) -> str:
    if format is None:
        return f"{v}"

    return f"{{0:{format}}}".format(v)


Template = NewType("Template", list[String | Expansion])
Expandable = String | Enum | Range
Bindings = dict[str, Expandable]
Assignment = NewType("Assignment", tuple[str, Expandable])


@enum.unique
class Operator(enum.Enum):
    EQ = "=="
    NEQ = "!="


@dataclass(frozen=True, config=ConfigDict(validate_assignment=True))
class BooleanExpr:
    left: Binding
    op: Operator
    right: String

    def eval(self, bindings: Bindings) -> "EvaluationResult":
        left = self.left.eval(bindings).coerce_to_string()

        if self.op is Operator.EQ:
            return left == self.right

        if self.op is Operator.NEQ:
            return left != self.right

        raise NotImplementedError(f"don't know how to eval operator {self.op}")


Expression = BooleanExpr
EvaluationResult = bool
