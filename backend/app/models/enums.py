from enum import Enum


class ProductionRunStatus(str, Enum):
    RUNNING = "RUNNING"

    COMPLETED = "COMPLETED"