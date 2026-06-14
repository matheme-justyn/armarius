# Armarius Evaluation Framework

Comprehensive evaluation system for Armarius PDF agent system using three specialized frameworks:

## Frameworks

### 1. Ragas (RAG Quality)
Evaluates retrieval quality for QueryAgent and SummarizeAgent.

**Metrics:**
- **Faithfulness**: Are answers grounded in retrieved contexts?
- **Answer Relevance**: Do answers address the question?

**Usage:**
```bash
uv run python evals/ragas_eval.py --dataset evals/datasets/golden_qa.json
```

### 2. DeepEval (Agent Workflows)
Evaluates Orchestrator → Agent execution chains.

**Metrics:**
- **Tool Correctness**: Are the right agents called in sequence?
- **Task Completion**: Does the workflow achieve its goal?
- **Step Efficiency**: Is execution optimal?

**Usage:**
```bash
uv run python evals/deepeval_eval.py
```

### 3. Promptfoo (Security)
Tests MCP Server and CLI for vulnerabilities.

**Tests:**
- Prompt injection attacks
- PII leakage detection
- Harmful content generation

**Usage:**
```bash
npx promptfoo eval -c evals/promptfoo_eval.yaml
```

## Directory Structure

```
evals/
├── __init__.py
├── config.yaml          # Central configuration
├── datasets/
│   └── golden_qa.json   # Golden test dataset
├── ragas_eval.py        # Ragas evaluator
├── deepeval_eval.py     # DeepEval evaluator
├── promptfoo_eval.yaml  # Promptfoo config
├── report.py            # Combined report generator
└── results/             # Output directory
    ├── ragas_results.json
    ├── deepeval_results.json
    ├── promptfoo_results.json
    ├── combined_report.json
    └── combined_report.md
```

## Installation

```bash
# Install evaluation dependencies
uv pip install ragas deepeval datasets

# Install Promptfoo (requires Node.js)
npm install -g promptfoo
```

## Running All Evaluations

```bash
# 1. Run Ragas evaluation
uv run python evals/ragas_eval.py

# 2. Run DeepEval evaluation
uv run python evals/deepeval_eval.py

# 3. Run Promptfoo evaluation
npx promptfoo eval -c evals/promptfoo_eval.yaml

# 4. Generate combined report
uv run python evals/report.py
```

## Golden Dataset Format

```json
[
  {
    "question": "What is the transformer architecture?",
    "expected_answer": "Expected answer text...",
    "expected_sources": ["transformers.pdf"],
    "expected_pages": [0, 1]
  }
]
```

## Configuration

Edit `evals/config.yaml` to:
- Enable/disable specific evaluations
- Change evaluation models
- Configure output formats
- Set result directories

## Results

Results are saved to `evals/results/`:
- Individual JSON files per framework
- Combined JSON report with all metrics
- Combined Markdown report for readability

## Interpretation

### Good Scores
- **Faithfulness**: > 0.7 (answers grounded in context)
- **Answer Relevance**: > 0.8 (answers address question)
- **Tool Correctness**: > 0.9 (correct agent selection)
- **Task Completion**: > 0.85 (goals achieved)

### Red Flags
- **Security**: Any prompt injection success
- **PII**: Any personal data leakage
- **Tool Correctness**: < 0.7 (wrong agents called)
