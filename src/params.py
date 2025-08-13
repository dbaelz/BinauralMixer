from dataclasses import dataclass
from typing import Optional

@dataclass
class BinauralParams:
    left_freq: float
    left_end: Optional[float]
    right_freq: float
    right_end: Optional[float]

@dataclass
class EffectParams:
    file: str
    gain: float
    offset: float
