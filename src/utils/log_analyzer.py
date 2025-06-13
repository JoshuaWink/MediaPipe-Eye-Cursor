"""
Log Analyzer for ModuLink Context Logs

Utilities to analyze, replay, and generate test data from comprehensive context logs.
"""

import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import glob

class ContextLogAnalyzer:
    """Analyzer for ModuLink context logs."""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = log_dir
    
    def get_log_files(self) -> List[str]:
        """Get all context log files."""
        pattern = os.path.join(self.log_dir, "context_*.jsonl")
        return sorted(glob.glob(pattern))
    
    def load_log_entries(self, log_file: str) -> List[Dict[str, Any]]:
        """Load all entries from a log file."""
        entries = []
        try:
            with open(log_file, 'r') as f:
                for line in f:
                    if line.strip():
                        entries.append(json.loads(line))
        except Exception as e:
            print(f"Error loading log file {log_file}: {e}")
        return entries
    
    def analyze_execution(self, log_file: str) -> Dict[str, Any]:
        """Analyze a single execution log."""
        entries = self.load_log_entries(log_file)
        
        if not entries:
            return {"error": "No entries found"}
        
        analysis = {
            "log_file": log_file,
            "execution_id": entries[0].get("execution_id", "unknown"),
            "total_entries": len(entries),
            "start_time": entries[0].get("timestamp"),
            "end_time": entries[-1].get("timestamp"),
            "chains_executed": [],
            "links_executed": [],
            "errors": [],
            "context_evolution": []
        }
        
        # Analyze entries
        for entry in entries:
            chain_name = entry.get("chain_name", "unknown")
            link_name = entry.get("link_name", "unknown")
            phase = entry.get("phase", "unknown")
            
            # Track chains
            if chain_name not in analysis["chains_executed"]:
                analysis["chains_executed"].append(chain_name)
            
            # Track links
            link_info = f"{chain_name}.{link_name}"
            if link_info not in analysis["links_executed"]:
                analysis["links_executed"].append(link_info)
            
            # Track errors
            if entry.get("error"):
                analysis["errors"].append({
                    "link": link_name,
                    "error": entry["error"],
                    "timestamp": entry["timestamp"]
                })
            
            # Track context evolution (keys added/removed)
            context_keys = list(entry.get("context", {}).keys())
            analysis["context_evolution"].append({
                "link": link_name,
                "phase": phase,
                "keys": context_keys,
                "key_count": len(context_keys)
            })
        
        return analysis
    
    def extract_test_data(self, log_file: str, link_name: str) -> List[Dict[str, Any]]:
        """Extract test data for a specific link from logs."""
        entries = self.load_log_entries(log_file)
        test_cases = []
        
        for i, entry in enumerate(entries):
            if entry.get("link_name") == link_name and entry.get("phase") == "before":
                # Find the corresponding "after" entry
                after_entry = None
                for j in range(i + 1, len(entries)):
                    if (entries[j].get("link_name") == link_name and 
                        entries[j].get("phase") == "after"):
                        after_entry = entries[j]
                        break
                
                if after_entry:
                    test_case = {
                        "link_name": link_name,
                        "input_context": entry["context"],
                        "expected_output": after_entry["context"],
                        "timestamp": entry["timestamp"],
                        "execution_id": entry["execution_id"]
                    }
                    test_cases.append(test_case)
        
        return test_cases
    
    def generate_test_file(self, log_file: str, link_name: str, output_file: str):
        """Generate a test file from logged data."""
        test_data = self.extract_test_data(log_file, link_name)
        
        if not test_data:
            print(f"No test data found for link '{link_name}' in {log_file}")
            return
        
        test_code = f'''"""
Auto-generated test data from context logs.

Source: {log_file}
Link: {link_name}
Generated: {datetime.now().isoformat()}
Test cases: {len(test_data)}
"""

import pytest
import json
from modulink import Ctx
from src.modulink_eye_tracker import {link_name}

class Test{link_name.title().replace('_', '')}FromLogs:
    """Test cases generated from actual execution logs."""
    
'''
        
        for i, test_case in enumerate(test_data):
            test_code += f'''
    @pytest.mark.asyncio
    async def test_{link_name}_case_{i + 1}(self):
        """Test case from execution {test_case["execution_id"][:8]}."""
        # Input context from logs
        input_ctx = {json.dumps(test_case["input_context"], indent=8)}
        
        # Execute the link
        result = await {link_name}(input_ctx)
        
        # Verify key outputs (customize as needed)
        expected_keys = {list(test_case["expected_output"].keys())}
        actual_keys = list(result.keys())
        
        # Check that all expected keys are present
        for key in expected_keys:
            assert key in actual_keys, f"Expected key '{{key}}' not found in result"
        
        # Add specific assertions based on your link's behavior
        # Example: assert result.get('status') == 'success'
'''
        
        # Write the test file
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w') as f:
            f.write(test_code)
        
        print(f"Generated test file: {output_file}")
        print(f"Test cases: {len(test_data)}")
    
    def replay_context(self, log_file: str, link_name: str) -> Dict[str, Any]:
        """Replay a context through the current implementation."""
        test_data = self.extract_test_data(log_file, link_name)
        
        if not test_data:
            return {"error": f"No test data found for link '{link_name}'"}
        
        # This would require importing and executing the actual link functions
        # For now, return the structure for manual replay
        return {
            "link_name": link_name,
            "test_cases_available": len(test_data),
            "sample_input": test_data[0]["input_context"] if test_data else None,
            "sample_expected": test_data[0]["expected_output"] if test_data else None
        }
    
    def print_summary(self, log_file: str):
        """Print a summary of the log analysis."""
        analysis = self.analyze_execution(log_file)
        
        print(f"\n📊 Log Analysis Summary")
        print(f"{'='*50}")
        print(f"Log File: {analysis['log_file']}")
        print(f"Execution ID: {analysis['execution_id']}")
        print(f"Total Entries: {analysis['total_entries']}")
        print(f"Start Time: {analysis['start_time']}")
        print(f"End Time: {analysis['end_time']}")
        print(f"Chains Executed: {', '.join(analysis['chains_executed'])}")
        print(f"Links Executed: {len(analysis['links_executed'])}")
        print(f"Errors: {len(analysis['errors'])}")
        
        if analysis['errors']:
            print(f"\n❌ Errors Found:")
            for error in analysis['errors']:
                print(f"  - {error['link']}: {error['error']['message']}")
        
        print(f"\n🔄 Context Evolution:")
        for evolution in analysis['context_evolution']:
            print(f"  {evolution['phase']} {evolution['link']}: {evolution['key_count']} keys")

def main():
    """Command line interface for log analysis."""
    import sys
    
    analyzer = ContextLogAnalyzer()
    log_files = analyzer.get_log_files()
    
    if not log_files:
        print("No log files found in logs/ directory")
        return
    
    print(f"Found {len(log_files)} log files:")
    for i, log_file in enumerate(log_files):
        print(f"  {i + 1}. {log_file}")
    
    # Use the most recent log file
    latest_log = log_files[-1]
    print(f"\nAnalyzing latest log: {latest_log}")
    
    analyzer.print_summary(latest_log)
    
    # Extract test data for a specific link if provided
    if len(sys.argv) > 1:
        link_name = sys.argv[1]
        test_data = analyzer.extract_test_data(latest_log, link_name)
        print(f"\n🧪 Test data for '{link_name}': {len(test_data)} cases")
        
        if test_data and len(sys.argv) > 2:
            output_file = sys.argv[2]
            analyzer.generate_test_file(latest_log, link_name, output_file)

if __name__ == "__main__":
    main()
