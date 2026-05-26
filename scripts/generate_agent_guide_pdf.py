#!/usr/bin/env python3
"""Generate Dell Capstone agent architecture PDF guide."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from fpdf import FPDF

REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATHS = [
    REPO_ROOT / "Dell-Capstone-Agent-Guide.pdf",
    REPO_ROOT.parent / "Dell-Capstone-Agent-Guide.pdf",
]


class GuidePDF(FPDF):
    def footer(self) -> None:
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(100, 100, 100)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

    def _reset_x(self) -> None:
        self.set_x(self.l_margin)

    def section_title(self, title: str) -> None:
        self._reset_x()
        self.ln(4)
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(20, 60, 120)
        self.multi_cell(0, 8, title)
        self.set_text_color(0, 0, 0)
        self.ln(2)

    def subsection(self, title: str) -> None:
        self.ln(2)
        self._reset_x()
        self.set_font("Helvetica", "B", 11)
        self.multi_cell(0, 6, title)
        self.ln(1)

    def body(self, text: str) -> None:
        self._reset_x()
        self.set_font("Helvetica", "", 10)
        self.multi_cell(0, 5, text)
        self.ln(1)

    def bullet(self, text: str) -> None:
        self._reset_x()
        self.set_font("Helvetica", "", 10)
        self.multi_cell(0, 5, f"  -  {text}")


def build_pdf() -> FPDF:
    pdf = GuidePDF()
    pdf.alias_nb_pages()
    pdf.set_margins(left=18, top=18, right=18)
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(0, 10, "Adaptive Experimentation Agent", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 12)
    pdf.cell(0, 7, "Architecture, Orchestration, Skills and Workstreams", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.set_font("Helvetica", "I", 10)
    pdf.multi_cell(
        0,
        5,
        f"Generated: {date.today().isoformat()}  |  Repository: github.com/anushkamathur14-cloud/Dell-Capstone",
    )
    pdf.ln(6)

    pdf.section_title("1. Project purpose")
    pdf.body(
        "A recommendation-first agentic system that turns experiment data into validated insights "
        "and ranked next-best experiments. MVP avoids autonomous production execution; humans approve launches."
    )

    pdf.section_title("2. Repository layout")
    pdf.bullet("src/agent/ - Orchestrator + LangGraph agents (validation, recommendation)")
    pdf.bullet("src/skills/ - Modular capabilities called by the orchestrator")
    pdf.bullet("src/validation/ - Deterministic validation checks (workstream B)")
    pdf.bullet("src/recommendation/ - Scoring, ranking, explanation (workstream D)")
    pdf.bullet("src/data/models.py - Pydantic contracts (Experiment, ValidationReport, etc.)")
    pdf.bullet("src/api/main.py - FastAPI endpoints")
    pdf.bullet("synthetic_env/ - Offline benchmark generation + quality checks")
    pdf.bullet("docs/ - validation_agent.md, recommendation_agent.md, EXPERIMENTATION_DEV_PLAN.md")

    pdf.section_title("3. General orchestration")
    pdf.body(
        "AdaptiveExperimentationOrchestrator (src/agent/orchestrator.py) runs a linear pipeline. "
        "It does NOT use LangGraph at the top level; it calls skills in fixed order."
    )
    pdf.subsection("Pipeline sequence")
    pdf.bullet("1. RetrievalSkill - load experiment context")
    pdf.bullet("2. ValidationSkill - ValidationAgent (LangGraph); halt if decision == stop")
    pdf.bullet("3. CausalEvaluationSkill - uplift / uncertainty / directions (stub)")
    pdf.bullet("4. ExperimentGenerationSkill - propose candidate experiments")
    pdf.bullet("5. RecommendationSkill - RecommendationAgent (LangGraph); rank & explain")
    pdf.body("Output: OrchestrationResult with schema_version v1.0, validation_report, recommendation.")

    pdf.add_page()
    pdf.section_title("4. API endpoints")
    pdf.bullet("GET /health - health check")
    pdf.bullet("POST /validate/{experiment_id}?objective=... - validation only")
    pdf.bullet("POST /recommend/{experiment_id}?objective=... - evaluation + generation + recommendation")
    pdf.bullet("POST /orchestrate/{experiment_id}?objective=... - full pipeline")
    pdf.body("Run API: uvicorn src.api.main:app --reload --host 127.0.0.1 --port 8000")

    pdf.section_title("5. Skills summary")
    pdf.subsection("RetrievalSkill (Workstream A - stub)")
    pdf.body("Returns context dict: experiment, arms, metrics, memory. Target: Parquet/SQL warehouse.")

    pdf.subsection("ValidationSkill -> ValidationAgent (Workstream B)")
    pdf.body("LangGraph nodes: structural -> metrics -> benchmark -> world_spec -> decide -> llm_diagnostics")
    pdf.bullet("structural: traffic split, arms present/unique")
    pdf.bullet("metrics: sample floors, multi-arm, retention spread")
    pdf.bullet("benchmark: synthetic_env parquet checks (if files exist)")
    pdf.bullet("world_spec: configs/world_spec.yaml constraints as WARNINGS")
    pdf.bullet("decide: go / caution / stop (2+ errors -> stop)")
    pdf.bullet("llm_diagnostics: template or optional LLM summary")
    pdf.body("Output: ValidationReport - decision, issues, warnings, checks, diagnostics_summary.")

    pdf.subsection("CausalEvaluationSkill (Workstream C - stub)")
    pdf.body("Returns estimated_lift, uncertainty, ranked_directions. Marked _stub: True.")

    pdf.subsection("ExperimentGenerationSkill (Workstream D - input)")
    pdf.body("Produces 2 RecommendationCandidate objects with metric_stub for ranking demos.")

    pdf.subsection("RecommendationSkill -> RecommendationAgent (Workstream D)")
    pdf.body("LangGraph nodes: prepare -> score -> rank -> explain")
    pdf.bullet("Scoring: lift_aware_v1 = retention - lambda * sqrt(variance) + uncertainty_bonus + lift")
    pdf.bullet("Outputs score_components per candidate for explainability")
    pdf.bullet("Optional LLM explanation for top pick")
    pdf.body("Output: RecommendationReport - top_recommendation, ranked_candidates, explanation.")

    pdf.add_page()
    pdf.section_title("6. Decision policies")
    pdf.subsection("Validation (B)")
    pdf.bullet("error severity -> issues[] -> can cause stop")
    pdf.bullet("warning severity -> warnings[] -> caution only, never stop alone")
    pdf.bullet("stop: 2+ errors | caution: 1 error or any warnings | go: clean")

    pdf.subsection("Recommendation (D)")
    pdf.body("Does not halt pipeline. Always returns ranked list; may warn on degenerate input.")

    pdf.section_title("7. GitHub branches")
    pdf.bullet("experimentation/validation-agent - Workstream B (validation agent + docs)")
    pdf.bullet("experimentation/recommendation-agent - Workstream D + B/E tests (most complete)")
    pdf.bullet("dev/experimentation-plan - shared experimentation roadmap")
    pdf.bullet("main - baseline (agent branches not merged yet)")
    pdf.body("Suggested merge: validation-agent -> recommendation-agent -> dev/experimentation-plan -> main")

    pdf.section_title("8. Environment variables")
    pdf.bullet("BENCHMARK_DATA_DIR - path to benchmark parquets")
    pdf.bullet("ENABLE_VALIDATION_LLM / ENABLE_RECOMMENDATION_LLM - optional LLM narratives")
    pdf.bullet("LANGCHAIN_API_KEY / LANGCHAIN_TRACING_V2 - LangSmith tracing")
    pdf.bullet("RECOMMENDATION_VARIANCE_LAMBDA (default 0.2)")
    pdf.bullet("RECOMMENDATION_UNCERTAINTY_WEIGHT (default 0.2)")

    pdf.section_title("9. Setup")
    pdf.bullet("python3 -m venv .venv && source .venv/bin/activate")
    pdf.bullet("pip install -e .   (requires Python >= 3.10)")
    pdf.bullet("pip install -e \".[llm]\"  - optional OpenAI explanations")
    pdf.bullet("cp .env.example .env")
    pdf.bullet("Generate benchmarks: python -c \"from synthetic_env.pipeline import run_generation; run_generation(output_dir='synthetic_env/benchmarks/generated_sanity_calibrated')\"")

    pdf.section_title("10. Testing")
    pdf.bullet("pytest tests/ -q - full unit suite")
    pdf.bullet("tests/test_validation_agent.py - validation agent")
    pdf.bullet("tests/test_recommendation_agent.py - recommendation agent")
    pdf.bullet("tests/test_workstream_be_contracts.py - schema + non-zero outputs + LangGraph (B & E)")
    pdf.bullet("tests/test_smoke.py - end-to-end orchestrator")
    pdf.body("Last verified: 26 tests passed (tests/ + synthetic_env/tests/).")

    pdf.section_title("11. Team workstream map")
    pdf.bullet("A - Data / benchmark inputs: RetrievalSkill + synthetic_env")
    pdf.bullet("B - Validation: ValidationAgent")
    pdf.bullet("C - Causal evaluation: CausalEvaluationSkill (stub)")
    pdf.bullet("D - Recommendation: ExperimentGenerationSkill + RecommendationAgent")
    pdf.bullet("E - Integration: Orchestrator, FastAPI, LangGraph wiring, schema_version, tests")

    pdf.section_title("12. Further reading (in repo)")
    pdf.bullet("docs/validation_agent.md")
    pdf.bullet("docs/recommendation_agent.md")
    pdf.bullet("docs/EXPERIMENTATION_DEV_PLAN.md")
    pdf.bullet("docs/architecture.md")
    pdf.bullet("ARCHITECTURE.md (capstone KB)")

    return pdf


def main() -> None:
    pdf = build_pdf()
    for path in OUTPUT_PATHS:
        path.parent.mkdir(parents=True, exist_ok=True)
        pdf.output(str(path))
        print(f"Wrote: {path}")


if __name__ == "__main__":
    main()
