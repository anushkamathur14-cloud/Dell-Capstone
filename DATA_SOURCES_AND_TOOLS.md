# Data sources and tools (adaptive experimentation agent)

Companion to [ARCHITECTURE.md](ARCHITECTURE.md). Use this to pick **data** and **tooling** for a prototype or production-shaped build.

---

## Data sources you can use

### Prototype / capstone (no real product telemetry)

| Kind | What it gives you | Examples |
|------|-------------------|----------|
| **Synthetic** | Control over assignment, outcomes, confounders | Scripts that simulate users, arms, and rewards (strong fit for validating bandit + causal code) |
| **Public game / player metrics** | Retention, monetization-style aggregates | Kaggle datasets tagged mobile games, player retention, churn (check license and leakage) |
| **Marketing / digital ads** | Channel, creative, campaign-style dimensions | Sample multi-channel or campaign performance datasets (Kaggle, academic repos) |
| **Classic experimentation** | A/B-style logs | Any table with user identifier, variant, outcome, timestamp; or data generated from a known data-generating process |

Prefer **synthetic** data when you need clean randomization to validate uplift/causal estimators; use **public** tables for narrative and charts when experiment IDs are weak or missing.

### Production-shaped (later)

| Kind | Typical systems |
|------|-----------------|
| **Experiment / feature flags** | LaunchDarkly, Optimizely, Statsig, Eppo, GrowthBook, or internal A/B tools |
| **Event stream** | Segment, Snowplow, Amplitude or Mixpanel exports, Kafka plus lake |
| **Warehouse** | Snowflake, Databricks, BigQuery, Redshift — join experiment facts to outcome facts on user and time |
| **Config / game parameters** | CMS, remote config, versioned JSON in object storage with a metadata database |

The architecture assumes a **warehouse plus experimentation platform** as the main spine.

---

## Tools by layer (reasonable defaults)

### Ingestion, storage, SQL

- **Warehouse / lakehouse**: Databricks, Snowflake, or BigQuery (match course or employer standard).
- **Orchestration**: Airflow, Dagster, or Prefect for pipelines; **Temporal** for durable workflows (launch experiment, wait, retrain).
- **Object storage** (video or screenshots in later phases): S3, Azure Blob, or GCS.

### Layer 1 — Perception (optional for v1)

- **Vision**: OpenCV; **PyTorch** plus a small detector/classifier if extracting UI elements from frames.
- **Feature store (optional)**: Feast, or plain curated tables in the warehouse for a capstone.

### Layer 2 — Generation (hypotheses)

- **LLM**: OpenAI, Anthropic, **Azure OpenAI** (common enterprise path), or on-prem Llama-class models if required.
- **Retrieval (experiment knowledge base)**: Embeddings in **pgvector**, **LanceDB**, **Chroma**, **Pinecone**, or your warehouse vendor’s vector features — for past experiments, configs, and playbooks.

### Layer 3 — Evaluation (causal / uplift)

- **Python**: **EconML**, **CausalML**, **DoWhy** (often with scikit-learn).
- **Statistics**: **statsmodels**, **scipy**; treat sequential testing and multiple comparisons explicitly.

### Layer 4 — Optimization (bandits / light RL)

- **Bandits**: **Vowpal Wabbit**, or a small **contextual bandit** in NumPy or PyTorch for transparency.
- **Heavier RL** (only if needed): **Ray RLlib**, **Stable-Baselines3** — more operational load; fine for research prototypes.

### API, UI, governance

- **API**: FastAPI pairs naturally with the Python ML stack.
- **UI**: React, or Streamlit / Gradio for fast internal demos.
- **Auth**: OIDC / SSO (Auth0, Okta, Azure AD, etc.).

---

## Phased adoption (avoid boiling the ocean)

1. **Phase A**: One warehouse (or local Parquet) plus **synthetic or CSV experiment logs**, **causal/uplift** in a notebook, and a **simple LLM** proposing next tests under a **fixed JSON schema** (validates Evaluation and Generation safely).
2. **Phase B**: Add a **bandit** over a **small discrete arm set** and a stub **experiment platform** API (even file-backed plus a scheduler) to prove the closed loop.
3. **Phase C**: Add **video or UI perception** only if the problem statement requires it.

---

## Narrowing the stack

Say whether you are optimizing for **course demo**, **Databricks**, or **fully local/offline** — the choices above collapse to one concrete path per category.
