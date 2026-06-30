from enum import Enum


class ProductionRunStatus(str, Enum):

    CREATED = "CREATED"

    RUNNING = "RUNNING"

    COMPLETED = "COMPLETED"

    CANCELLED = "CANCELLED"

    BLOCKED = "BLOCKED"