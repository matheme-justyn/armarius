"""DeepEval evaluation for agent workflow assessment.

Evaluates Orchestrator → Agent execution chains for:
- Tool Correctness: Are the right agents called?
- Task Completion: Does the workflow achieve the goal?
- Step Efficiency: Is the execution optimal?
"""

import json
from pathlib import Path
from typing import List, Dict, Any
import sys

try:
    from deepeval import evaluate
    from deepeval.metrics import GEval
    from deepeval.test_case import LLMTestCase, LLMTestCaseParams
except ImportError:
    print("ERROR: deepeval not installed. Run: uv pip install deepeval")
    sys.exit(1)

from armarius.agents import Orchestrator, QueryAgent, CompareAgent, SummarizeAgent, CitationAgent
from armarius.storage import SemanticSearch, Embedder, VectorStore


class DeepEvalEvaluator:
    def __init__(self):
        self.embedder = Embedder()
        self.vector_store = VectorStore(embedding_dim=self.embedder.dimension)
        self.search = SemanticSearch(embedder=self.embedder, vector_store=self.vector_store)
        
        self.query_agent = QueryAgent(self.search)
        self.compare_agent = CompareAgent(self.vector_store)
        self.summarize_agent = SummarizeAgent()
        self.citation_agent = CitationAgent(screenshot_dir=Path.home() / ".armarius" / "screenshots")
        
        self.orchestrator = Orchestrator(
            query_agent=self.query_agent,
            compare_agent=self.compare_agent,
            summarize_agent=self.summarize_agent,
            citation_agent=self.citation_agent,
        )
        
        self.tool_correctness_metric = GEval(
            name="Tool Correctness",
            criteria="Verify that the correct agents were called in the right sequence",
            evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT, LLMTestCaseParams.EXPECTED_OUTPUT],
        )
        
        self.task_completion_metric = GEval(
            name="Task Completion",
            criteria="Check if the workflow achieved its stated goal completely",
            evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT],
        )
    
    def create_test_cases(self) -> List[LLMTestCase]:
        test_cases = [
            LLMTestCase(
                input="Find information about transformer architecture",
                actual_output=str(self.orchestrator.process_query(
                    "transformer architecture",
                    workflow="search_and_cite"
                )),
                expected_output="Should call QueryAgent → CitationAgent",
            ),
            LLMTestCase(
                input="Compare attention mechanisms across documents",
                actual_output=str(self.orchestrator.process_query(
                    "attention mechanism",
                    workflow="compare_and_cite"
                )),
                expected_output="Should call QueryAgent → CompareAgent → CitationAgent",
            ),
            LLMTestCase(
                input="Summarize deep learning concepts",
                actual_output=str(self.orchestrator.process_query(
                    "deep learning",
                    workflow="summarize_and_cite"
                )),
                expected_output="Should call QueryAgent → SummarizeAgent → CitationAgent",
            ),
        ]
        return test_cases
    
    def evaluate(self) -> Dict[str, Any]:
        print("🔍 Creating test cases for DeepEval...")
        test_cases = self.create_test_cases()
        
        print("📊 Evaluating Tool Correctness...")
        tool_results = evaluate(test_cases, [self.tool_correctness_metric])
        
        print("📊 Evaluating Task Completion...")
        task_results = evaluate(test_cases, [self.task_completion_metric])
        
        return {
            "framework": "deepeval",
            "metrics": {
                "tool_correctness": float(tool_results[0].score) if tool_results else 0.0,
                "task_completion": float(task_results[0].score) if task_results else 0.0,
            },
            "test_cases": len(test_cases),
        }


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Run DeepEval evaluation")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("evals/results/deepeval_results.json"),
        help="Output path for results"
    )
    
    args = parser.parse_args()
    
    evaluator = DeepEvalEvaluator()
    results = evaluator.evaluate()
    
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✅ DeepEval evaluation complete!")
    print(f"📊 Tool Correctness: {results['metrics']['tool_correctness']:.3f}")
    print(f"📊 Task Completion: {results['metrics']['task_completion']:.3f}")
    print(f"💾 Results saved to: {args.output}")


if __name__ == "__main__":
    main()
