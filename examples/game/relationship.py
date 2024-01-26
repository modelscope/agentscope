from enum import Enum

class Familiarity(Enum):
    STRANGER = 1
    SLIGHTLY_FAMILIAR = 2
    FAMILIAR = 3

    MAX_LEVEL = FAMILIAR
    MIN_LEVEL = STRANGER

    @staticmethod
    def from_value(value):
        if isinstance(value, Familiarity):
            return value
        elif isinstance(value, int):
            if value in Familiarity._value2member_map_:
                return Familiarity._value2member_map_[value]
            else:
                raise ValueError(f"Invalid integer for Familiarity level: '{value}'")
        elif isinstance(value, str):
            descriptions = {
                "陌生": Familiarity.STRANGER,
                "稍微熟悉": Familiarity.SLIGHTLY_FAMILIAR,
                "熟悉": Familiarity.FAMILIAR
            }
            
            if value in descriptions:
                return descriptions[value]
            else:
                raise ValueError(f"Invalid string for Familiarity level: '{value}'")
        else:
            raise TypeError("Value must be a Familiarity instance, integer, or string.")

    def __str__(self):
        descriptions = {
            Familiarity.STRANGER: "陌生",
            Familiarity.SLIGHTLY_FAMILIAR: "稍微熟悉",
            Familiarity.FAMILIAR: "熟悉"
        }
        return descriptions.get(self, "Unknown")
    
    def __add__(self, other):
        """Increment familiarity, not exceeding 'FAMILIAR'."""
        if not isinstance(other, int):
            raise ValueError("Can only add an integer to Familiarity.")
        new_level = min(self.value + other, Familiarity.MAX_LEVEL.value)
        return Familiarity(new_level)


    def __sub__(self, other):
        """Decrement familiarity level, not going below 'STRANGER'."""
        if not isinstance(other, int):
            raise ValueError("Can only subtract an integer from Familiarity.")
        new_level = max(self.value - other, Familiarity.MIN_LEVEL.value)
        return Familiarity(new_level)


class Relationship:
    def __init__(self, init_level=1,
                 satis_thres=0):
        self._satis_thres = satis_thres
        self._level = Familiarity.from_value(init_level)
    
    def is_satisfied(self, score):
        return score > self._satis_thres 

    def update(self, score):
        if self.is_satisfied(score):
            self._level += 1
        else:
            self._level -= 1
    @property
    def level(self):
        return self._level
    
    def to_string(self):
        return str(self.level)

    def is_stranger(self):
        self.level == Familiarity.STRANGER

    @property
    def prompt(self):
        if self.level == Familiarity.STRANGER:
            return "stranger_prompt"
        elif self.level == Familiarity.SLIGHTLY_FAMILIAR:
            return "slight_familiar_prompt"
        elif self.level == Familiarity.FAMILIAR:
            return "familiar_prompt"
        else:
            return "stranger_prompt"


