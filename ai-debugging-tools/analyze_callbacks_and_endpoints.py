"""
Callback and Endpoint Integration Analysis Tool

This script performs DeepSource-like static analysis to map callbacks and endpoints
in the KPP simulator, identifying integration issues and providing recommendations.
"""

import ast
import os
import json
import logging
from typing import Dict, List, Set, Any, Tuple
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class CallbackInfo:
    """Information about a callback function."""
    name: str
    file_path: str
    line_number: int
    function_type: str  # 'route', 'callback', 'event_handler', 'method'
    parameters: List[str]
    return_type: str
    decorators: List[str]
    dependencies: List[str]
    called_by: List[str]
    calls: List[str]


@dataclass
class EndpointInfo:
    """Information about an API endpoint."""
    route: str
    methods: List[str]
    file_path: str
    line_number: int
    function_name: str
    parameters: List[str]
    response_type: str
    error_handling: bool
    authentication: bool
    rate_limiting: bool
    dependencies: List[str]


@dataclass
class IntegrationIssue:
    """Integration issue found during analysis."""
    issue_type: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    file_path: str
    line_number: int
    message: str
    recommendation: str
    affected_components: List[str]


class CallbackEndpointAnalyzer:
    """Analyzer for callbacks and endpoints in the KPP simulator."""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.callbacks: Dict[str, CallbackInfo] = {}
        self.endpoints: Dict[str, EndpointInfo] = {}
        self.issues: List[IntegrationIssue] = []
        self.dependency_graph: Dict[str, Set[str]] = defaultdict(set)
        self.reverse_dependency_graph: Dict[str, Set[str]] = defaultdict(set)
        
    def analyze_project(self) -> Dict[str, Any]:
        """Analyze the entire project for callbacks and endpoints."""
        logger.info("Starting callback and endpoint analysis...")
        
        # Analyze Flask app
        self._analyze_flask_app()
        
        # Analyze simulation engine
        self._analyze_simulation_engine()
        
        # Analyze components
        self._analyze_components()
        
        # Build dependency graphs
        self._build_dependency_graphs()
        
        # Detect integration issues
        self._detect_integration_issues()
        
        # Generate recommendations
        recommendations = self._generate_recommendations()
        
        return {
            'callbacks': [asdict(cb) for cb in self.callbacks.values()],
            'endpoints': [asdict(ep) for ep in self.endpoints.values()],
            'issues': [asdict(issue) for issue in self.issues],
            'dependency_graph': {k: list(v) for k, v in self.dependency_graph.items()},
            'recommendations': recommendations,
            'summary': self._generate_summary()
        }
    
    def _analyze_flask_app(self):
        """Analyze Flask app for routes and callbacks."""
        app_file = self.project_root / "app.py"
        if not app_file.exists():
            logger.warning("app.py not found")
            return
        
        logger.info("Analyzing Flask app...")
        
        with open(app_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check for route decorators
                route_info = self._extract_route_info(node, app_file)
                if route_info:
                    self.endpoints[route_info.route] = route_info
                
                # Check for callback patterns
                callback_info = self._extract_callback_info(node, app_file)
                if callback_info:
                    self.callbacks[callback_info.name] = callback_info
    
    def _analyze_simulation_engine(self):
        """Analyze simulation engine for callbacks and event handlers."""
        engine_file = self.project_root / "simulation" / "engine.py"
        if not engine_file.exists():
            logger.warning("simulation/engine.py not found")
            return
        
        logger.info("Analyzing simulation engine...")
        
        with open(engine_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                callback_info = self._extract_simulation_callback_info(node, engine_file)
                if callback_info:
                    self.callbacks[callback_info.name] = callback_info
    
    def _analyze_components(self):
        """Analyze simulation components for callbacks."""
        components_dir = self.project_root / "simulation" / "components"
        if not components_dir.exists():
            logger.warning("simulation/components directory not found")
            return
        
        logger.info("Analyzing simulation components...")
        
        for py_file in components_dir.rglob("*.py"):
            if py_file.name.startswith("__"):
                continue
            
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    callback_info = self._extract_component_callback_info(node, py_file)
                    if callback_info:
                        self.callbacks[callback_info.name] = callback_info
    
    def _extract_route_info(self, node: ast.FunctionDef, file_path: Path) -> EndpointInfo:
        """Extract route information from a function definition."""
        route = None
        methods = ['GET']
        
        # Check for route decorators
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Call):
                if isinstance(decorator.func, ast.Attribute):
                    if decorator.func.attr == 'route':
                        # Extract route path
                        if decorator.args:
                            route = self._extract_string_literal(decorator.args[0])
                        
                        # Extract methods
                        for keyword in decorator.keywords:
                            if keyword.arg == 'methods':
                                if isinstance(keyword.value, ast.List):
                                    methods = [self._extract_string_literal(item) for item in keyword.value.elts]
        
        if route:
            return EndpointInfo(
                route=route,
                methods=methods,
                file_path=str(file_path),
                line_number=node.lineno,
                function_name=node.name,
                parameters=[arg.arg for arg in node.args.args],
                response_type=self._infer_response_type(node),
                error_handling=self._has_error_handling(node),
                authentication=False,  # Would need more analysis
                rate_limiting=False,   # Would need more analysis
                dependencies=self._extract_dependencies(node)
            )
        
        return None
    
    def _extract_callback_info(self, node: ast.FunctionDef, file_path: Path) -> CallbackInfo:
        """Extract callback information from a function definition."""
        # Check for callback patterns
        function_type = 'unknown'
        decorators = []
        
        for decorator in node.decorator_list:
            decorator_name = self._get_decorator_name(decorator)
            decorators.append(decorator_name)
            
            if 'route' in decorator_name:
                function_type = 'route'
            elif 'callback' in decorator_name:
                function_type = 'callback'
            elif 'event' in decorator_name:
                function_type = 'event_handler'
        
        # Check function name patterns
        if not function_type or function_type == 'unknown':
            if 'callback' in node.name.lower():
                function_type = 'callback'
            elif 'handler' in node.name.lower():
                function_type = 'event_handler'
            elif 'route' in node.name.lower():
                function_type = 'route'
        
        return CallbackInfo(
            name=node.name,
            file_path=str(file_path),
            line_number=node.lineno,
            function_type=function_type,
            parameters=[arg.arg for arg in node.args.args],
            return_type=self._infer_return_type(node),
            decorators=decorators,
            dependencies=self._extract_dependencies(node),
            called_by=[],
            calls=self._extract_function_calls(node)
        )
    
    def _extract_simulation_callback_info(self, node: ast.FunctionDef, file_path: Path) -> CallbackInfo:
        """Extract callback information specific to simulation engine."""
        # Check for simulation-specific patterns
        function_type = 'method'
        
        if 'step' in node.name.lower():
            function_type = 'simulation_step'
        elif 'update' in node.name.lower():
            function_type = 'state_update'
        elif 'trigger' in node.name.lower():
            function_type = 'event_trigger'
        elif 'handle' in node.name.lower():
            function_type = 'event_handler'
        
        return CallbackInfo(
            name=node.name,
            file_path=str(file_path),
            line_number=node.lineno,
            function_type=function_type,
            parameters=[arg.arg for arg in node.args.args],
            return_type=self._infer_return_type(node),
            decorators=[],
            dependencies=self._extract_dependencies(node),
            called_by=[],
            calls=self._extract_function_calls(node)
        )
    
    def _extract_component_callback_info(self, node: ast.FunctionDef, file_path: Path) -> CallbackInfo:
        """Extract callback information from simulation components."""
        function_type = 'component_method'
        
        # Check for component-specific patterns
        if 'update' in node.name.lower():
            function_type = 'component_update'
        elif 'compute' in node.name.lower():
            function_type = 'computation'
        elif 'calculate' in node.name.lower():
            function_type = 'calculation'
        
        return CallbackInfo(
            name=node.name,
            file_path=str(file_path),
            line_number=node.lineno,
            function_type=function_type,
            parameters=[arg.arg for arg in node.args.args],
            return_type=self._infer_return_type(node),
            decorators=[],
            dependencies=self._extract_dependencies(node),
            called_by=[],
            calls=self._extract_function_calls(node)
        )
    
    def _build_dependency_graphs(self):
        """Build dependency graphs between callbacks and endpoints."""
        logger.info("Building dependency graphs...")
        
        # Build forward dependencies
        for callback_name, callback in self.callbacks.items():
            for call in callback.calls:
                if call in self.callbacks:
                    self.dependency_graph[callback_name].add(call)
                    self.reverse_dependency_graph[call].add(callback_name)
        
        # Update called_by information
        for callback_name, callback in self.callbacks.items():
            callback.called_by = list(self.reverse_dependency_graph[callback_name])
    
    def _detect_integration_issues(self):
        """Detect integration issues between callbacks and endpoints."""
        logger.info("Detecting integration issues...")
        
        # Check for orphaned callbacks
        for callback_name, callback in self.callbacks.items():
            if not callback.called_by and callback.function_type not in ['route', 'main']:
                self.issues.append(IntegrationIssue(
                    issue_type='orphaned_callback',
                    severity='medium',
                    file_path=callback.file_path,
                    line_number=callback.line_number,
                    message=f"Callback '{callback_name}' is not called by any other function",
                    recommendation="Consider removing if unused or add proper integration",
                    affected_components=[callback_name]
                ))
        
        # Check for circular dependencies
        for callback_name in self.callbacks:
            if self._has_circular_dependency(callback_name):
                self.issues.append(IntegrationIssue(
                    issue_type='circular_dependency',
                    severity='high',
                    file_path=self.callbacks[callback_name].file_path,
                    line_number=self.callbacks[callback_name].line_number,
                    message=f"Circular dependency detected involving '{callback_name}'",
                    recommendation="Refactor to break circular dependency",
                    affected_components=self._get_circular_dependency_chain(callback_name)
                ))
        
        # Check for missing error handling in endpoints
        for endpoint_name, endpoint in self.endpoints.items():
            if not endpoint.error_handling:
                self.issues.append(IntegrationIssue(
                    issue_type='missing_error_handling',
                    severity='medium',
                    file_path=endpoint.file_path,
                    line_number=endpoint.line_number,
                    message=f"Endpoint '{endpoint_name}' lacks error handling",
                    recommendation="Add try-catch blocks and proper error responses",
                    affected_components=[endpoint_name]
                ))
        
        # Check for performance issues
        for callback_name, callback in self.callbacks.items():
            if len(callback.calls) > 10:  # Too many function calls
                self.issues.append(IntegrationIssue(
                    issue_type='performance_issue',
                    severity='medium',
                    file_path=callback.file_path,
                    line_number=callback.line_number,
                    message=f"Callback '{callback_name}' makes many function calls ({len(callback.calls)})",
                    recommendation="Consider optimizing or breaking into smaller functions",
                    affected_components=[callback_name]
                ))
    
    def _generate_recommendations(self) -> List[Dict[str, Any]]:
        """Generate recommendations for improving callback and endpoint integration."""
        recommendations = []
        
        # Group issues by type
        issue_groups = defaultdict(list)
        for issue in self.issues:
            issue_groups[issue.issue_type].append(issue)
        
        # Generate recommendations for each issue type
        for issue_type, issues in issue_groups.items():
            if issue_type == 'orphaned_callback':
                recommendations.append({
                    'category': 'code_cleanup',
                    'priority': 'medium',
                    'title': 'Remove or integrate orphaned callbacks',
                    'description': f'Found {len(issues)} callbacks that are not called by any other function',
                    'actions': [
                        'Review each orphaned callback for potential removal',
                        'Add proper integration if the callback is needed',
                        'Consider adding unit tests for important callbacks'
                    ],
                    'affected_files': list(set(issue.file_path for issue in issues))
                })
            
            elif issue_type == 'circular_dependency':
                recommendations.append({
                    'category': 'architecture',
                    'priority': 'high',
                    'title': 'Break circular dependencies',
                    'description': f'Found {len(issues)} circular dependency chains',
                    'actions': [
                        'Identify the dependency cycle and break it',
                        'Consider using dependency injection',
                        'Extract shared functionality into separate modules'
                    ],
                    'affected_files': list(set(issue.file_path for issue in issues))
                })
            
            elif issue_type == 'missing_error_handling':
                recommendations.append({
                    'category': 'robustness',
                    'priority': 'medium',
                    'title': 'Add error handling to endpoints',
                    'description': f'Found {len(issues)} endpoints without error handling',
                    'actions': [
                        'Add try-catch blocks around critical operations',
                        'Implement proper error response formats',
                        'Add logging for error conditions'
                    ],
                    'affected_files': list(set(issue.file_path for issue in issues))
                })
            
            elif issue_type == 'performance_issue':
                recommendations.append({
                    'category': 'performance',
                    'priority': 'medium',
                    'title': 'Optimize callback performance',
                    'description': f'Found {len(issues)} callbacks with potential performance issues',
                    'actions': [
                        'Break large callbacks into smaller functions',
                        'Consider caching for expensive operations',
                        'Profile performance-critical callbacks'
                    ],
                    'affected_files': list(set(issue.file_path for issue in issues))
                })
        
        return recommendations
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate analysis summary."""
        return {
            'total_callbacks': len(self.callbacks),
            'total_endpoints': len(self.endpoints),
            'total_issues': len(self.issues),
            'callback_types': self._count_callback_types(),
            'endpoint_methods': self._count_endpoint_methods(),
            'issue_severities': self._count_issue_severities(),
            'most_complex_callbacks': self._get_most_complex_callbacks(),
            'most_dependent_callbacks': self._get_most_dependent_callbacks()
        }
    
    # Helper methods
    def _extract_string_literal(self, node) -> str:
        """Extract string literal from AST node."""
        if isinstance(node, ast.Str):
            return node.s
        elif isinstance(node, ast.Constant):
            return str(node.value)
        return None
    
    def _get_decorator_name(self, decorator) -> str:
        """Get decorator name from AST node."""
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Attribute):
            return decorator.attr
        elif isinstance(decorator, ast.Call):
            if isinstance(decorator.func, ast.Attribute):
                return decorator.func.attr
            elif isinstance(decorator.func, ast.Name):
                return decorator.func.id
        return 'unknown'
    
    def _infer_response_type(self, node: ast.FunctionDef) -> str:
        """Infer response type from function body."""
        for stmt in node.body:
            if isinstance(stmt, ast.Return):
                if isinstance(stmt.value, ast.Call):
                    if isinstance(stmt.value.func, ast.Attribute):
                        if stmt.value.func.attr == 'jsonify':
                            return 'json'
        return 'unknown'
    
    def _infer_return_type(self, node: ast.FunctionDef) -> str:
        """Infer return type from function body."""
        for stmt in node.body:
            if isinstance(stmt, ast.Return):
                if isinstance(stmt.value, ast.Dict):
                    return 'dict'
                elif isinstance(stmt.value, ast.Str):
                    return 'str'
                elif isinstance(stmt.value, ast.Num):
                    return 'number'
        return 'unknown'
    
    def _has_error_handling(self, node: ast.FunctionDef) -> bool:
        """Check if function has error handling."""
        for stmt in node.body:
            if isinstance(stmt, ast.Try):
                return True
        return False
    
    def _extract_dependencies(self, node: ast.FunctionDef) -> List[str]:
        """Extract function dependencies."""
        dependencies = set()
        for stmt in ast.walk(node):
            if isinstance(stmt, ast.Import):
                for alias in stmt.names:
                    dependencies.add(alias.name)
            elif isinstance(stmt, ast.ImportFrom):
                if stmt.module:
                    dependencies.add(stmt.module)
        return list(dependencies)
    
    def _extract_function_calls(self, node: ast.FunctionDef) -> List[str]:
        """Extract function calls from function body."""
        calls = set()
        for stmt in ast.walk(node):
            if isinstance(stmt, ast.Call):
                if isinstance(stmt.func, ast.Name):
                    calls.add(stmt.func.id)
                elif isinstance(stmt.func, ast.Attribute):
                    calls.add(stmt.func.attr)
        return list(calls)
    
    def _has_circular_dependency(self, start_node: str) -> bool:
        """Check for circular dependencies using DFS."""
        visited = set()
        rec_stack = set()
        
        def dfs(node):
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in self.dependency_graph[node]:
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            
            rec_stack.remove(node)
            return False
        
        return dfs(start_node)
    
    def _get_circular_dependency_chain(self, start_node: str) -> List[str]:
        """Get the circular dependency chain."""
        # Simplified implementation - would need more complex logic for full chain
        return [start_node]
    
    def _count_callback_types(self) -> Dict[str, int]:
        """Count callback types."""
        counts = defaultdict(int)
        for callback in self.callbacks.values():
            counts[callback.function_type] += 1
        return dict(counts)
    
    def _count_endpoint_methods(self) -> Dict[str, int]:
        """Count endpoint methods."""
        counts = defaultdict(int)
        for endpoint in self.endpoints.values():
            for method in endpoint.methods:
                counts[method] += 1
        return dict(counts)
    
    def _count_issue_severities(self) -> Dict[str, int]:
        """Count issue severities."""
        counts = defaultdict(int)
        for issue in self.issues:
            counts[issue.severity] += 1
        return dict(counts)
    
    def _get_most_complex_callbacks(self) -> List[Dict[str, Any]]:
        """Get most complex callbacks (by number of calls)."""
        complex_callbacks = []
        for callback in self.callbacks.values():
            complex_callbacks.append({
                'name': callback.name,
                'file': callback.file_path,
                'calls': len(callback.calls),
                'type': callback.function_type
            })
        
        return sorted(complex_callbacks, key=lambda x: x['calls'], reverse=True)[:10]
    
    def _get_most_dependent_callbacks(self) -> List[Dict[str, Any]]:
        """Get most dependent callbacks (by number of callers)."""
        dependent_callbacks = []
        for callback in self.callbacks.values():
            dependent_callbacks.append({
                'name': callback.name,
                'file': callback.file_path,
                'called_by': len(callback.called_by),
                'type': callback.function_type
            })
        
        return sorted(dependent_callbacks, key=lambda x: x['called_by'], reverse=True)[:10]


def main():
    """Main function to run the analysis."""
    # Analyze the current project
    analyzer = CallbackEndpointAnalyzer(".")
    results = analyzer.analyze_project()
    
    # Save results to file
    with open("callback_endpoint_analysis.json", "w") as f:
        json.dump(results, f, indent=2)
    
    # Print summary
    summary = results['summary']
    print("\n" + "="*60)
    print("CALLBACK AND ENDPOINT ANALYSIS SUMMARY")
    print("="*60)
    print(f"Total Callbacks: {summary['total_callbacks']}")
    print(f"Total Endpoints: {summary['total_endpoints']}")
    print(f"Total Issues: {summary['total_issues']}")
    
    print(f"\nCallback Types:")
    for cb_type, count in summary['callback_types'].items():
        print(f"  {cb_type}: {count}")
    
    print(f"\nEndpoint Methods:")
    for method, count in summary['endpoint_methods'].items():
        print(f"  {method}: {count}")
    
    print(f"\nIssue Severities:")
    for severity, count in summary['issue_severities'].items():
        print(f"  {severity}: {count}")
    
    print(f"\nMost Complex Callbacks:")
    for cb in summary['most_complex_callbacks'][:5]:
        print(f"  {cb['name']} ({cb['calls']} calls) - {cb['type']}")
    
    print(f"\nMost Dependent Callbacks:")
    for cb in summary['most_dependent_callbacks'][:5]:
        print(f"  {cb['name']} ({cb['called_by']} callers) - {cb['type']}")
    
    print(f"\nRecommendations:")
    for i, rec in enumerate(results['recommendations'], 1):
        print(f"  {i}. {rec['title']} ({rec['priority']} priority)")
        print(f"     {rec['description']}")
    
    print(f"\nDetailed results saved to: callback_endpoint_analysis.json")


if __name__ == "__main__":
    main() 