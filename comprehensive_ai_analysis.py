#!/usr/bin/env python3
"""
Comprehensive AI Analysis for KPP Simulator
Combines DeepSource analysis with custom callback and endpoint analysis.
"""

import subprocess
import json
import os
import sys
import logging
import time
from pathlib import Path
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
import ast
import re

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class CallbackInfo:
    """Information about a callback"""
    name: str
    file_path: str
    line_number: int
    category: str
    priority: str
    description: str
    is_implemented: bool
    is_integrated: bool
    integration_status: str

@dataclass
class EndpointInfo:
    """Information about an endpoint"""
    path: str
    method: str
    file_path: str
    line_number: int
    description: str
    parameters: List[str]
    response_type: str
    is_implemented: bool
    is_tested: bool

@dataclass
class AnalysisResult:
    """Comprehensive analysis result"""
    callbacks: List[CallbackInfo]
    endpoints: List[EndpointInfo]
    code_quality: Dict[str, Any]
    integration_status: Dict[str, Any]
    recommendations: List[str]

class ComprehensiveAIAnalyzer:
    """Comprehensive AI analysis combining multiple tools"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.callbacks = []
        self.endpoints = []
        self.code_quality_results = {}
        self.integration_status = {}
        
    def run_comprehensive_analysis(self) -> AnalysisResult:
        """Run comprehensive analysis using all available tools"""
        logger.info("🤖 Starting Comprehensive AI Analysis")
        logger.info("=" * 80)
        
        start_time = time.time()
        
        # Phase 1: DeepSource Analysis
        logger.info("🔍 PHASE 1: DeepSource Code Quality Analysis")
        deepsource_results = self._run_deepsource_analysis()
        
        # Phase 2: Callback Analysis
        logger.info("📞 PHASE 2: Callback Integration Analysis")
        callback_results = self._analyze_callbacks()
        
        # Phase 3: Endpoint Analysis
        logger.info("🌐 PHASE 3: Endpoint Coverage Analysis")
        endpoint_results = self._analyze_endpoints()
        
        # Phase 4: Integration Analysis
        logger.info("🔗 PHASE 4: Integration Status Analysis")
        integration_results = self._analyze_integration_status()
        
        # Phase 5: Generate Recommendations
        logger.info("💡 PHASE 5: Generate AI Recommendations")
        recommendations = self._generate_ai_recommendations(
            deepsource_results, callback_results, endpoint_results, integration_results
        )
        
        analysis_time = time.time() - start_time
        
        logger.info(f"⏱️ Total Analysis Time: {analysis_time:.2f}s")
        
        return AnalysisResult(
            callbacks=callback_results,
            endpoints=endpoint_results,
            code_quality=deepsource_results,
            integration_status=integration_results,
            recommendations=recommendations
        )
    
    def _run_deepsource_analysis(self) -> Dict[str, Any]:
        """Run DeepSource analysis"""
        try:
            logger.info("  Running DeepSource analysis...")
            
            # Try to run DeepSource
            result = subprocess.run(
                [sys.executable, "-m", "deepsource", "analyze"],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            if result.returncode == 0:
                logger.info("  ✅ DeepSource analysis completed")
                return {
                    "status": "success",
                    "output": result.stdout,
                    "issues_found": self._parse_deepsource_output(result.stdout)
                }
            else:
                logger.warning("  ⚠️ DeepSource analysis failed, using fallback")
                return self._run_fallback_code_analysis()
                
        except Exception as e:
            logger.warning(f"  ⚠️ DeepSource error: {e}, using fallback")
            return self._run_fallback_code_analysis()
    
    def _run_fallback_code_analysis(self) -> Dict[str, Any]:
        """Run fallback code analysis when DeepSource is not available"""
        logger.info("  Running fallback code analysis...")
        
        # Analyze Python files for common issues
        python_files = list(self.project_root.rglob("*.py"))
        total_files = len(python_files)
        total_lines = 0
        syntax_errors = 0
        import_errors = 0
        
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    total_lines += len(content.splitlines())
                
                # Check for syntax errors
                try:
                    ast.parse(content)
                except SyntaxError:
                    syntax_errors += 1
                    
            except Exception:
                import_errors += 1
        
        return {
            "status": "fallback",
            "total_files": total_files,
            "total_lines": total_lines,
            "syntax_errors": syntax_errors,
            "import_errors": import_errors,
            "quality_score": max(0, 100 - (syntax_errors + import_errors) * 10)
        }
    
    def _parse_deepsource_output(self, output: str) -> List[Dict[str, Any]]:
        """Parse DeepSource output for issues"""
        issues = []
        lines = output.split('\n')
        
        for line in lines:
            if 'error' in line.lower() or 'warning' in line.lower():
                issues.append({
                    "type": "issue",
                    "message": line.strip(),
                    "severity": "error" if "error" in line.lower() else "warning"
                })
        
        return issues
    
    def _analyze_callbacks(self) -> List[CallbackInfo]:
        """Analyze callback implementation and integration"""
        logger.info("  Analyzing callback implementations...")
        
        callbacks = []
        
        # Define callback patterns to search for
        callback_patterns = [
            ("simulation/engine.py", [
                "trigger_emergency_stop", "apply_emergency_stop",
                "get_transient_status", "acknowledge_transient_event",
                "_init_with_new_config", "_init_with_legacy_params",
                "_get_time_step", "get_parameters", "set_parameters",
                "get_summary", "run", "stop", "set_chain_geometry",
                "initiate_startup", "get_physics_status",
                "disable_enhanced_physics", "get_enhanced_performance_metrics"
            ]),
            ("simulation/components/fluid.py", [
                "calculate_density", "apply_nanobubble_effects",
                "calculate_buoyant_force", "set_temperature"
            ]),
            ("simulation/components/environment.py", [
                "get_density", "get_viscosity"
            ]),
            ("simulation/components/pneumatics.py", [
                "calculate_buoyancy_change", "calculate_compression_work",
                "vent_air", "get_thermodynamic_cycle_analysis",
                "inject_air", "analyze_thermodynamic_cycle"
            ]),
            ("simulation/components/thermal.py", [
                "set_temperature", "calculate_isothermal_compression_work",
                "calculate_adiabatic_compression_work", "calculate_thermal_density_effect",
                "calculate_heat_exchange_rate", "set_ambient_temperature"
            ]),
            ("simulation/components/floater/thermal.py", [
                "calculate_thermal_expansion", "calculate_expansion_work"
            ]),
            ("simulation/components/chain.py", [
                "add_floaters", "synchronize"
            ]),
            ("simulation/components/sprocket.py", [
                "calculate_torque_from_chain_tension"
            ]),
            ("simulation/components/gearbox.py", [
                "get_input_power", "get_output_power"
            ]),
            ("simulation/components/one_way_clutch.py", [
                "_should_engage", "_calculate_transmitted_torque",
                "_calculate_engagement_losses"
            ]),
            ("simulation/components/flywheel.py", [
                "_calculate_friction_losses", "_calculate_windage_losses",
                "_track_energy_flow", "get_energy_efficiency",
                "calculate_pid_correction"
            ]),
            ("simulation/components/integrated_electrical_system.py", [
                "_update_performance_metrics", "_calculate_load_management",
                "_calculate_generator_frequency", "_get_comprehensive_state"
            ]),
            ("simulation/components/integrated_drivetrain.py", [
                "get_power_flow_summary"
            ]),
            ("simulation/components/advanced_generator.py", [
                "_calculate_electromagnetic_torque", "_calculate_losses",
                "_calculate_power_factor", "_estimate_efficiency",
                "_get_state_dict", "set_field_excitation", "set_user_load",
                "get_user_load", "_calculate_foc_torque", "set_foc_parameters",
                "enable_foc", "get_foc_status"
            ]),
            ("simulation/components/power_electronics.py", [
                "_check_protection_systems", "_update_synchronization",
                "_calculate_power_conversion", "_regulate_output_voltage",
                "_correct_power_factor", "set_power_demand", "disconnect",
                "reconnect", "apply_control_commands"
            ]),
            ("simulation/components/floater/pneumatic.py", [
                "update_injection", "start_venting", "update_venting"
            ]),
            ("simulation/components/floater/state_machine.py", [
                "_define_transitions", "_on_start_filling", "_on_filling_complete",
                "_on_start_venting", "_on_venting_complete"
            ]),
            ("simulation/components/floater/core.py", [
                "get_force", "is_filled", "volume", "area", "mass",
                "fill_progress", "state"
            ]),
            ("simulation/components/floater/validation.py", [
                "_define_constraints"
            ]),
            ("simulation/components/sensors.py", [
                "register", "poll"
            ])
        ]
        
        for file_path, callback_names in callback_patterns:
            full_path = self.project_root / file_path
            
            if full_path.exists():
                callbacks.extend(self._analyze_file_callbacks(full_path, callback_names))
            else:
                # File doesn't exist, mark callbacks as not implemented
                for callback_name in callback_names:
                    callbacks.append(CallbackInfo(
                        name=callback_name,
                        file_path=file_path,
                        line_number=0,
                        category=self._get_callback_category(callback_name),
                        priority=self._get_callback_priority(callback_name),
                        description=self._get_callback_description(callback_name),
                        is_implemented=False,
                        is_integrated=False,
                        integration_status="file_not_found"
                    ))
        
        logger.info(f"  ✅ Analyzed {len(callbacks)} callbacks")
        return callbacks
    
    def _analyze_file_callbacks(self, file_path: Path, callback_names: List[str]) -> List[CallbackInfo]:
        """Analyze callbacks in a specific file"""
        callbacks = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.splitlines()
            
            for callback_name in callback_names:
                line_number = self._find_function_line(content, callback_name)
                is_implemented = line_number > 0
                is_integrated = self._check_callback_integration(content, callback_name)
                
                callbacks.append(CallbackInfo(
                    name=callback_name,
                    file_path=str(file_path.relative_to(self.project_root)),
                    line_number=line_number,
                    category=self._get_callback_category(callback_name),
                    priority=self._get_callback_priority(callback_name),
                    description=self._get_callback_description(callback_name),
                    is_implemented=is_implemented,
                    is_integrated=is_integrated,
                    integration_status="integrated" if is_integrated else "not_integrated"
                ))
                
        except Exception as e:
            logger.warning(f"  ⚠️ Error analyzing {file_path}: {e}")
        
        return callbacks
    
    def _find_function_line(self, content: str, function_name: str) -> int:
        """Find the line number of a function definition"""
        lines = content.splitlines()
        
        for i, line in enumerate(lines, 1):
            if f"def {function_name}(" in line or f"async def {function_name}(" in line:
                return i
        
        return 0
    
    def _check_callback_integration(self, content: str, callback_name: str) -> bool:
        """Check if a callback is integrated with the callback manager"""
        # Look for integration patterns
        integration_patterns = [
            f"callback_integration_manager.register_callback",
            f"register_callback({callback_name}",
            f"CallbackInfo.*{callback_name}",
            f"@callback"
        ]
        
        for pattern in integration_patterns:
            if pattern in content:
                return True
        
        return False
    
    def _get_callback_category(self, callback_name: str) -> str:
        """Get the category of a callback based on its name"""
        if "emergency" in callback_name or "safety" in callback_name:
            return "emergency"
        elif "transient" in callback_name:
            return "transient"
        elif "config" in callback_name or "init" in callback_name or "param" in callback_name:
            return "config"
        elif "run" in callback_name or "stop" in callback_name or "start" in callback_name:
            return "simulation"
        else:
            return "performance"
    
    def _get_callback_priority(self, callback_name: str) -> str:
        """Get the priority of a callback based on its name"""
        if "emergency" in callback_name or "safety" in callback_name:
            return "CRITICAL"
        elif "run" in callback_name or "stop" in callback_name or "init" in callback_name:
            return "HIGH"
        elif "get_" in callback_name or "set_" in callback_name:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _get_callback_description(self, callback_name: str) -> str:
        """Get a description for a callback based on its name"""
        descriptions = {
            "trigger_emergency_stop": "Trigger emergency shutdown procedure",
            "apply_emergency_stop": "Apply emergency stop procedures",
            "get_transient_status": "Get transient event status",
            "acknowledge_transient_event": "Acknowledge transient events",
            "calculate_density": "Calculate fluid density",
            "apply_nanobubble_effects": "Apply nanobubble physics effects",
            "calculate_buoyant_force": "Calculate buoyant force",
            "set_temperature": "Set temperature value",
            "get_density": "Get environmental density",
            "get_viscosity": "Get fluid viscosity",
            "calculate_compression_work": "Calculate compression work",
            "vent_air": "Vent air from system",
            "inject_air": "Inject air into system",
            "run": "Start simulation",
            "stop": "Stop simulation",
            "get_parameters": "Get simulation parameters",
            "set_parameters": "Set simulation parameters"
        }
        
        return descriptions.get(callback_name, f"Callback: {callback_name}")
    
    def _analyze_endpoints(self) -> List[EndpointInfo]:
        """Analyze API endpoints"""
        logger.info("  Analyzing API endpoints...")
        
        endpoints = []
        
        # Define endpoint patterns to search for
        endpoint_patterns = [
            ("app.py", [
                ("/", "GET", "Main application route"),
                ("/health", "GET", "Health check endpoint"),
                ("/api/status", "GET", "API status endpoint")
            ]),
            ("routes/simulation_api.py", [
                ("/api/simulation/start", "POST", "Start simulation"),
                ("/api/simulation/stop", "POST", "Stop simulation"),
                ("/api/simulation/status", "GET", "Get simulation status"),
                ("/api/simulation/parameters", "GET", "Get simulation parameters"),
                ("/api/simulation/parameters", "POST", "Set simulation parameters"),
                ("/api/simulation/data", "GET", "Get simulation data"),
                ("/api/simulation/export", "GET", "Export simulation data")
            ]),
            ("routes/export_routes.py", [
                ("/api/export/csv", "GET", "Export data as CSV"),
                ("/api/export/json", "GET", "Export data as JSON"),
                ("/api/export/pdf", "GET", "Export data as PDF")
            ]),
            ("routes/stream.py", [
                ("/api/stream/simulation", "GET", "Stream simulation data"),
                ("/api/stream/performance", "GET", "Stream performance data"),
                ("/api/stream/events", "GET", "Stream system events")
            ])
        ]
        
        for file_path, endpoint_definitions in endpoint_patterns:
            full_path = self.project_root / file_path
            
            if full_path.exists():
                endpoints.extend(self._analyze_file_endpoints(full_path, endpoint_definitions))
            else:
                # File doesn't exist, mark endpoints as not implemented
                for path, method, description in endpoint_definitions:
                    endpoints.append(EndpointInfo(
                        path=path,
                        method=method,
                        file_path=file_path,
                        line_number=0,
                        description=description,
                        parameters=[],
                        response_type="application/json",
                        is_implemented=False,
                        is_tested=False
                    ))
        
        logger.info(f"  ✅ Analyzed {len(endpoints)} endpoints")
        return endpoints
    
    def _analyze_file_endpoints(self, file_path: Path, endpoint_definitions: List[Tuple[str, str, str]]) -> List[EndpointInfo]:
        """Analyze endpoints in a specific file"""
        endpoints = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.splitlines()
            
            for path, method, description in endpoint_definitions:
                line_number = self._find_endpoint_line(content, path, method)
                is_implemented = line_number > 0
                parameters = self._extract_endpoint_parameters(content, path, method)
                is_tested = self._check_endpoint_testing(path, method)
                
                endpoints.append(EndpointInfo(
                    path=path,
                    method=method,
                    file_path=str(file_path.relative_to(self.project_root)),
                    line_number=line_number,
                    description=description,
                    parameters=parameters,
                    response_type="application/json",
                    is_implemented=is_implemented,
                    is_tested=is_tested
                ))
                
        except Exception as e:
            logger.warning(f"  ⚠️ Error analyzing {file_path}: {e}")
        
        return endpoints
    
    def _find_endpoint_line(self, content: str, path: str, method: str) -> int:
        """Find the line number of an endpoint definition"""
        lines = content.splitlines()
        
        for i, line in enumerate(lines, 1):
            if f"@{method.lower()}" in line.lower() and path in line:
                return i
            elif f"route('{path}')" in line or f'route("{path}")' in line:
                return i
        
        return 0
    
    def _extract_endpoint_parameters(self, content: str, path: str, method: str) -> List[str]:
        """Extract parameters from an endpoint"""
        # This is a simplified extraction - in practice you'd need more sophisticated parsing
        parameters = []
        
        # Look for common parameter patterns
        if "request.json" in content:
            parameters.append("JSON body")
        if "request.args" in content:
            parameters.append("Query parameters")
        if "request.form" in content:
            parameters.append("Form data")
        
        return parameters
    
    def _check_endpoint_testing(self, path: str, method: str) -> bool:
        """Check if an endpoint has tests"""
        # Simplified check - just look for common test patterns
        test_patterns = [
            "test_",
            "endpoint_test",
            "api_test"
        ]
        
        # Check if any test files exist in the project
        try:
            test_files = list(self.project_root.glob("**/test_*.py"))
            if test_files:
                return True
        except:
            pass
        
        return False
    
    def _analyze_integration_status(self) -> Dict[str, Any]:
        """Analyze overall integration status"""
        logger.info("  Analyzing integration status...")
        
        # Count implemented vs non-implemented callbacks
        implemented_callbacks = sum(1 for c in self.callbacks if c.is_implemented)
        integrated_callbacks = sum(1 for c in self.callbacks if c.is_integrated)
        implemented_endpoints = sum(1 for e in self.endpoints if e.is_implemented)
        tested_endpoints = sum(1 for e in self.endpoints if e.is_tested)
        
        return {
            "callbacks": {
                "total": len(self.callbacks),
                "implemented": implemented_callbacks,
                "integrated": integrated_callbacks,
                "implementation_rate": implemented_callbacks / max(len(self.callbacks), 1) * 100,
                "integration_rate": integrated_callbacks / max(len(self.callbacks), 1) * 100
            },
            "endpoints": {
                "total": len(self.endpoints),
                "implemented": implemented_endpoints,
                "tested": tested_endpoints,
                "implementation_rate": implemented_endpoints / max(len(self.endpoints), 1) * 100,
                "testing_rate": tested_endpoints / max(len(self.endpoints), 1) * 100
            },
            "overall_status": {
                "callback_completion": implemented_callbacks / max(len(self.callbacks), 1) * 100,
                "endpoint_completion": implemented_endpoints / max(len(self.endpoints), 1) * 100,
                "integration_completion": integrated_callbacks / max(len(self.callbacks), 1) * 100
            }
        }
    
    def _generate_ai_recommendations(self, deepsource_results: Dict, callback_results: List[CallbackInfo], 
                                   endpoint_results: List[EndpointInfo], integration_results: Dict) -> List[str]:
        """Generate AI-powered recommendations"""
        logger.info("  Generating AI recommendations...")
        
        recommendations = []
        
        # Code quality recommendations
        if deepsource_results.get("status") == "success":
            issues = deepsource_results.get("issues_found", [])
            if len(issues) > 10:
                recommendations.append("🔧 Address code quality issues identified by DeepSource")
        else:
            quality_score = deepsource_results.get("quality_score", 0)
            if quality_score < 90:
                recommendations.append("🔧 Improve code quality score (currently {quality_score}%)")
        
        # Callback recommendations
        callback_stats = integration_results["callbacks"]
        if callback_stats["implementation_rate"] < 100:
            recommendations.append(f"📞 Complete callback implementation ({callback_stats['implementation_rate']:.1f}% done)")
        
        if callback_stats["integration_rate"] < 100:
            recommendations.append(f"🔗 Complete callback integration ({callback_stats['integration_rate']:.1f}% done)")
        
        # Endpoint recommendations
        endpoint_stats = integration_results["endpoints"]
        if endpoint_stats["implementation_rate"] < 100:
            recommendations.append(f"🌐 Complete endpoint implementation ({endpoint_stats['implementation_rate']:.1f}% done)")
        
        if endpoint_stats["testing_rate"] < 100:
            recommendations.append(f"🧪 Add endpoint testing ({endpoint_stats['testing_rate']:.1f}% tested)")
        
        # Performance recommendations
        high_complexity_callbacks = [c for c in callback_results if c.is_implemented and "calculate" in c.name.lower()]
        if len(high_complexity_callbacks) > 20:
            recommendations.append("⚡ Optimize performance-critical callbacks")
        
        # Security recommendations
        security_endpoints = [e for e in endpoint_results if "admin" in e.path.lower() or "config" in e.path.lower()]
        if security_endpoints and not all(e.is_tested for e in security_endpoints):
            recommendations.append("🔒 Add security testing for administrative endpoints")
        
        # Architecture recommendations
        if len(callback_results) > 100:
            recommendations.append("🏗️ Consider modularizing callback architecture for better maintainability")
        
        if len(endpoint_results) > 50:
            recommendations.append("🌐 Implement API versioning for better compatibility")
        
        return recommendations
    
    def save_comprehensive_report(self, result: AnalysisResult, filename: str = "comprehensive_ai_analysis_report.json"):
        """Save comprehensive analysis report"""
        try:
            report = {
                "summary": {
                    "analysis_timestamp": time.time(),
                    "total_callbacks": len(result.callbacks),
                    "total_endpoints": len(result.endpoints),
                    "code_quality_status": result.code_quality.get("status", "unknown"),
                    "integration_completion": result.integration_status["overall_status"]["integration_completion"]
                },
                "callbacks": [
                    {
                        "name": c.name,
                        "file_path": c.file_path,
                        "line_number": c.line_number,
                        "category": c.category,
                        "priority": c.priority,
                        "description": c.description,
                        "is_implemented": c.is_implemented,
                        "is_integrated": c.is_integrated,
                        "integration_status": c.integration_status
                    }
                    for c in result.callbacks
                ],
                "endpoints": [
                    {
                        "path": e.path,
                        "method": e.method,
                        "file_path": e.file_path,
                        "line_number": e.line_number,
                        "description": e.description,
                        "parameters": e.parameters,
                        "response_type": e.response_type,
                        "is_implemented": e.is_implemented,
                        "is_tested": e.is_tested
                    }
                    for e in result.endpoints
                ],
                "code_quality": result.code_quality,
                "integration_status": result.integration_status,
                "recommendations": result.recommendations
            }
            
            with open(filename, 'w') as f:
                json.dump(report, f, indent=2)
            
            logger.info(f"📄 Comprehensive report saved to {filename}")
            
        except Exception as e:
            logger.error(f"❌ Failed to save report: {e}")

def main():
    """Main function to run comprehensive AI analysis"""
    logger.info("🤖 Starting Comprehensive AI Analysis for KPP Simulator")
    logger.info("=" * 80)
    
    # Initialize analyzer
    analyzer = ComprehensiveAIAnalyzer()
    
    # Run comprehensive analysis
    result = analyzer.run_comprehensive_analysis()
    
    # Save report
    analyzer.save_comprehensive_report(result)
    
    # Print comprehensive summary
    print("\n" + "="*80)
    print("🤖 COMPREHENSIVE AI ANALYSIS RESULTS")
    print("="*80)
    
    # Callback summary
    callback_stats = result.integration_status["callbacks"]
    print(f"📞 CALLBACK ANALYSIS:")
    print(f"  Total Callbacks: {callback_stats['total']}")
    print(f"  Implemented: {callback_stats['implemented']} ({callback_stats['implementation_rate']:.1f}%)")
    print(f"  Integrated: {callback_stats['integrated']} ({callback_stats['integration_rate']:.1f}%)")
    
    # Endpoint summary
    endpoint_stats = result.integration_status["endpoints"]
    print(f"\n🌐 ENDPOINT ANALYSIS:")
    print(f"  Total Endpoints: {endpoint_stats['total']}")
    print(f"  Implemented: {endpoint_stats['implemented']} ({endpoint_stats['implementation_rate']:.1f}%)")
    print(f"  Tested: {endpoint_stats['tested']} ({endpoint_stats['testing_rate']:.1f}%)")
    
    # Code quality summary
    print(f"\n🔍 CODE QUALITY:")
    if result.code_quality.get("status") == "success":
        issues = result.code_quality.get("issues_found", [])
        print(f"  DeepSource Status: ✅ Success")
        print(f"  Issues Found: {len(issues)}")
    else:
        quality_score = result.code_quality.get("quality_score", 0)
        print(f"  Fallback Analysis: {quality_score}% quality score")
    
    # Overall status
    overall = result.integration_status["overall_status"]
    print(f"\n📊 OVERALL STATUS:")
    print(f"  Callback Completion: {overall['callback_completion']:.1f}%")
    print(f"  Endpoint Completion: {overall['endpoint_completion']:.1f}%")
    print(f"  Integration Completion: {overall['integration_completion']:.1f}%")
    
    # Recommendations
    if result.recommendations:
        print(f"\n💡 AI RECOMMENDATIONS:")
        for i, rec in enumerate(result.recommendations, 1):
            print(f"  {i}. {rec}")
    
    print("\n" + "="*80)
    
    # Final assessment
    completion_score = (overall['callback_completion'] + overall['endpoint_completion'] + overall['integration_completion']) / 3
    
    if completion_score >= 90:
        logger.info("🎉 EXCELLENT! KPP Simulator is highly complete and well-integrated!")
    elif completion_score >= 75:
        logger.info("✅ GOOD! KPP Simulator is mostly complete with room for improvement.")
    elif completion_score >= 50:
        logger.info("⚠️ MODERATE! KPP Simulator needs significant work to complete.")
    else:
        logger.warning("❌ NEEDS WORK! KPP Simulator requires substantial development.")
    
    return result

if __name__ == "__main__":
    main() 