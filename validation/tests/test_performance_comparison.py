#!/usr/bin/env python3
"""
Phase 8 Performance Comparison Script
Compares legacy system performance vs advanced systems performance.
"""

import requests
import time
import json
import sys
from typing import Dict, List, Tuple

class PerformanceComparator:
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        
    def run_performance_comparison(self):
        """Run comprehensive performance comparison"""
        print("📊 PHASE 8 PERFORMANCE COMPARISON: Legacy vs Advanced")
        print("=" * 70)
        
        # Start simulation
        print("🚀 Starting simulation for performance analysis...")
        if not self._start_simulation():
            print("❌ Failed to start simulation")
            return False
            
        # Wait for steady state
        print("⏳ Waiting for steady state operation...")
        time.sleep(10)
        
        # Collect performance data
        performance_data = self._collect_performance_data()
        
        # Analyze and compare
        self._analyze_performance(performance_data)
        
        # Stop simulation
        self._stop_simulation()
        
        return True
    
    def _start_simulation(self) -> bool:
        """Start simulation"""
        try:
            response = requests.post(f"{self.base_url}/start", json={}, timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"Error starting simulation: {e}")
            return False
    
    def _stop_simulation(self):
        """Stop simulation"""
        try:
            requests.post(f"{self.base_url}/stop", timeout=5)
        except:
            pass
    
    def _collect_performance_data(self) -> Dict:
        """Collect comprehensive performance data"""
        print("📈 Collecting performance data from all systems...")
        
        data = {}
        
        # Core simulation data
        try:
            response = requests.get(f"{self.base_url}/data/summary", timeout=5)
            if response.status_code == 200:
                data['core'] = response.json()
        except:
            data['core'] = {}
        
        # Advanced drivetrain data
        try:
            response = requests.get(f"{self.base_url}/data/drivetrain_status", timeout=5)
            if response.status_code == 200:
                data['drivetrain'] = response.json()
        except:
            data['drivetrain'] = {}
        
        # Advanced electrical data
        try:
            response = requests.get(f"{self.base_url}/data/electrical_status", timeout=5)
            if response.status_code == 200:
                data['electrical'] = response.json()
        except:
            data['electrical'] = {}
        
        # Control system data
        try:
            response = requests.get(f"{self.base_url}/data/control_status", timeout=5)
            if response.status_code == 200:
                data['control'] = response.json()
        except:
            data['control'] = {}
        
        # Grid services data
        try:
            response = requests.get(f"{self.base_url}/data/grid_services_status", timeout=5)
            if response.status_code == 200:
                data['grid_services'] = response.json()
        except:
            data['grid_services'] = {}
        
        # Enhanced losses data
        try:
            response = requests.get(f"{self.base_url}/data/enhanced_losses", timeout=5)
            if response.status_code == 200:
                data['losses'] = response.json()
        except:
            data['losses'] = {}
        
        # System overview
        try:
            response = requests.get(f"{self.base_url}/data/system_overview", timeout=5)
            if response.status_code == 200:
                data['overview'] = response.json()
        except:
            data['overview'] = {}
        
        # Pneumatic performance
        try:
            response = requests.get(f"{self.base_url}/data/pneumatic_status", timeout=5)
            if response.status_code == 200:
                data['pneumatic'] = response.json()
        except:
            data['pneumatic'] = {}
        
        return data
    
    def _analyze_performance(self, data: Dict):
        """Analyze and compare performance"""
        print("\n🔍 PERFORMANCE ANALYSIS")
        print("=" * 50)
        
        # Data richness comparison
        self._compare_data_richness(data)
        
        # System capability comparison
        self._compare_system_capabilities(data)
        
        # Accuracy and detail comparison
        self._compare_accuracy_detail(data)
        
        # Feature completeness comparison
        self._compare_feature_completeness(data)
        
        # Performance metrics comparison
        self._compare_performance_metrics(data)
        
        # Overall assessment
        self._overall_assessment(data)
    
    def _compare_data_richness(self, data: Dict):
        """Compare data richness between legacy and advanced systems"""
        print("\n📊 Data Richness Comparison")
        print("-" * 30)
        
        # Count legacy data points (basic simulation data)
        legacy_data_points = 0
        core_data = data.get('core', {})
        if core_data:
            legacy_fields = ['time', 'torque', 'power', 'flywheel_speed_rpm', 'chain_speed_rpm', 
                           'clutch_engaged', 'pulse_count', 'overall_efficiency']
            legacy_data_points = len([field for field in legacy_fields if field in core_data])
        
        # Count advanced data points
        advanced_data_points = 0
        for system_name, system_data in data.items():
            if system_name != 'core' and isinstance(system_data, dict):
                advanced_data_points += self._count_nested_fields(system_data)
        
        improvement = 0
        if legacy_data_points > 0:
            improvement = ((advanced_data_points - legacy_data_points) / legacy_data_points) * 100
        
        print(f"Legacy System Data Points: {legacy_data_points}")
        print(f"Advanced Systems Data Points: {advanced_data_points}")
        print(f"Data Richness Improvement: +{improvement:.1f}%")
        
        if improvement > 200:
            print("🎉 SIGNIFICANT data richness improvement!")
        elif improvement > 100:
            print("✅ GOOD data richness improvement!")
        else:
            print("⚠️  Limited data richness improvement")
    
    def _compare_system_capabilities(self, data: Dict):
        """Compare system capabilities"""
        print("\n⚙️  System Capabilities Comparison")
        print("-" * 35)
        
        # Legacy capabilities (basic simulation)
        legacy_capabilities = [
            "Basic torque calculation",
            "Simple power output", 
            "Basic clutch model",
            "Simple efficiency calculation"
        ]
        
        # Advanced capabilities
        advanced_capabilities = []
        
        if data.get('drivetrain'):
            advanced_capabilities.extend([
                "Multi-stage gearbox modeling",
                "Flywheel energy storage simulation",
                "One-way clutch physics",
                "Sprocket chain dynamics"
            ])
        
        if data.get('electrical'):
            advanced_capabilities.extend([
                "Generator electromagnetic modeling", 
                "Power electronics simulation",
                "Grid synchronization",
                "Load factor optimization"
            ])
        
        if data.get('control'):
            advanced_capabilities.extend([
                "Integrated control system",
                "Fault detection and management",
                "Pneumatic timing control",
                "System health monitoring"
            ])
        
        if data.get('grid_services'):
            advanced_capabilities.extend([
                "Grid services coordination",
                "Market participation",
                "Frequency regulation",
                "Demand response"
            ])
        
        if data.get('losses'):
            advanced_capabilities.extend([
                "Enhanced loss modeling",
                "Thermal management",
                "Component temperature monitoring",
                "Efficiency optimization"
            ])
        
        print(f"Legacy Capabilities: {len(legacy_capabilities)}")
        for cap in legacy_capabilities:
            print(f"  • {cap}")
        
        print(f"\nAdvanced Capabilities: {len(advanced_capabilities)}")
        for cap in advanced_capabilities:
            print(f"  ✨ {cap}")
        
        capability_improvement = len(advanced_capabilities) - len(legacy_capabilities)
        print(f"\nCapability Enhancement: +{capability_improvement} new features")
    
    def _compare_accuracy_detail(self, data: Dict):
        """Compare accuracy and detail level"""
        print("\n🎯 Accuracy & Detail Comparison")
        print("-" * 32)
        
        # Check for advanced modeling features
        advanced_features = []
        
        drivetrain_data = data.get('drivetrain', {})
        if drivetrain_data:
            if drivetrain_data.get('system_efficiency', 0) > 0:
                advanced_features.append("Detailed drivetrain efficiency modeling")
            if drivetrain_data.get('flywheel_stored_energy', 0) > 0:
                advanced_features.append("Flywheel energy storage tracking")
        
        electrical_data = data.get('electrical', {})
        if electrical_data:
            if electrical_data.get('electrical_efficiency', 0) > 0:
                advanced_features.append("Electrical system efficiency modeling")
            if electrical_data.get('power_quality', {}):
                advanced_features.append("Power quality monitoring")
        
        losses_data = data.get('losses', {})
        if losses_data:
            if losses_data.get('mechanical_losses', {}):
                advanced_features.append("Detailed loss breakdown")
            if losses_data.get('component_temperatures', {}):
                advanced_features.append("Component thermal modeling")
        
        print("Advanced Modeling Features:")
        for feature in advanced_features:
            print(f"  ✅ {feature}")
        
        if len(advanced_features) >= 4:
            print("\n🏆 HIGH FIDELITY modeling achieved!")
        elif len(advanced_features) >= 2:
            print("\n✅ GOOD modeling detail level")
        else:
            print("\n⚠️  Limited modeling improvements")
    
    def _compare_performance_metrics(self, data: Dict):
        """Compare actual performance metrics"""
        print("\n📈 Performance Metrics Comparison")
        print("-" * 34)
        
        # Get key performance indicators
        core_data = data.get('core', {})
        drivetrain_data = data.get('drivetrain', {})
        electrical_data = data.get('electrical', {})
        overview_data = data.get('overview', {})
        
        # Legacy metrics (basic)
        legacy_power = core_data.get('power', 0)
        legacy_efficiency = core_data.get('overall_efficiency', 0)
        
        # Advanced metrics
        advanced_electrical_power = electrical_data.get('grid_power_output', 0)
        advanced_efficiency = drivetrain_data.get('system_efficiency', 0)
        grid_synchronized = electrical_data.get('synchronized', False)
        load_factor = electrical_data.get('load_factor', 0)
        
        print(f"Power Output Comparison:")
        print(f"  Legacy Power: {legacy_power/1000:.1f} kW")
        print(f"  Advanced Grid Power: {advanced_electrical_power/1000:.1f} kW")
        
        print(f"\nEfficiency Comparison:")
        print(f"  Legacy Efficiency: {legacy_efficiency*100:.1f}%")
        print(f"  Advanced Drivetrain Efficiency: {advanced_efficiency*100:.1f}%")
        
        print(f"\nNew Advanced Metrics:")
        print(f"  Grid Synchronized: {grid_synchronized}")
        print(f"  Load Factor: {load_factor*100:.1f}%")
        
        # Calculate system complexity score
        complexity_score = 0
        if drivetrain_data: complexity_score += 20
        if electrical_data: complexity_score += 25
        if data.get('control'): complexity_score += 20
        if data.get('grid_services'): complexity_score += 15
        if data.get('losses'): complexity_score += 20
        
        print(f"\nSystem Complexity Score: {complexity_score}/100")
        
        if complexity_score >= 80:
            print("🎊 COMPREHENSIVE advanced system integration!")
        elif complexity_score >= 60:
            print("✅ GOOD system integration level")
        else:
            print("⚠️  Partial system integration")
    
    def _compare_feature_completeness(self, data: Dict):
        """Compare feature completeness"""
        print("\n🔧 Feature Completeness Analysis")
        print("-" * 33)
        
        # Check for major feature categories
        features = {
            "Mechanical Modeling": bool(data.get('drivetrain')),
            "Electrical Systems": bool(data.get('electrical')),
            "Control Systems": bool(data.get('control')),
            "Grid Services": bool(data.get('grid_services')),
            "Loss Analysis": bool(data.get('losses')),
            "System Overview": bool(data.get('overview')),
            "Pneumatic Integration": bool(data.get('pneumatic'))
        }
        
        completed_features = sum(features.values())
        total_features = len(features)
        
        print("Feature Completion Status:")
        for feature, completed in features.items():
            status = "✅ ACTIVE" if completed else "❌ MISSING"
            print(f"  {status}: {feature}")
        
        completion_rate = (completed_features / total_features) * 100
        print(f"\nFeature Completion Rate: {completion_rate:.1f}% ({completed_features}/{total_features})")
        
        if completion_rate >= 90:
            print("🎉 EXCELLENT feature completeness!")
        elif completion_rate >= 70:
            print("✅ GOOD feature completeness")
        else:
            print("⚠️  More features need integration")
    
    def _overall_assessment(self, data: Dict):
        """Provide overall assessment"""
        print("\n🏆 OVERALL PHASE 8 INTEGRATION ASSESSMENT")
        print("=" * 50)
        
        # Calculate overall score
        scores = []
        
        # Data richness score
        total_data_points = sum(self._count_nested_fields(system_data) 
                               for system_data in data.values() 
                               if isinstance(system_data, dict))
        data_score = min(100, (total_data_points / 50) * 100)  # 50+ data points = 100%
        scores.append(("Data Richness", data_score))
        
        # System integration score
        active_systems = sum(1 for system_data in data.values() 
                           if isinstance(system_data, dict) and len(system_data) > 0)
        integration_score = (active_systems / 8) * 100  # 8 expected systems
        scores.append(("System Integration", integration_score))
        
        # Feature completeness score
        expected_features = ["drivetrain", "electrical", "control", "grid_services", "losses", "overview"]
        active_features = sum(1 for feature in expected_features if data.get(feature))
        feature_score = (active_features / len(expected_features)) * 100
        scores.append(("Feature Completeness", feature_score))
        
        # Calculate weighted average
        overall_score = sum(score for _, score in scores) / len(scores)
        
        print("Component Scores:")
        for component, score in scores:
            print(f"  {component}: {score:.1f}%")
        
        print(f"\nOVERALL INTEGRATION SCORE: {overall_score:.1f}%")
        
        if overall_score >= 90:
            print("\n🎊 OUTSTANDING! Phase 8 integration is highly successful!")
            print("The KPP simulation has been transformed into a comprehensive,")
            print("professional-grade system with advanced capabilities.")
        elif overall_score >= 75:
            print("\n🎉 EXCELLENT! Phase 8 integration is successful!")
            print("Most advanced systems are active and providing value.")
        elif overall_score >= 60:
            print("\n✅ GOOD! Phase 8 integration shows significant progress.")
            print("Key systems are working but some optimization remains.")
        else:
            print("\n⚠️  NEEDS IMPROVEMENT! Phase 8 integration is incomplete.")
            print("Several systems need attention to achieve full integration.")
        
        print("\nKey Achievements:")
        if data.get('drivetrain'):
            print("✅ Advanced mechanical drivetrain simulation")
        if data.get('electrical'):
            print("✅ Professional electrical system modeling")
        if data.get('control'):
            print("✅ Integrated control system management")
        if data.get('grid_services'):
            print("✅ Grid services coordination capability")
        if data.get('losses'):
            print("✅ Enhanced loss analysis and optimization")
        if total_data_points > 30:
            print("✅ Rich data output for comprehensive monitoring")
    
    def _count_nested_fields(self, data: dict, prefix: str = "") -> int:
        """Recursively count fields in nested dictionaries"""
        count = 0
        for key, value in data.items():
            if isinstance(value, dict):
                count += self._count_nested_fields(value, f"{prefix}{key}.")
            elif isinstance(value, list):
                count += len(value)
            else:
                count += 1
        return count

def main():
    """Main execution"""
    print("Starting Phase 8 Performance Comparison...")
    print("Make sure the simulation server is running on http://localhost:5000")
    print()
    
    comparator = PerformanceComparator()
    success = comparator.run_performance_comparison()
    
    if success:
        print("\n🎯 Performance comparison completed successfully!")
        return 0
    else:
        print("\n💥 Performance comparison failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
