from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional

class RepeatMode(Enum):
    TIMES = auto()
    DURATION = auto()
    ENDLESS = auto()

@dataclass
class Repeat:
    mode: RepeatMode
    value: Optional[float] = None

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
    repeat: Optional[Repeat] = None
