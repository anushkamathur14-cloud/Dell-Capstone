"""Validation skill stub."""


class ValidationSkill:
    def run(self, context: dict) -> dict:
        issues = []

        if not context["experiment"].traffic_split:
            issues.append("Missing traffic split.")

        if not context["metrics"]:
            issues.append("No metrics summary available.")

        decision = "go" if not issues else "caution"
        if len(issues) > 2:
            decision = "stop"

        return {"decision": decision, "issues": issues}
