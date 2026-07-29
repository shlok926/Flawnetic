from anthropic import AsyncAnthropic
from config.settings import settings

class AIAnalyzer:
    def __init__(self):
        # We use Anthropic Claude to enrich QA findings
        self.client = AsyncAnthropic(api_key=settings.anthropic_api_key)

    async def analyze_finding(self, title: str, description: str, steps: dict) -> str:
        """
        Sends the raw bug finding to Claude to generate a professional Root Cause 
        and Remediation plan.
        """
        if not settings.anthropic_api_key or settings.anthropic_api_key == "your-anthropic-api-key":
            return "AI Remediation skipped: Valid Anthropic API Key not found in .env."

        prompt = f"""
You are a Senior Application Security and QA Engineer. 
I have found a bug/vulnerability in a web application during an automated scan.

Title: {title}
Description: {description}
Steps to Reproduce: {steps}

Provide a concise, professional explanation containing:
1. Root Cause: Why this typically happens.
2. Remediation: Concrete steps or code snippets to fix this.
3. False Positive Check: What to look for to confirm it's real.

Keep it under 3 paragraphs and format it nicely using Markdown. Do not include introductory fluff.
"""
        
        try:
            response = await self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1000,
                temperature=0.2,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return response.content[0].text
        except Exception as e:
            return f"AI Analysis failed: {str(e)}"
