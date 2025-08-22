from datetime import datetime, timedelta
from typing import Protocol
from pydantic import BaseModel, Field

class BackoffStrategy(Protocol):
    """Protocol defining retry backoff behavior"""
    
    min_delay: float
    max_delay: float
    
    def calculate_next_retry(self, retry_count: int, last_retry: datetime) -> datetime:
        """Calculate the next retry time based on retry count and last attempt
        
        Args:
            retry_count: Number of retries attempted so far
            last_retry: Timestamp of the last retry attempt
            
        Returns:
            Datetime when the next retry should occur
        """
        ...

class ExponentialBackoff:
    """Exponential backoff with multiplier and bounds"""
    
    def __init__(self, min_delay: float, max_delay: float, multiplier: float = 2.0):
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.multiplier = multiplier
    
    def calculate_next_retry(self, retry_count: int, last_retry: datetime) -> datetime:
        """Calculate next retry time with exponential backoff

        For retry_count:
        1 -> min_delay
        2 -> min_delay * multiplier
        3 -> min_delay * multiplier^2
        etc.

        Example with min_delay=1, multiplier=2:
        retry_count=1 -> 1s
        retry_count=2 -> 2s
        retry_count=3 -> 4s
        retry_count=4 -> 8s
        """
        # retry_count=1 should use min_delay
        # retry_count=2 should use min_delay * multiplier
        # retry_count=3 should use min_delay * multiplier^2
        exponent = max(0, retry_count - 1)  # -1 to get 0 for first retry
        delay = self.min_delay * (self.multiplier ** exponent)
        
        # Ensure delay is within bounds
        delay = min(max(delay, self.min_delay), self.max_delay)
        return last_retry + timedelta(seconds=delay)

class LinearBackoff:
    """Linear backoff with fixed increment and bounds"""
    
    def __init__(self, min_delay: float, max_delay: float, increment: float):
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.increment = increment
    
    def calculate_next_retry(self, retry_count: int, last_retry: datetime) -> datetime:
        """Calculate next retry time with linear backoff

        For retry_count:
        1 -> min_delay
        2 -> min_delay + increment
        3 -> min_delay + (increment * 2)
        etc.

        Example with min_delay=1, increment=5:
        retry_count=1 -> 1s
        retry_count=2 -> 6s (1 + 5)
        retry_count=3 -> 11s (1 + 5*2)
        retry_count=4 -> 16s (1 + 5*3)
        """
        # retry_count=1 should use min_delay
        # retry_count=2 should use min_delay + increment
        # retry_count=3 should use min_delay + increment*2
        multiplier = max(0, retry_count - 1)  # -1 to get 0 for first retry
        delay = self.min_delay + (self.increment * multiplier)
        
        # Ensure delay is within bounds
        delay = min(max(delay, self.min_delay), self.max_delay)
        return last_retry + timedelta(seconds=delay)

class BackoffConfig(BaseModel):
    """Configuration for retry backoff behavior"""
    min_delay: float = Field(
        default=1.0,
        description="Minimum delay between retries in seconds",
        ge=0.1
    )
    max_delay: float = Field(
        default=300.0,
        description="Maximum delay between retries in seconds",
        ge=1.0
    )
    strategy: str = Field(
        default="exponential",
        description="Backoff strategy to use (exponential or linear)"
    )
    multiplier: float = Field(
        default=2.0,
        description="Multiplier for exponential backoff",
        ge=1.1
    )
    increment: float = Field(
        default=5.0,
        description="Increment for linear backoff in seconds",
        ge=0.1
    )