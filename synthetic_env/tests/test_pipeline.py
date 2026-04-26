from synthetic_env.pipeline import run_generation


def test_run_generation_smoke() -> None:
    outputs = run_generation(n_users=300, experiment_id="exp_test_001", seed=13, output_dir="synthetic_env/benchmarks/generated_test")
    assert not outputs["metrics_summary"].empty
    assert outputs["validation_report"].shape[0] >= 4
