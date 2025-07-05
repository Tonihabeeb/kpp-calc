#!/usr/bin/env python3
"""
DeepSource Analysis Runner for KPP Simulator
Automates static code analysis and applies fixes.
"""

import subprocess
import json
import os
import sys
import logging
from typing import Dict, List, Any
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DeepSourceAnalyzer:
    """DeepSource analysis automation for KPP Simulator."""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.analysis_results = {}
        self.fixes_applied = []
        self.critical_issues = []
        
    def check_deepsource_installation(self) -> bool:
        """Check if DeepSource CLI is installed."""
        try:
            result = subprocess.run(
                ["deepsource", "--version"],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            if result.returncode == 0:
                logger.info(f"DeepSource CLI found: {result.stdout.strip()}")
                return True
            else:
                logger.error("DeepSource CLI not found or not working")
                return False
        except FileNotFoundError:
            logger.error("DeepSource CLI not installed")
            return False
    
    def install_deepsource(self) -> bool:
        """Install DeepSource CLI if not present."""
        try:
            logger.info("Installing DeepSource CLI...")
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "deepsource"],
                check=True,
                cwd=self.project_root
            )
            logger.info("DeepSource CLI installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install DeepSource: {e}")
            return False
    
    def run_analysis(self) -> Dict[str, Any]:
        """Run DeepSource analysis on the codebase."""
        logger.info("Running DeepSource analysis...")
        
        try:
            # Run analysis
            result = subprocess.run(
                ["deepsource", "analyze", "--output-format", "json"],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            if result.returncode == 0:
                # Parse JSON output
                analysis_data = json.loads(result.stdout)
                self.analysis_results = analysis_data
                
                # Extract issues
                issues = analysis_data.get("issues", [])
                logger.info(f"Found {len(issues)} issues")
                
                # Categorize issues
                self._categorize_issues(issues)
                
                return analysis_data
            else:
                logger.error(f"DeepSource analysis failed: {result.stderr}")
                return {}
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse DeepSource output: {e}")
            return {}
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            return {}
    
    def _categorize_issues(self, issues: List[Dict[str, Any]]):
        """Categorize issues by severity and type."""
        for issue in issues:
            issue_type = issue.get("issue_type", "")
            severity = issue.get("severity", "medium")
            
            # Critical issues that need immediate attention
            if severity == "high" or "security" in issue_type.lower():
                self.critical_issues.append(issue)
            
            # Log issue details
            logger.info(f"Issue: {issue.get('title', 'Unknown')} - {severity}")
    
    def apply_autofixes(self) -> List[str]:
        """Apply automatic fixes for issues that can be auto-fixed."""
        logger.info("Applying automatic fixes...")
        
        try:
            # Run autofix
            result = subprocess.run(
                ["deepsource", "fix"],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            if result.returncode == 0:
                # Parse fixes applied
                fixes = self._parse_fixes_output(result.stdout)
                self.fixes_applied = fixes
                logger.info(f"Applied {len(fixes)} automatic fixes")
                return fixes
            else:
                logger.error(f"Autofix failed: {result.stderr}")
                return []
                
        except Exception as e:
            logger.error(f"Autofix failed: {e}")
            return []
    
    def _parse_fixes_output(self, output: str) -> List[str]:
        """Parse the output of the fix command."""
        fixes = []
        lines = output.split('\n')
        
        for line in lines:
            if "Fixed" in line or "Applied" in line:
                fixes.append(line.strip())
        
        return fixes
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive analysis report."""
        total_issues = len(self.analysis_results.get("issues", []))
        critical_count = len(self.critical_issues)
        fixes_count = len(self.fixes_applied)
        
        report = {
            "summary": {
                "total_issues": total_issues,
                "critical_issues": critical_count,
                "autofixes_applied": fixes_count,
                "remaining_issues": total_issues - fixes_count
            },
            "critical_issues": [
                {
                    "title": issue.get("title", "Unknown"),
                    "file": issue.get("file", "Unknown"),
                    "line": issue.get("line", 0),
                    "severity": issue.get("severity", "medium"),
                    "issue_type": issue.get("issue_type", "unknown"),
                    "description": issue.get("description", "No description")
                }
                for issue in self.critical_issues
            ],
            "applied_fixes": self.fixes_applied,
            "recommendations": self._generate_recommendations()
        }
        
        return report
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on analysis results."""
        recommendations = []
        
        # Check for common KPP simulator issues
        issues = self.analysis_results.get("issues", [])
        
        # Memory management issues
        memory_issues = [i for i in issues if "memory" in i.get("title", "").lower()]
        if memory_issues:
            recommendations.append("Implement memory management for large state dictionaries")
        
        # Thread safety issues
        thread_issues = [i for i in issues if "thread" in i.get("title", "").lower() or "global" in i.get("title", "").lower()]
        if thread_issues:
            recommendations.append("Add thread safety to global state management")
        
        # Exception handling issues
        exception_issues = [i for i in issues if "exception" in i.get("title", "").lower()]
        if exception_issues:
            recommendations.append("Add comprehensive exception handling in simulation engine")
        
        # Performance issues
        performance_issues = [i for i in issues if "performance" in i.get("title", "").lower()]
        if performance_issues:
            recommendations.append("Optimize performance-critical functions")
        
        return recommendations
    
    def save_report(self, report: Dict[str, Any], filename: str = "deepsource_report.json"):
        """Save analysis report to file."""
        try:
            with open(filename, 'w') as f:
                json.dump(report, f, indent=2)
            logger.info(f"Report saved to {filename}")
        except Exception as e:
            logger.error(f"Failed to save report: {e}")

def main():
    """Main function to run DeepSource analysis."""
    logger.info("Starting DeepSource Analysis for KPP Simulator")
    
    # Initialize analyzer
    analyzer = DeepSourceAnalyzer()
    
    # Check/install DeepSource
    if not analyzer.check_deepsource_installation():
        if not analyzer.install_deepsource():
            logger.error("Failed to install DeepSource. Exiting.")
            return
    
    # Run analysis
    analysis_results = analyzer.run_analysis()
    
    if not analysis_results:
        logger.error("Analysis failed. Exiting.")
        return
    
    # Apply autofixes
    fixes = analyzer.apply_autofixes()
    
    # Generate report
    report = analyzer.generate_report()
    
    # Save report
    analyzer.save_report(report)
    
    # Print summary
    print("\n" + "="*60)
    print("DEEPSOURCE ANALYSIS REPORT")
    print("="*60)
    print(f"Total Issues Found: {report['summary']['total_issues']}")
    print(f"Critical Issues: {report['summary']['critical_issues']}")
    print(f"Autofixes Applied: {report['summary']['autofixes_applied']}")
    print(f"Remaining Issues: {report['summary']['remaining_issues']}")
    
    if report['critical_issues']:
        print("\nCRITICAL ISSUES:")
        for issue in report['critical_issues']:
            print(f"  - {issue['title']}")
            print(f"    File: {issue['file']}:{issue['line']}")
            print(f"    Type: {issue['issue_type']}")
            print(f"    Description: {issue['description']}")
            print()
    
    if report['recommendations']:
        print("RECOMMENDATIONS:")
        for rec in report['recommendations']:
            print(f"  - {rec}")
    
    print("\n" + "="*60)
    logger.info("DeepSource analysis completed")

if __name__ == "__main__":
    main() 