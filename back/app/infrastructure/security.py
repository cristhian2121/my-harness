from __future__ import annotations

from app.application.use_cases import SecurityDecision


class PromptSecurityFilter:
    def __init__(self) -> None:
        self._rules: dict[str, tuple[str, ...]] = {
            "prompt_injection": (
                "ignore previous instructions",
                "system prompt",
                "reveal your instructions",
                "show hidden prompt",
                "developer message",
            ),
            "credential_exfiltration": (
                "api key",
                "secret",
                "password",
                "token",
                "credentials",
            ),
            "offensive_security": (
                "sql injection",
                "bypass authentication",
                "exploit",
                "payload",
                "privilege escalation",
                "remote code execution",
                "xss",
            ),
        }

    def validate(self, message: str) -> SecurityDecision:
        normalized_message = message.strip().lower()
        for category, patterns in self._rules.items():
            if any(pattern in normalized_message for pattern in patterns):
                return SecurityDecision(
                    allowed=False,
                    category=category,
                    reason=f"Rejected by local security rule: {category}.",
                )
        return SecurityDecision(allowed=True)
