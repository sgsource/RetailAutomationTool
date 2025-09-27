from dataclasses import dataclass
import re

@dataclass
class Feet:
    value: str
    def __repr__(self):
        return f"Feet({self.value})"

@dataclass
class Set:
    value: str
    def __repr__(self):
        return f"Set({self.value})"

@dataclass
class Undef:
    value: str
    def __repr__(self):
        return f"Undef('{self.value}')"

class UnitFactory:
    @staticmethod
    def create(text: str):
        match text.lower():
            case _ if (m := re.fullmatch(r"(\d+)\s*ft", text)):
                return Feet(m.group(1))
            case _ if (m := re.fullmatch(r"set\s+(\d+)", text)):
                return Set(m.group(1))
            case _:
                return Undef(text)

# Example usage
examples = ["12 ft", "set 1", "unknown format"]
for ex in examples:
    obj = UnitFactory.create(ex)
    print(obj, type(obj))
