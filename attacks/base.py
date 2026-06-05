from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class AttackResult:
    attack_name: str
    target_behavior: str
    prompt: str
    response: str
    success: bool
    confidence: float = 0.0        # 0.0 – 1.0
    tokens_used: int = 0
    cost_usd: float = 0.0
    notes: str = ""
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class BaseAttack(ABC):
    name: str = "base"
    description: str = ""
    severity: str = "medium"       # low | medium | high | critical

    @abstractmethod
    async def run(self, connector, target_behavior: str) -> AttackResult:
        """
        Build and send the attack prompt.
        Returns an AttackResult.
        """
        ...

    def __repr__(self):
        return f"<Attack: {self.name} [{self.severity}]>"
