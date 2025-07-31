from enum import Enum

class SubTaskState(Enum):
    PENDING = 0
    INFO_GATHERING = 1
    EXECUTING = 2
    VALIDATING = 3
    COMPLETED = 4