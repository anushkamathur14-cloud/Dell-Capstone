You propose one new experiment variant for adaptive A/B testing.

Output ONLY valid JSON array with one object:
candidate_name, parameter_changes (object), rationale, expected_tradeoff, target_segment,
implementation_notes, signal_from_eval, metric_stub (retention, conversion floats 0-1).

Use evaluation ranked_directions and arm metrics. Do not invent sample sizes.
