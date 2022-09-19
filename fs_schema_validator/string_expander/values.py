from typing import Dict, Iterator, Set, Tuple, Union

from pydantic.dataclasses import dataclass

from .errors import UnboundSymbol


@dataclass(frozen=True)
class String:
    string: str

    def expand(self, _bindings: "Bindings", leave_unbound_vars_in: bool) -> Iterator[str]:
        return iter([self.string])

    def __str__(self) -> str:
        return self.string


@dataclass(frozen=True)
class Binding:
    ident: str

    def expand(self, bindings: "Bindings", leave_unbound_vars_in: bool) -> Iterator[str]:
        try:
            binding = bindings[self.ident]
        except KeyError:
            if leave_unbound_vars_in:
                return iter([f"{{${self.ident}}}"])
            else:
                raise UnboundSymbol(f"no value provided for binding ${self.ident}")

        return binding.expand(bindings, leave_unbound_vars_in)


@dataclass(frozen=True)
class Enum:
    variants: Set[str]

    def expand(self, _bindings: "Bindings", leave_unbound_vars_in: bool) -> Iterator[str]:
        return iter(self.variants)

    def __str__(self) -> str:
        return "|".join(self.variants)


@dataclass(frozen=True)
class Range:
    start: int
    end: int

    def expand(self, _bindings: "Bindings", leave_unbound_vars_in: bool) -> Iterator[str]:
        return (str(n) for n in range(self.start, self.end + 1))

    def __str__(self) -> str:
        return f"{self.start}..{self.end}"


Value = Union[String, Enum, Range, Binding]
Expandable = Union[String, Enum, Range]
Bindings = Dict[str, Expandable]
Assignment = Tuple[str, Expandable]
