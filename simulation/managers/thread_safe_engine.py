import threading
import time
import logging
import copy
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple, Callable
from enum import Enum
from simulation.engine import SimulationEngine
from .state_manager import StateManager


class ThreadPriority(Enum):
    """Thread priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class LockType(Enum):
    """Lock types for resource management"""
    READ = "read"
    WRITE = "write"
    EXCLUSIVE = "exclusive"


class ThreadInfo:
    """Information about a managed thread"""
    def __init__(self, thread_id: int, name: str, priority: ThreadPriority, 
                 start_time: datetime, last_activity: datetime, status: str):
        self.thread_id = thread_id
        self.name = name
        self.priority = priority
        self.start_time = start_time
        self.last_activity = last_activity
        self.status = status


class LockRequest:
    """Information about a lock request"""
    def __init__(self, timestamp: datetime, thread_id: int, lock_type: LockType, 
                 resource: str, timeout: float):
        self.timestamp = timestamp
        self.thread_id = thread_id
        self.lock_type = lock_type
        self.resource = resource
        self.timeout = timeout
        self.granted = False


class ResourceLock:
    """Advanced resource lock with read/write/exclusive capabilities"""
    def __init__(self, resource_name: str):
        self.resource_name = resource_name
        self.read_lock = threading.RLock()
        self.write_lock = threading.RLock()
        self.exclusive_lock = threading.RLock()
        self.readers = 0
        self.writers = 0
        self.exclusive_holder = None
        
    def acquire_read(self, timeout: float = 1.0) -> bool:
        """Acquire read lock"""
        try:
            if self.read_lock.acquire(timeout=timeout):
                self.readers += 1
                return True
            return False
        except:
            return False
    
    def acquire_write(self, timeout: float = 1.0) -> bool:
        """Acquire write lock"""
        try:
            if self.write_lock.acquire(timeout=timeout):
                self.writers += 1
                return True
            return False
        except:
            return False
    
    def acquire_exclusive(self, timeout: float = 1.0) -> bool:
        """Acquire exclusive lock"""
        try:
            if self.exclusive_lock.acquire(timeout=timeout):
                self.exclusive_holder = threading.current_thread().ident
                return True
            return False
        except:
            return False
    
    def release_read(self):
        """Release read lock"""
        if self.readers > 0:
            self.readers -= 1
            self.read_lock.release()
    
    def release_write(self):
        """Release write lock"""
        if self.writers > 0:
            self.writers -= 1
            self.write_lock.release()
    
    def release_exclusive(self):
        """Release exclusive lock"""
        if self.exclusive_holder == threading.current_thread().ident:
            self.exclusive_holder = None
            self.exclusive_lock.release()


class ThreadSafeQueue:
    """Thread-safe queue implementation"""
    def __init__(self, maxsize: int = 0):
        import queue
        self.queue = queue.Queue(maxsize=maxsize)
        self.lock = threading.RLock()
    
    def put(self, item: Any, block: bool = True, timeout: Optional[float] = None):
        """Put item in queue"""
        with self.lock:
            self.queue.put(item, block=block, timeout=timeout)
    
    def get(self, block: bool = True, timeout: Optional[float] = None) -> Any:
        """Get item from queue"""
        with self.lock:
            return self.queue.get(block=block, timeout=timeout)
    
    def empty(self) -> bool:
        """Check if queue is empty"""
        with self.lock:
            return self.queue.empty()
    
    def qsize(self) -> int:
        """Get queue size"""
        with self.lock:
            return self.queue.qsize()


class ThreadSafeDict:
    """Thread-safe dictionary implementation"""
    def __init__(self):
        self._data = {}
        self._lock = threading.RLock()
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get value from dictionary"""
        with self._lock:
            return self._data.get(key, default)
    
    def set(self, key: str, value: Any):
        """Set value in dictionary"""
        with self._lock:
            self._data[key] = value
    
    def __setitem__(self, key: str, value: Any):
        """Set value in dictionary using [] operator"""
        with self._lock:
            self._data[key] = value
    
    def __getitem__(self, key: str) -> Any:
        """Get value from dictionary using [] operator"""
        with self._lock:
            return self._data[key]
    
    def keys(self):
        """Get dictionary keys"""
        with self._lock:
            return list(self._data.keys())
    
    def values(self):
        """Get dictionary values"""
        with self._lock:
            return list(self._data.values())
    
    def items(self):
        """Get dictionary items"""
        with self._lock:
            return list(self._data.items())

class ThreadSafeEngine:
    """
    Advanced thread-safe simulation engine wrapper.
    Provides comprehensive thread safety, performance monitoring,
    and resource management for the KPP simulator.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the thread-safe engine.
        
        Args:
            config: Configuration dictionary for the simulation
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Thread management
        self.threads: Dict[int, ThreadInfo] = {}
        self.thread_counter = 0
        self.thread_lock = threading.RLock()
        
        # Resource management
        self.resource_locks: Dict[str, ResourceLock] = {}
        self.lock_history: List[LockRequest] = []
        self.lock_history_max = 1000
        
        # Performance monitoring
        self.performance_metrics = {
            'total_operations': 0,
            'successful_operations': 0,
            'failed_operations': 0,
            'average_response_time': 0.0,
            'peak_memory_usage': 0.0,
            'current_memory_usage': 0.0
        }
        
        # Message queues
        self.message_queues: Dict[str, ThreadSafeQueue] = {}
        self.queue_lock = threading.RLock()
        
        # Thread-safe data storage
        self.thread_safe_data = ThreadSafeDict()
        
        # Monitoring thread
        self.monitoring_thread = None
        self.monitoring_active = False
        
        # Initialize simulation engine
        from simulation.engine import SimulationEngine
        self.engine = SimulationEngine(config)
        
        # Start monitoring
        self._start_monitoring()
        
        self.logger.info("ThreadSafeEngine initialized with advanced features")
    
    def start(self):
        """Start the simulation thread-safely"""
        with self.thread_lock:
            if not self.engine.is_running:
                self.engine.start()
                self.logger.info("Simulation started via ThreadSafeEngine")
    
    def stop(self):
        """Stop the simulation thread-safely"""
        with self.thread_lock:
            if self.engine.is_running:
                self.engine.stop()
                self.logger.info("Simulation stopped via ThreadSafeEngine")
    
    def get_state(self) -> Dict[str, Any]:
        """Get current simulation state thread-safely"""
        with self.thread_lock:
            return self.engine.get_state()
    
    @property
    def is_running(self) -> bool:
        """Check if simulation is running thread-safely"""
        with self.thread_lock:
            return self.engine.is_running
    
    def create_thread(self, target: Callable, name: str, 
                     priority: ThreadPriority = ThreadPriority.NORMAL,
                     args: Tuple = (), kwargs: Dict = {}) -> int:
        """
        Create a new managed thread.
        
        Args:
            target: Function to run in thread
            name: Thread name
            priority: Thread priority
            args: Function arguments
            kwargs: Function keyword arguments
            
        Returns:
            Thread ID
        """
        with self.thread_lock:
            thread_id = self.thread_counter
            self.thread_counter += 1
            
            thread_info = ThreadInfo(
                thread_id=thread_id,
                name=name,
                priority=priority,
                start_time=datetime.now(),
                last_activity=datetime.now(),
                status="created"
            )
            
            self.threads[thread_id] = thread_info
            
            # Create and start thread
            thread = threading.Thread(
                target=self._thread_wrapper,
                args=(target, name, priority, args, kwargs, thread_id),
                name=f"{name}_{thread_id}",
                daemon=True
            )
            thread.start()
            
            self.logger.info(f"Created thread {thread_id} ({name}) with priority {priority.name}")
            return thread_id
    
    def _thread_wrapper(self, target: Callable, name: str, priority: ThreadPriority,
                       args: Tuple, kwargs: Dict, thread_id: int):
        """Wrapper for thread execution with monitoring"""
        try:
            with self.thread_lock:
                if thread_id in self.threads:
                    self.threads[thread_id].status = "running"
                    self.threads[thread_id].last_activity = datetime.now()
            
            # Execute target function
            result = target(*args, **kwargs)
            
            with self.thread_lock:
                if thread_id in self.threads:
                    self.threads[thread_id].status = "completed"
                    self.threads[thread_id].last_activity = datetime.now()
            
            return result
            
        except Exception as e:
            with self.thread_lock:
                if thread_id in self.threads:
                    self.threads[thread_id].status = f"error: {str(e)}"
                    self.threads[thread_id].last_activity = datetime.now()
            
            self.logger.error(f"Thread {thread_id} ({name}) failed: {e}")
            raise
    
    def acquire_lock(self, resource: str, lock_type: LockType, 
                    timeout: float = 1.0) -> bool:
        """
        Acquire a resource lock.
        
        Args:
            resource: Resource name
            lock_type: Type of lock to acquire
            timeout: Timeout in seconds
            
        Returns:
            True if lock acquired, False otherwise
        """
        # Ensure resource lock exists
        if resource not in self.resource_locks:
            with self.thread_lock:
                if resource not in self.resource_locks:
                    self.resource_locks[resource] = ResourceLock(resource)
        
        # Create lock request
        request = LockRequest(
            timestamp=datetime.now(),
            thread_id=threading.current_thread().ident or 0,
            lock_type=lock_type,
            resource=resource,
            timeout=timeout
        )
        
        # Attempt to acquire lock
        resource_lock = self.resource_locks[resource]
        if lock_type == LockType.READ:
            success = resource_lock.acquire_read(timeout)
        elif lock_type == LockType.WRITE:
            success = resource_lock.acquire_write(timeout)
        elif lock_type == LockType.EXCLUSIVE:
            success = resource_lock.acquire_exclusive(timeout)
        else:
            success = False
        
        request.granted = success
        
        # Record lock request
        with self.thread_lock:
            self.lock_history.append(request)
            if len(self.lock_history) > self.lock_history_max:
                self.lock_history.pop(0)
        
        return success
    
    def release_lock(self, resource: str, lock_type: LockType):
        """Release a resource lock"""
        if resource in self.resource_locks:
            resource_lock = self.resource_locks[resource]
            if lock_type == LockType.READ:
                resource_lock.release_read()
            elif lock_type == LockType.WRITE:
                resource_lock.release_write()
            elif lock_type == LockType.EXCLUSIVE:
                resource_lock.release_exclusive()
    
    def get_thread_safe_data(self, key: str, default: Any = None) -> Any:
        """Get thread-safe data"""
        return self.thread_safe_data.get(key, default)
    
    def set_thread_safe_data(self, key: str, value: Any):
        """Set thread-safe data"""
        self.thread_safe_data[key] = value
    
    def create_message_queue(self, queue_name: str, maxsize: int = 0) -> ThreadSafeQueue:
        """Create a new message queue"""
        with self.queue_lock:
            queue = ThreadSafeQueue(maxsize)
            self.message_queues[queue_name] = queue
            return queue
    
    def get_message_queue(self, queue_name: str) -> Optional[ThreadSafeQueue]:
        """Get an existing message queue"""
        return self.message_queues.get(queue_name)
    
    def execute_safely(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute a function with comprehensive error handling and monitoring.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
        """
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            
            # Update performance metrics
            with self.thread_lock:
                self.performance_metrics['total_operations'] += 1
                self.performance_metrics['successful_operations'] += 1
                response_time = time.time() - start_time
                self.performance_metrics['average_response_time'] = (
                    (self.performance_metrics['average_response_time'] * 
                     (self.performance_metrics['total_operations'] - 1) + response_time) /
                    self.performance_metrics['total_operations']
                )
            
            return result
            
        except Exception as e:
            with self.thread_lock:
                self.performance_metrics['total_operations'] += 1
                self.performance_metrics['failed_operations'] += 1
            
            self.logger.error(f"Function execution failed: {e}")
            raise
    
    def get_thread_info(self, thread_id: int) -> Optional[ThreadInfo]:
        """Get information about a specific thread"""
        with self.thread_lock:
            return self.threads.get(thread_id)
    
    def get_all_threads(self) -> Dict[int, ThreadInfo]:
        """Get information about all threads"""
        with self.thread_lock:
            return copy.deepcopy(self.threads)
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        with self.thread_lock:
            return copy.deepcopy(self.performance_metrics)
    
    def get_lock_statistics(self) -> Dict[str, Any]:
        """Get lock usage statistics"""
        with self.thread_lock:
            stats = {
                'total_locks': len(self.resource_locks),
                'lock_history_size': len(self.lock_history),
                'recent_requests': []
            }
            
            # Get recent lock requests
            recent_requests = self.lock_history[-10:] if self.lock_history else []
            for request in recent_requests:
                stats['recent_requests'].append({
                    'timestamp': request.timestamp.isoformat(),
                    'resource': request.resource,
                    'lock_type': request.lock_type.value,
                    'granted': request.granted,
                    'timeout': request.timeout
                })
            
            return stats
    
    def _start_monitoring(self):
        """Start the monitoring thread"""
        if not self.monitoring_active:
            self.monitoring_active = True
            self.monitoring_thread = threading.Thread(
                target=self._monitoring_loop,
                name="ThreadSafeEngine_Monitor",
                daemon=True
            )
            self.monitoring_thread.start()
            self.logger.info("Started ThreadSafeEngine monitoring")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                self._update_thread_info()
                self._cleanup_completed_threads()
                self._update_performance_metrics()
                time.sleep(1.0)  # Update every second
            except Exception as e:
                self.logger.error(f"Monitoring loop error: {e}")
                time.sleep(5.0)  # Wait longer on error
    
    def _update_thread_info(self):
        """Update thread information"""
        with self.thread_lock:
            for thread_info in self.threads.values():
                if thread_info.status == "running":
                    thread_info.last_activity = datetime.now()
    
    def _cleanup_completed_threads(self):
        """Clean up completed threads"""
        with self.thread_lock:
            completed_threads = [
                thread_id for thread_id, info in self.threads.items()
                if info.status in ["completed", "error"]
            ]
            
            for thread_id in completed_threads:
                del self.threads[thread_id]
    
    def _update_performance_metrics(self):
        """Update performance metrics"""
        # This would include memory usage tracking, etc.
        # Simplified for now
        pass
    
    def _cleanup_threads(self):
        """Clean up all threads"""
        with self.thread_lock:
            self.threads.clear()
    
    def clear_lock_history(self):
        """Clear lock history"""
        with self.thread_lock:
            self.lock_history.clear()
    
    def reset_performance_metrics(self):
        """Reset performance metrics"""
        with self.thread_lock:
            self.performance_metrics = {
                'total_operations': 0,
                'successful_operations': 0,
                'failed_operations': 0,
                'average_response_time': 0.0,
                'peak_memory_usage': 0.0,
                'current_memory_usage': 0.0
            }

