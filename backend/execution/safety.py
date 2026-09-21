from datetime import datetime, timedelta
from typing import Tuple, Optional
from backend.data.models import SpotData, OptionChain

class ExecutionSafetyEngine:
    def __init__(self, max_allowed_stale_seconds: int = 30):
        self.max_allowed_stale_seconds = max_allowed_stale_seconds
        self.kill_switch_active = False

    def activate_kill_switch(self, reason: str = "Manual override"):
        self.kill_switch_active = True
        return f"Kill switch activated: {reason}"

    def deactivate_kill_switch(self):
        self.kill_switch_active = False
        return "Kill switch deactivated"

    def validate_data_freshness(self, spot: SpotData) -> Tuple[bool, Optional[str]]:
        if self.kill_switch_active:
            return False, "Execution blocked: Kill switch is ACTIVE"

        age_seconds = (datetime.now() - spot.timestamp).total_seconds()
        if age_seconds > self.max_allowed_stale_seconds:
            return False, f"Execution blocked: Data is stale ({round(age_seconds, 1)}s old > limit {self.max_allowed_stale_seconds}s)"

        return True, None
