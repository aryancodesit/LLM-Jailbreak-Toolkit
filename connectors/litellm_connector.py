import os
import asyncio
import litellm
from typing import Tuple

litellm.telemetry = False  # Disable litellm telemetry


class LiteLLMConnector:
    """
    Thin wrapper around litellm.
    Returns (response_text, tokens_used, cost_usd).
    """

    def __init__(self, config: dict):
        self.model = config["target"]["model"]
        self.api_key = config["target"]["api_key"]
        self.max_tokens = config["target"].get("max_tokens", 512)
        self.temperature = config["target"].get("temperature", 0.7)
        self._total_cost = 0.0

        # Set key in env so litellm picks it up
        provider = self.model.split("/")[0]
        key_map = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "google": "GEMINI_API_KEY",
            "gemini": "GEMINI_API_KEY",
            "groq": "GROQ_API_KEY",
        }
        if env_var := key_map.get(provider):
            os.environ[env_var] = self.api_key

    async def send(self, prompt: str) -> Tuple[str, int, float]:
        import litellm.exceptions

        # Small base throttle to prevent instant bursts
        await asyncio.sleep(1.0)

        for attempt in range(4):
            try:
                response = await litellm.acompletion(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                )

                text = response.choices[0].message.content or ""
                tokens = response.usage.total_tokens if response.usage else 0

                try:
                    cost = litellm.completion_cost(completion_response=response)
                except Exception:
                    cost = 0.0

                self._total_cost += cost
                return text, tokens, cost

            except Exception as e:
                err_msg = str(e).lower()
                is_rate_limit = (
                    "rate limit" in err_msg 
                    or "429" in err_msg 
                    or "tpm" in err_msg 
                    or "rpm" in err_msg
                    or isinstance(e, litellm.exceptions.RateLimitError)
                )
                
                if is_rate_limit and attempt < 3:
                    # Exponential backoff: 5s, 10s, 20s
                    wait_time = 5 * (2 ** attempt)
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    raise e

    @property
    def total_cost(self) -> float:
        return self._total_cost
