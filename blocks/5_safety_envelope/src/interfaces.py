# Block 5: Safety - Interfaces
from enum import Enum

class Action(Enum):
    EMERGENCY_BRAKE = 'EMERGENCY'
    SERVICE_BRAKE = 'SERVICE'
    WARNING = 'WARNING'
    CAUTION = 'CAUTION'
    CLEAR = 'CLEAR'
