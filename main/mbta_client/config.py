from dataclasses import dataclass


@dataclass
class MBTAConfig:
    api_key: str
    base_url: str = "https://api-v3.mbta.com"
    timeout: int = 10
    max_retries: int = 3
    backoff_factor: float = 0.3
