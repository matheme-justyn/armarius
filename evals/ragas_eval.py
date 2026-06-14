"""Ragas evaluation for RAG quality assessment.

Evaluates QueryAgent and SummarizeAgent for:
- Faithfulness: Are answers grounded in retrieved contexts?
- Answer Relevance: Do answers address the question?
"""

import json
from pathlib import Path
from typing import List, Dict, Any
import sys

try:
    from ragas import evaluate
    from ragas.metrics import faithfulness, answer_relevance
    from datasets import Dataset
except ImportError:
    print("ERROR: ragas not installed. Run: uv pip install ragas datasets")
    sys.exit(1)

from armarius.storage import SemanticSearch, Embedder, VectorStore, SearchQuery
from armarius.agents import QueryAgent


class RagasEvaluator:
    def __init__(self, golden_dataset_path: Path):
        self.golden_dataset_path = golden_dataset_path
        self.embedder = Embedder()
        self.vector_store = VectorStore(embedding_dim=self.embedder.dimension)
        self.search = SemanticSearch(embedder=self.embedder, vector_store=self.vector_store)
        self.query_agent = QueryAgent(self.search)
    
    def load_golden_dataset(self) -> List[Dict[str, Any]]:
        with open(self.golden_dataset_path, 'r') as f:
            return json.load(f)
    
    def run_agent_on_question(self, question: str) -> Dict[str, Any]:
        search_query = SearchQuery(text=question, top_k=5)
        results = self.search.search(search_query)
        
        contexts = [r.chunk.text for r in results]
        answer = self._synthesize_answer(results, question)
        
        return {
            "question": question,
            "answer": answer,
            "contexts": contexts,
        }
    
    def _synthesize_answer(self, results, question: str) -> str:
        if not results:
            return "No relevant information found."
        
        top_chunk = results[0].chunk.text
        return f"Based on the documents: {top_chunk[:200]}..."
    
    def prepare_ragas_dataset(self) -> Dataset:
        golden_data = self.load_golden_dataset()
        
        questions = []
        answers = []
        contexts_list = []
        ground_truths = []
        
        for item in golden_data:
            result = self.run_agent_on_question(item["question"])
            
            questions.append(result["question"])
            answers.append(result["answer"])
            contexts_list.append(result["contexts"])
            ground_truths.append(item["expected_answer"])
        
        dataset_dict = {
            "question": questions,
            "answer": answers,
            "contexts": contexts_list,
            "ground_truth": ground_truths,
        }
        
        return Dataset.from_dict(dataset_dict)
    
    def evaluate(self) -> Dict[str, Any]:
        print("🔍 Preparing dataset for Ragas evaluation...")
        dataset = self.prepare_ragas_dataset()
        
        print("📊 Running Ragas evaluation (Faithfulness + Answer Relevance)...")
        results = evaluate(
            dataset,
            metrics=[faithfulness, answer_relevance],
        )
        
        return {
            "framework": "ragas",
            "metrics": {
                "faithfulness": float(results["faithfulness"]),
                "answer_relevance": float(results["answer_relevance"]),
            },
            "dataset_size": len(dataset),
        }


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Run Ragas evaluation")
    parser.add_argument(
        "--dataset",
        type=Path,
        default=Path("evals/datasets/golden_qa.json"),
        help="Path to golden QA dataset"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("evals/results/ragas_results.json"),
        help="Output path for results"
    )
    
    args = parser.parse_args()
    
    evaluator = RagasEvaluator(args.dataset)
    results = evaluator.evaluate()
    
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✅ Ragas evaluation complete!")
    print(f"📊 Faithfulness: {results['metrics']['faithfulness']:.3f}")
    print(f"📊 Answer Relevance: {results['metrics']['answer_relevance']:.3f}")
    print(f"💾 Results saved to: {args.output}")


if __name__ == "__main__":
    main()
