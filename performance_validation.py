#!/usr/bin/env python3
"""
Comprehensive Performance Validation for KPP Simulator
Tests performance under various conditions and validates production readiness.
"""

import time
import threading
import psutil
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, Any, List
import statistics

# Import our simulation components
from simulation.engine import SimulationEngine
from simulation.components.thermal import ThermalModel
from simulation.components.fluid import FluidSystem
from simulation.components.environment import EnvironmentSystem
from simulation.components.control import Control
from simulation.components.chain import Chain
from simulation.components.pneumatics import PneumaticSystem
from simulation.components.integrated_drivetrain import IntegratedDrivetrain
from simulation.components.integrated_electrical_system import IntegratedElectricalSystem

class PerformanceValidator:
    """Performance validation for KPP simulator"""
    
    def __init__(self):
        self.results = {}
        self.start_time = time.time()
        
    def benchmark_function(self, func, iterations: int = 1000, warmup: int = 100) -> Dict[str, float]:
        """Benchmark a function's performance"""
        # Warmup
        for _ in range(warmup):
            try:
                func()
            except:
                pass
        
        # Actual benchmark
        times = []
        for _ in range(iterations):
            start = time.perf_counter()
            try:
                func()
            except Exception as e:
                print(f"Function failed: {e}")
            end = time.perf_counter()
            times.append(end - start)
        
        return {
            'min_time': min(times),
            'max_time': max(times),
            'avg_time': statistics.mean(times),
            'median_time': statistics.median(times),
            'std_dev': statistics.stdev(times) if len(times) > 1 else 0.0
        }
    
    def get_memory_usage(self) -> Dict[str, float]:
        """Get current memory usage"""
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        return {
            'rss_mb': memory_info.rss / 1024 / 1024,  # Resident Set Size in MB
            'vms_mb': memory_info.vms / 1024 / 1024,  # Virtual Memory Size in MB
            'percent': process.memory_percent()
        }
    
    def get_cpu_usage(self) -> float:
        """Get current CPU usage"""
        return psutil.cpu_percent(percpu=False)
    
    def test_component_performance(self):
        """Test individual component performance"""
        print("🔍 Testing Component Performance...")
        
        # Test Thermal Model
        thermal = ThermalModel()
        results = self.benchmark_function(lambda: thermal.update(0.01), iterations=10000)
        self.results['thermal_update'] = results
        print(f"✅ Thermal Model Update: {results['avg_time']*1000:.3f} ms")
        
        # Test Fluid System
        fluid = FluidSystem()
        results = self.benchmark_function(lambda: fluid.update(0.01), iterations=10000)
        self.results['fluid_update'] = results
        print(f"✅ Fluid System Update: {results['avg_time']*1000:.3f} ms")
        
        # Test Environment System
        env = EnvironmentSystem()
        results = self.benchmark_function(lambda: env.update(0.01), iterations=10000)
        self.results['environment_update'] = results
        print(f"✅ Environment System Update: {results['avg_time']*1000:.3f} ms")
        
        # Test Control System
        control = Control()
        results = self.benchmark_function(lambda: control.update(0.01), iterations=10000)
        self.results['control_update'] = results
        print(f"✅ Control System Update: {results['avg_time']*1000:.3f} ms")
        
        # Test Chain System
        chain = Chain()
        results = self.benchmark_function(lambda: chain.update(0.01), iterations=10000)
        self.results['chain_update'] = results
        print(f"✅ Chain System Update: {results['avg_time']*1000:.3f} ms")
        
        # Test Pneumatic System
        pneumatic = PneumaticSystem()
        results = self.benchmark_function(lambda: pneumatic.update(0.01), iterations=10000)
        self.results['pneumatic_update'] = results
        print(f"✅ Pneumatic System Update: {results['avg_time']*1000:.3f} ms")
        
        # Test Drivetrain
        drivetrain = IntegratedDrivetrain()
        results = self.benchmark_function(lambda: drivetrain.update(0.01), iterations=10000)
        self.results['drivetrain_update'] = results
        print(f"✅ Drivetrain Update: {results['avg_time']*1000:.3f} ms")
        
        # Test Electrical System
        electrical = IntegratedElectricalSystem()
        results = self.benchmark_function(lambda: electrical.update(0.01), iterations=10000)
        self.results['electrical_update'] = results
        print(f"✅ Electrical System Update: {results['avg_time']*1000:.3f} ms")
    
    def test_engine_performance(self):
        """Test full engine performance"""
        print("\n🚀 Testing Engine Performance...")
        
        # Test engine creation
        start = time.perf_counter()
        engine = SimulationEngine()
        creation_time = time.perf_counter() - start
        self.results['engine_creation'] = creation_time
        print(f"✅ Engine Creation: {creation_time*1000:.3f} ms")
        
        # Test engine start
        start = time.perf_counter()
        engine.start()
        start_time = time.perf_counter() - start
        self.results['engine_start'] = start_time
        print(f"✅ Engine Start: {start_time*1000:.3f} ms")
        
        # Test state retrieval
        results = self.benchmark_function(lambda: engine.get_state(), iterations=1000)
        self.results['state_retrieval'] = results
        print(f"✅ State Retrieval: {results['avg_time']*1000:.3f} ms")
        
        # Test engine stop
        start = time.perf_counter()
        engine.stop()
        stop_time = time.perf_counter() - start
        self.results['engine_stop'] = stop_time
        print(f"✅ Engine Stop: {stop_time*1000:.3f} ms")
    
    def test_memory_performance(self):
        """Test memory usage patterns"""
        print("\n💾 Testing Memory Performance...")
        
        initial_memory = self.get_memory_usage()
        print(f"📊 Initial Memory: {initial_memory['rss_mb']:.1f} MB")
        
        # Create multiple components
        components = []
        for i in range(100):
            components.append(ThermalModel())
            components.append(FluidSystem())
            components.append(EnvironmentSystem())
        
        memory_after_creation = self.get_memory_usage()
        print(f"📊 Memory After Component Creation: {memory_after_creation['rss_mb']:.1f} MB")
        
        # Test memory growth during operation
        for _ in range(1000):
            for component in components[:10]:  # Test with subset
                try:
                    component.update(0.01)
                except:
                    pass
        
        memory_after_operation = self.get_memory_usage()
        print(f"📊 Memory After Operation: {memory_after_operation['rss_mb']:.1f} MB")
        
        self.results['memory_growth'] = {
            'initial_mb': initial_memory['rss_mb'],
            'after_creation_mb': memory_after_creation['rss_mb'],
            'after_operation_mb': memory_after_operation['rss_mb'],
            'growth_mb': memory_after_operation['rss_mb'] - initial_memory['rss_mb']
        }
    
    def test_concurrent_performance(self):
        """Test concurrent operation performance"""
        print("\n🔄 Testing Concurrent Performance...")
        
        def worker_function(component_id: int):
            """Worker function for concurrent testing"""
            thermal = ThermalModel()
            fluid = FluidSystem()
            for _ in range(1000):
                try:
                    thermal.update(0.01)
                    fluid.update(0.01)
                except:
                    pass
        
        # Test single-threaded
        start = time.perf_counter()
        worker_function(0)
        single_threaded_time = time.perf_counter() - start
        
        # Test multi-threaded
        threads = []
        start = time.perf_counter()
        for i in range(4):
            thread = threading.Thread(target=worker_function, args=(i,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        multi_threaded_time = time.perf_counter() - start
        
        self.results['concurrent_performance'] = {
            'single_threaded_time': single_threaded_time,
            'multi_threaded_time': multi_threaded_time,
            'speedup': single_threaded_time / multi_threaded_time
        }
        
        print(f"✅ Single-threaded: {single_threaded_time:.3f}s")
        print(f"✅ Multi-threaded: {multi_threaded_time:.3f}s")
        print(f"✅ Speedup: {self.results['concurrent_performance']['speedup']:.2f}x")
    
    def validate_performance_requirements(self):
        """Validate performance against requirements"""
        print("\n📋 Validating Performance Requirements...")
        
        requirements = {
            'component_update_max_ms': 10.0,  # 10ms max per component update
            'engine_start_max_ms': 1000.0,    # 1s max for engine start
            'state_retrieval_max_ms': 50.0,   # 50ms max for state retrieval
            'memory_growth_max_mb': 100.0,    # 100MB max memory growth
            'concurrent_speedup_min': 1.5     # 1.5x minimum speedup
        }
        
        violations = []
        
        # Check component update times
        for component, results in self.results.items():
            if 'update' in component and 'avg_time' in results:
                avg_ms = results['avg_time'] * 1000
                if avg_ms > requirements['component_update_max_ms']:
                    violations.append(f"{component}: {avg_ms:.3f}ms > {requirements['component_update_max_ms']}ms")
        
        # Check engine start time
        if 'engine_start' in self.results:
            start_ms = self.results['engine_start'] * 1000
            if start_ms > requirements['engine_start_max_ms']:
                violations.append(f"Engine start: {start_ms:.3f}ms > {requirements['engine_start_max_ms']}ms")
        
        # Check state retrieval time
        if 'state_retrieval' in self.results:
            retrieval_ms = self.results['state_retrieval']['avg_time'] * 1000
            if retrieval_ms > requirements['state_retrieval_max_ms']:
                violations.append(f"State retrieval: {retrieval_ms:.3f}ms > {requirements['state_retrieval_max_ms']}ms")
        
        # Check memory growth
        if 'memory_growth' in self.results:
            growth_mb = self.results['memory_growth']['growth_mb']
            if growth_mb > requirements['memory_growth_max_mb']:
                violations.append(f"Memory growth: {growth_mb:.1f}MB > {requirements['memory_growth_max_mb']}MB")
        
        # Check concurrent speedup
        if 'concurrent_performance' in self.results:
            speedup = self.results['concurrent_performance']['speedup']
            if speedup < requirements['concurrent_speedup_min']:
                violations.append(f"Concurrent speedup: {speedup:.2f}x < {requirements['concurrent_speedup_min']}x")
        
        if violations:
            print("❌ Performance Requirements Violations:")
            for violation in violations:
                print(f"   - {violation}")
            return False
        else:
            print("✅ All Performance Requirements Met!")
            return True
    
    def generate_report(self):
        """Generate comprehensive performance report"""
        print("\n" + "="*80)
        print("📊 KPP SIMULATOR PERFORMANCE VALIDATION REPORT")
        print("="*80)
        
        print(f"\n🕒 Test Duration: {time.time() - self.start_time:.2f} seconds")
        print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        print("\n📈 Component Performance Summary:")
        print("-" * 50)
        for component, results in self.results.items():
            if isinstance(results, dict) and 'avg_time' in results:
                avg_ms = results['avg_time'] * 1000
                print(f"{component:25s}: {avg_ms:8.3f} ms")
        
        print("\n💾 Memory Performance:")
        print("-" * 50)
        if 'memory_growth' in self.results:
            mem = self.results['memory_growth']
            print(f"Initial Memory:     {mem['initial_mb']:8.1f} MB")
            print(f"After Creation:     {mem['after_creation_mb']:8.1f} MB")
            print(f"After Operation:    {mem['after_operation_mb']:8.1f} MB")
            print(f"Memory Growth:      {mem['growth_mb']:8.1f} MB")
        
        print("\n🔄 Concurrent Performance:")
        print("-" * 50)
        if 'concurrent_performance' in self.results:
            perf = self.results['concurrent_performance']
            print(f"Single-threaded:    {perf['single_threaded_time']:8.3f} s")
            print(f"Multi-threaded:     {perf['multi_threaded_time']:8.3f} s")
            print(f"Speedup:            {perf['speedup']:8.2f} x")
        
        print("\n🎯 Performance Requirements:")
        print("-" * 50)
        requirements_met = self.validate_performance_requirements()
        
        print(f"\n{'='*80}")
        if requirements_met:
            print("✅ PERFORMANCE VALIDATION PASSED - SYSTEM IS PRODUCTION READY!")
        else:
            print("❌ PERFORMANCE VALIDATION FAILED - OPTIMIZATION REQUIRED")
        print(f"{'='*80}")
        
        return requirements_met

def main():
    """Main performance validation function"""
    print("🚀 Starting KPP Simulator Performance Validation...")
    
    validator = PerformanceValidator()
    
    try:
        # Run all performance tests
        validator.test_component_performance()
        validator.test_engine_performance()
        validator.test_memory_performance()
        validator.test_concurrent_performance()
        
        # Generate report
        success = validator.generate_report()
        
        return 0 if success else 1
        
    except Exception as e:
        print(f"❌ Performance validation failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 