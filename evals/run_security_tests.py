"""Config-driven security test runner."""

import json
import yaml
from pathlib import Path
from typing import List, Dict, Any
import sys
import glob

try:
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    import torch
except ImportError:
    print("ERROR: transformers not installed. Run: uv pip install transformers torch")
    sys.exit(1)

try:
    from presidio_analyzer import AnalyzerEngine
    from presidio_anonymizer import AnonymizerEngine
except ImportError:
    print("ERROR: presidio not installed. Run: uv pip install presidio-analyzer presidio-anonymizer")
    sys.exit(1)

from armarius.client import ArmariusClient


class ConfigDrivenSecurityTester:
    def __init__(self, config_path: Path):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.cli = ArmariusClient()
        self.results = []
        
        if self.config['security_checks']['prompt_guard']['enabled']:
            print("🔐 Loading Prompt Guard...")
            model_name = self.config['security_checks']['prompt_guard']['model']
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
            self.model.eval()
        else:
            self.tokenizer = None
            self.model = None
        
        if self.config['security_checks']['presidio']['enabled']:
            print("🔐 Loading Presidio...")
            self.analyzer = AnalyzerEngine()
            self.anonymizer = AnonymizerEngine()
        else:
            self.analyzer = None
            self.anonymizer = None
    
    def resolve_pdf_files(self) -> List[Path]:
        pdf_paths = []
        for pattern in self.config['test_config']['pdf_files']:
            if '*' in pattern or '?' in pattern:
                pdf_paths.extend([Path(p) for p in glob.glob(pattern)])
            else:
                pdf_paths.append(Path(pattern))
        
        return [p.resolve() for p in pdf_paths if p.exists()]
    
    def check_injection(self, query: str) -> Dict[str, Any]:
        if not self.model:
            return {"is_malicious": False, "confidence": 0.0}
        
        inputs = self.tokenizer(query, return_tensors="pt", truncation=True, max_length=512)
        
        with torch.no_grad():
            outputs = self.model(**inputs)
            probs = torch.softmax(outputs.logits, dim=1)[0]
        
        labels = ["benign", "injection", "jailbreak"]
        prediction = labels[torch.argmax(probs).item()]
        confidence = float(torch.max(probs).item())
        
        threshold = self.config['security_checks']['prompt_guard']['confidence_threshold']
        
        return {
            "prediction": prediction,
            "confidence": confidence,
            "is_malicious": prediction in ["injection", "jailbreak"] and confidence >= threshold
        }
    
    def check_pii(self, text: str) -> Dict[str, Any]:
        if not self.analyzer:
            return {"has_pii": False, "count": 0, "detections": []}
        
        entities = self.config['security_checks']['presidio']['entities']
        threshold = self.config['security_checks']['presidio']['score_threshold']
        
        results = self.analyzer.analyze(text=text, language="en", entities=entities)
        
        filtered_results = [r for r in results if r.score >= threshold]
        
        detections = [
            {
                "type": r.entity_type,
                "text": text[r.start:r.end],
                "score": r.score
            }
            for r in filtered_results
        ]
        
        return {
            "has_pii": len(filtered_results) > 0,
            "count": len(filtered_results),
            "detections": detections
        }
    
    def test_query(
        self, 
        query: str, 
        should_block: bool,
        expect_no_pii: bool = False
    ) -> Dict[str, Any]:
        injection_check = self.check_injection(query)
        
        try:
            response = self.cli.query(query)
            response_text = str(response)
            error = None
        except Exception as e:
            response_text = None
            error = str(e)
        
        pii_check = self.check_pii(response_text) if response_text else None
        
        status = "PASS"
        reason = []
        
        if should_block:
            if not injection_check["is_malicious"]:
                status = "FAIL"
                reason.append("Expected injection detection but query passed")
        
        if expect_no_pii and pii_check and pii_check["has_pii"]:
            status = "FAIL"
            reason.append(f"PII detected: {pii_check['count']} entities")
        
        if not should_block and injection_check["is_malicious"]:
            status = "FAIL"
            reason.append("Benign query flagged as malicious (false positive)")
        
        return {
            "query": query,
            "expected_behavior": {
                "should_block": should_block,
                "expect_no_pii": expect_no_pii
            },
            "injection_check": injection_check,
            "pii_check": pii_check,
            "error": error,
            "status": status,
            "reason": reason if reason else None,
            "response_preview": response_text[:200] if response_text else None
        }
    
    def run_tests(self, pdf_files: List[Path]) -> Dict[str, Any]:
        print(f"\n📄 Indexing {len(pdf_files)} PDF(s)...")
        for pdf in pdf_files:
            print(f"  - {pdf.name}")
            self.cli.index(pdf)
        
        test_categories = self.config['test_categories']
        all_results = {}
        
        for category_name, category_config in test_categories.items():
            if not category_config.get('enabled', True):
                continue
            
            print(f"\n🧪 Testing {category_name}...")
            
            queries = category_config['queries']
            should_block = category_config.get('should_block', False)
            expect_no_pii = category_config.get('expect_no_pii', False)
            
            category_results = []
            for i, query in enumerate(queries, 1):
                print(f"  [{i}/{len(queries)}] {query[:60]}...")
                
                result = self.test_query(query, should_block, expect_no_pii)
                category_results.append(result)
                
                status_emoji = "✅" if result["status"] == "PASS" else "❌"
                print(f"    {status_emoji} {result['status']}")
                
                if result["reason"]:
                    for r in result["reason"]:
                        print(f"       → {r}")
            
            all_results[category_name] = category_results
        
        return all_results
    
    def generate_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        total = sum(len(cat) for cat in results.values())
        passed = sum(
            1 for cat_results in results.values()
            for r in cat_results
            if r["status"] == "PASS"
        )
        
        pii_leakage = sum(
            1 for cat_results in results.values()
            for r in cat_results
            if r["pii_check"] and r["pii_check"]["has_pii"]
        )
        
        injection_success = sum(
            1 for cat_results in results.values()
            for r in cat_results
            if r["expected_behavior"]["should_block"] 
            and not r["injection_check"]["is_malicious"]
        )
        
        benign_false_positives = sum(
            1 for cat_results in results.values()
            for r in cat_results
            if not r["expected_behavior"]["should_block"]
            and r["injection_check"]["is_malicious"]
        )
        
        thresholds = self.config['thresholds']
        
        return {
            "total_tests": total,
            "passed": passed,
            "failed": total - passed,
            "pass_rate": passed / total if total > 0 else 0,
            "pii_leakage_count": pii_leakage,
            "injection_success_count": injection_success,
            "benign_false_positives": benign_false_positives,
            "meets_thresholds": {
                "pass_rate": (passed / total) >= thresholds['min_pass_rate'],
                "pii_leakage": pii_leakage <= thresholds['max_pii_leakage'],
                "injection_success": injection_success <= thresholds['max_injection_success'],
                "false_positives": benign_false_positives <= thresholds['max_benign_false_positives']
            }
        }
    
    def generate_report(self, results: Dict[str, Any], summary: Dict[str, Any]) -> str:
        lines = [
            "# Armarius Security Test Report",
            "",
            "## Summary",
            "",
            f"- **Total Tests**: {summary['total_tests']}",
            f"- **Passed**: {summary['passed']} ✅",
            f"- **Failed**: {summary['failed']} ❌",
            f"- **Pass Rate**: {summary['pass_rate']:.1%}",
            "",
            "## Security Metrics",
            "",
            f"- **PII Leakage**: {summary['pii_leakage_count']} incidents",
            f"- **Injection Success**: {summary['injection_success_count']} attacks",
            f"- **False Positives**: {summary['benign_false_positives']} benign queries blocked",
            "",
            "## Threshold Compliance",
            ""
        ]
        
        for metric, passed in summary['meets_thresholds'].items():
            status = "✅ PASS" if passed else "❌ FAIL"
            lines.append(f"- **{metric.replace('_', ' ').title()}**: {status}")
        
        lines.extend([
            "",
            "## Results by Category",
            ""
        ])
        
        for category, cat_results in results.items():
            passed = sum(1 for r in cat_results if r["status"] == "PASS")
            total = len(cat_results)
            
            lines.append(f"### {category.replace('_', ' ').title()}")
            lines.append(f"- Tests: {total}")
            lines.append(f"- Passed: {passed}/{total}")
            lines.append("")
        
        return "\n".join(lines)
    
    def run(self):
        pdf_files = self.resolve_pdf_files()
        
        if not pdf_files:
            print("❌ No PDF files found")
            sys.exit(1)
        
        print(f"🔐 Armarius Security Test Suite (Config-Driven)")
        print(f"📄 Testing with {len(pdf_files)} PDF(s)")
        
        results = self.run_tests(pdf_files)
        summary = self.generate_summary(results)
        
        output_config = self.config['output']
        output_path = Path(output_config['path'])
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        full_results = {
            "config": str(self.config),
            "pdf_files": [str(p) for p in pdf_files],
            "summary": summary,
            "results": results
        }
        
        with open(output_path, 'w') as f:
            json.dump(full_results, f, indent=2)
        
        if output_config['report']['generate']:
            report = self.generate_report(results, summary)
            report_path = Path(output_config['report']['path'])
            with open(report_path, 'w') as f:
                f.write(report)
            print(f"\n📄 Report saved to: {report_path}")
        
        print("\n" + "="*60)
        print("📊 SECURITY TEST RESULTS")
        print("="*60)
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Passed: {summary['passed']} ✅")
        print(f"Failed: {summary['failed']} ❌")
        print(f"Pass Rate: {summary['pass_rate']:.1%}")
        print(f"\n💾 Results saved to: {output_path}")
        
        all_passed = all(summary['meets_thresholds'].values())
        sys.exit(0 if all_passed else 1)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Run security tests from config")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("evals/security_config.yaml"),
        help="Config file path"
    )
    
    args = parser.parse_args()
    
    if not args.config.exists():
        print(f"❌ Config file not found: {args.config}")
        sys.exit(1)
    
    tester = ConfigDrivenSecurityTester(args.config)
    tester.run()


if __name__ == "__main__":
    main()
