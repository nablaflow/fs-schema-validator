from dataclasses import dataclass
from typing import Dict, Iterator, Set, Tuple, Union

from .errors import UnboundSymbol


@dataclass
class String:
    string: str

    def expand(self, _bindings: "Bindings") -> Iterator[str]:
        return iter([self.string])

    def __str__(self) -> str:
        return self.string


@dataclass
class Binding:
    ident: str

    def expand(self, bindings: "Bindings") -> Iterator[str]:
        try:
            return bindings[self.ident].expand(bindings)
        except KeyError:
            raise UnboundSymbol(f"no value provided for binding ${self.ident}")


@dataclass
class Enum:
    variants: Set[str]

    def expand(self, _bindings: "Bindings") -> Iterator[str]:
        return iter(self.variants)

    def __str__(self) -> str:
        return "|".join(self.variants)


@dataclass
class Range:
    start: int
    end: int

    def expand(self, _bindings: "Bindings") -> Iterator[str]:
        return (str(n) for n in range(self.start, self.end + 1))

    def __str__(self) -> str:
        return f"{self.start}..{self.end}"


Value = Union[String, Enum, Range, Binding]
Expandable = Union[String, Enum, Range]
Bindings = Dict[str, Expandable]
Assignment = Tuple[str, Union[Enum, Range, String]]
