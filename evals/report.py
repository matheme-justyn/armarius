"""Report aggregator for all evaluation frameworks.

Combines results from Ragas, DeepEval, and Promptfoo into unified report.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List


class EvaluationReport:
    def __init__(self, results_dir: Path = Path("evals/results")):
        self.results_dir = results_dir
        self.timestamp = datetime.now().isoformat()
    
    def load_results(self) -> Dict[str, Any]:
        results = {}
        
        ragas_file = self.results_dir / "ragas_results.json"
        if ragas_file.exists():
            with open(ragas_file, 'r') as f:
                results["ragas"] = json.load(f)
        
        deepeval_file = self.results_dir / "deepeval_results.json"
        if deepeval_file.exists():
            with open(deepeval_file, 'r') as f:
                results["deepeval"] = json.load(f)
        
        promptfoo_file = self.results_dir / "promptfoo_results.json"
        if promptfoo_file.exists():
            with open(promptfoo_file, 'r') as f:
                results["promptfoo"] = json.load(f)
        
        return results
    
    def generate_json_report(self, results: Dict[str, Any]) -> Dict[str, Any]:
        report = {
            "timestamp": self.timestamp,
            "summary": self._generate_summary(results),
            "detailed_results": results,
        }
        return report
    
    def _generate_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        summary = {}
        
        if "ragas" in results:
            ragas = results["ragas"]["metrics"]
            summary["rag_quality"] = {
                "faithfulness": ragas.get("faithfulness", 0),
                "answer_relevance": ragas.get("answer_relevance", 0),
                "avg_score": (ragas.get("faithfulness", 0) + ragas.get("answer_relevance", 0)) / 2,
            }
        
        if "deepeval" in results:
            deepeval = results["deepeval"]["metrics"]
            summary["agent_workflows"] = {
                "tool_correctness": deepeval.get("tool_correctness", 0),
                "task_completion": deepeval.get("task_completion", 0),
                "avg_score": (deepeval.get("tool_correctness", 0) + deepeval.get("task_completion", 0)) / 2,
            }
        
        if "promptfoo" in results:
            summary["security"] = {
                "status": "evaluated",
                "details": "See promptfoo_results.json"
            }
        
        return summary
    
    def generate_markdown_report(self, results: Dict[str, Any]) -> str:
        lines = [
            "# Armarius Evaluation Report",
            f"\nGenerated: {self.timestamp}\n",
            "## Executive Summary\n",
        ]
        
        summary = self._generate_summary(results)
        
        if "rag_quality" in summary:
            rag = summary["rag_quality"]
            lines.append("### RAG Quality (Ragas)")
            lines.append(f"- **Faithfulness**: {rag['faithfulness']:.3f}")
            lines.append(f"- **Answer Relevance**: {rag['answer_relevance']:.3f}")
            lines.append(f"- **Average Score**: {rag['avg_score']:.3f}\n")
        
        if "agent_workflows" in summary:
            agent = summary["agent_workflows"]
            lines.append("### Agent Workflows (DeepEval)")
            lines.append(f"- **Tool Correctness**: {agent['tool_correctness']:.3f}")
            lines.append(f"- **Task Completion**: {agent['task_completion']:.3f}")
            lines.append(f"- **Average Score**: {agent['avg_score']:.3f}\n")
        
        if "security" in summary:
            lines.append("### Security (Promptfoo)")
            lines.append(f"- **Status**: {summary['security']['status']}")
            lines.append(f"- **Details**: {summary['security']['details']}\n")
        
        lines.append("\n## Detailed Results\n")
        lines.append("See individual result files in `evals/results/`:\n")
        lines.append("- `ragas_results.json` - RAG quality metrics")
        lines.append("- `deepeval_results.json` - Agent workflow metrics")
        lines.append("- `promptfoo_results.json` - Security test results")
        
        return "\n".join(lines)
    
    def generate_report(self, output_format: str = "both"):
        print("📊 Loading evaluation results...")
        results = self.load_results()
        
        if not results:
            print("⚠️  No results found. Run evaluations first.")
            return
        
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        if output_format in ["json", "both"]:
            json_report = self.generate_json_report(results)
            json_path = self.results_dir / "combined_report.json"
            with open(json_path, 'w') as f:
                json.dump(json_report, f, indent=2)
            print(f"✅ JSON report saved to: {json_path}")
        
        if output_format in ["markdown", "both"]:
            md_report = self.generate_markdown_report(results)
            md_path = self.results_dir / "combined_report.md"
            with open(md_path, 'w') as f:
                f.write(md_report)
            print(f"✅ Markdown report saved to: {md_path}")
        
        print("\n📈 Evaluation Summary:")
        summary = self._generate_summary(results)
        if "rag_quality" in summary:
            print(f"  RAG Quality: {summary['rag_quality']['avg_score']:.3f}")
        if "agent_workflows" in summary:
            print(f"  Agent Workflows: {summary['agent_workflows']['avg_score']:.3f}")
        if "security" in summary:
            print(f"  Security: {summary['security']['status']}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate combined evaluation report")
    parser.add_argument(
        "--format",
        choices=["json", "markdown", "both"],
        default="both",
        help="Output format"
    )
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=Path("evals/results"),
        help="Directory containing result files"
    )
    
    args = parser.parse_args()
    
    reporter = EvaluationReport(args.results_dir)
    reporter.generate_report(args.format)


if __name__ == "__main__":
    main()
