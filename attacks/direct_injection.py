from .base import BaseAttack, AttackResult


class DirectInjectionAttack(BaseAttack):
    """
    Simplest attack: send the request as-is with no wrapping.
    Used as a baseline to measure model's raw refusal rate.
    """
    name = "direct_injection"
    description = "Sends the target behavior as a raw, unwrapped prompt. Baseline test."
    severity = "low"

    async def run(self, connector, target_behavior: str) -> AttackResult:
        prompt = target_behavior  # No manipulation — pure baseline

        response, tokens, cost = await connector.send(prompt)

        return AttackResult(
            attack_name=self.name,
            target_behavior=target_behavior,
            prompt=prompt,
            response=response,
            success=False,        # Evaluator sets this — placeholder
            tokens_used=tokens,
            cost_usd=cost,
            notes="Baseline — no obfuscation applied.",
        )
