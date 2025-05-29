from enum import Enum


class TaskStatus(str, Enum):
    PENDING = 'pending'
    PROCESSING = 'processing'
    COMPLETED = 'completed'
    FAILED = 'failed'

class UserStatus(str, Enum):
    BRONZE = 'bronze'
    SILVER = 'silver'
    GOLD = 'gold'
    DIAMOND = 'diamond'
