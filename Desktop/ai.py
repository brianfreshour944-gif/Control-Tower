import json
import aiohttp

class AIClient:
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model

    async def evaluate(self, context: dict) -> dict:
        """
        Returns: {"action": "BUY"|"SELL"|"HOLD", "confidence": float, "reason": str}
        """
        prompt = f"""
        You are an expert quantitative trading assistant.
        Evaluate the following market context and decide whether the bot should BUY, SELL, or HOLD.

        Context:
        {json.dumps(context, indent=2)}

        Rules:
        - Only return BUY, SELL, or HOLD.
        - BUY only if trend, volatility, and regime strongly support upside.
        - SELL only if downside risk is high or position is overextended.
        - HOLD if conditions are mixed or unclear.
        - Include a confidence score (0–1) and a short reason.
        """

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.groq.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                },
            ) as resp:
                data = await resp.json()
                text = data["choices"][0]["message"]["content"]

        try:
            return json.loads(text)
        except:
            return {"action": "HOLD", "confidence": 0.0, "reason": "AI parse error"}