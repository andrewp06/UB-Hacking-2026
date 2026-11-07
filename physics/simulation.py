import pymonk
import math
from dataclasses import dataclass
DT = 1.0 / 120.0
DURATION = 8.0
GROUND_Y = 545
START_X = 230
PIXELS_PER_METER = 100.0 


@dataclass
class SimulationResult:
    distance: float       # Maximum forward displacement, display meters.
    survival_time: float  # Simulated seconds until a fall or the time limit.
    fell: bool


