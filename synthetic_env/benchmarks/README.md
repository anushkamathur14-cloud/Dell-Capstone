# Synthetic Benchmark Baseline

## Baseline Freeze

- Baseline name: `benchmark_v1_delayed_effects_pass`
- Frozen artifacts directory: `synthetic_env/benchmarks/generated_sanity_calibrated/`

## Baseline Conclusion

- Compact and interpretable world
- Non-trivial treatment effects
- Heterogeneous effects present
- Delayed effects calibrated and validated
- Suitable for benchmarking recommendation-first adaptive experimentation workflows

## Included Artifacts

- `population.parquet`
- `experiments.parquet`
- `arms.parquet`
- `observations.parquet`
- `metrics_summary.parquet`
- `experiment_memory.parquet`
- `validation_report.parquet`
- `calibration_note.md`
- `sanity_summary.md`

## Notes for Development Phase

Use `generated_sanity_calibrated` as the v1 comparison anchor. Any future simulator changes should be evaluated against this baseline before introducing new benchmark versions.
