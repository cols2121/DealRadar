import os
import anthropic

MODELS = {
    "anthropic": "claude-haiku-4-5-20251001",
    "anthropic-smart": "claude-sonnet-4-6",
}

COSTS = {
    "claude-haiku-4-5-20251001": (0.02, 0.10),
    "claude-sonnet-4-6": (0.24, 1.20),
}


class LLMClient:
    def __init__(self, provider: str | None = None):
        self.provider = provider or os.getenv("LLM_PROVIDER", "anthropic")
        if self.provider == "mock":
            return
        if not os.getenv("ANTHROPIC_API_KEY"):
            raise ValueError("ANTHROPIC_API_KEY not set")
        self._client = anthropic.Anthropic()
        self.model = MODELS.get(self.provider, MODELS["anthropic"])

    def complete(self, prompt: str, system: str = "", max_tokens: int = 1024) -> str:
        if self.provider == "mock":
            return (
                '{"score":50,"stage_guess":"pre-seed","one_line":"Mock company",'
                '"memo_3_lines":"Mock memo.","confidence":"low","evidence_urls":[]}'
            )
        msg = self._client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        usage = msg.usage
        in_cost, out_cost = COSTS.get(self.model, (0, 0))
        cost_gbp = (usage.input_tokens * in_cost + usage.output_tokens * out_cost) / 1_000_000
        print(f"[llm] {usage.input_tokens}in {usage.output_tokens}out £{cost_gbp:.5f}")
        return msg.content[0].text
