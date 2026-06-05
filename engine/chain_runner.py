from attacks.registry import REGISTRY
from attacks.base import AttackResult
from engine.models import ChainResult, StepResult
from engine.combo_attack import ComboAttack


class ChainRunner:
    """
    Executes a strategy — the core of Phase 5.

    Reads a strategy dict, instantiates attacks in order,
    and chains them based on success/failure rules.

    Supports:
    - Sequential escalation (stop on first success)
    - Full scan (run all regardless)
    - Combo attacks (stack two techniques)
    - Async callback for live TUI streaming
    """

    def __init__(self, connector, evaluator, store=None):
        self.connector = connector
        self.evaluator = evaluator
        self.store     = store

    async def run(
        self,
        strategy: dict,
        target_behavior: str,
        on_step=None,       # async callback(step_result) for TUI streaming
    ) -> ChainResult:

        chain = ChainResult(
            strategy_name   = strategy.get("name", "unknown"),
            target_behavior = target_behavior,
        )

        stop_on_success = strategy.get("stop_on_success", True)
        steps           = strategy.get("steps", [])

        for i, step_def in enumerate(steps, start=1):

            # Budget guard
            if self.connector.total_cost >= self._budget():
                break

            # Build attack instance(s)
            attack = self._build_attack(step_def)
            if attack is None:
                continue

            # Run attack
            try:
                result: AttackResult = await attack.run(self.connector, target_behavior)
                result = await self.evaluator.evaluate(result)
            except Exception as e:
                result = AttackResult(
                    attack_name     = getattr(attack, "name", "unknown"),
                    target_behavior = target_behavior,
                    prompt          = "",
                    response        = f"[ERROR: {e}]",
                    success         = False,
                    notes           = f"Exception: {e}",
                )

            # Determine action
            if result.success and stop_on_success:
                action = "stop_success"
            elif result.success and not stop_on_success:
                action = "continue_success"
            elif i == len(steps):
                action = "exhausted"
            else:
                action = "escalate"

            step_result = StepResult(
                step_number  = i,
                attack_name  = result.attack_name,
                attack_result = result,
                action       = action,
            )

            chain.steps.append(step_result)
            chain.total_tokens  += result.tokens_used
            chain.total_cost_usd += result.cost_usd

            if self.store:
                self.store.save(result)

            # Fire live callback for TUI
            if on_step:
                await on_step(step_result)

            # Update chain-level success
            if result.success:
                chain.final_success  = True
                chain.winning_attack = result.attack_name
                chain.winning_step   = i
                if stop_on_success:
                    break
            
            # Rate limit guard sleep
            import asyncio
            await asyncio.sleep(2.0)

        return chain

    # ── helpers ──────────────────────────────────────────────────────────────

    def _build_attack(self, step_def: dict):
        """Build a single or combo attack from a step definition."""

        # Combo step: {"combo": ["attack_a", "attack_b"]}
        if "combo" in step_def:
            names = step_def["combo"]
            if len(names) < 2:
                return None
            a = self._instantiate(names[0])
            b = self._instantiate(names[1])
            if a and b:
                return ComboAttack(a, b)
            return None

        # Single step: {"attack": "attack_name"}
        if "attack" in step_def:
            return self._instantiate(step_def["attack"])

        return None

    def _instantiate(self, name: str):
        """Instantiate an attack by registry name."""
        if name not in REGISTRY:
            return None
        return REGISTRY[name]["class"]()

    def _budget(self) -> float:
        """Pull budget from connector if available."""
        return getattr(self.connector, '_budget_cap', 999.0)
