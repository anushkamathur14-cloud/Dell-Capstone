"""Lightweight recommendation scoring helper."""


def weighted_score(components: dict[str, float], weights: dict[str, float]) -> float:
    return sum(components.get(key, 0.0) * weights.get(key, 0.0) for key in components)
