from dataclasses import dataclass, field
from datetime import datetime
from attacks.base import AttackResult


@dataclass
class StepResult:
    step_number:  int
    attack_name:  str
    attack_result: AttackResult
    action:       str    # "stop_success" | "escalate" | "combo_next" | "exhausted"


@dataclass
class ChainResult:
    strategy_name:   str
    target_behavior: str
    steps:           list[StepResult] = field(default_factory=list)
    final_success:   bool = False
    winning_attack:  str | None = None
    winning_step:    int | None = None
    total_tokens:    int = 0
    total_cost_usd:  float = 0.0
    timestamp:       str = field(
        default_factory=lambda: datetime.utcnow().isoformat()
    )

    def summary(self) -> dict:
        return {
            "strategy":       self.strategy_name,
            "target":         self.target_behavior,
            "success":        self.final_success,
            "winning_attack": self.winning_attack,
            "winning_step":   self.winning_step,
            "steps_run":      len(self.steps),
            "total_tokens":   self.total_tokens,
            "total_cost_usd": round(self.total_cost_usd, 6),
            "timestamp":      self.timestamp,
        }
