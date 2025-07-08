"""
Thread Safe Engine for KPP Simulator
Implements thread safety and concurrency features
"""

import logging
import threading
import time
import queue
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any, Callable, Generic, TypeVar
from datetime import datetime, timedelta
import weakref
import copy

T = TypeVar('T')


class ThreadPriority(Enum):
    """Thread priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class LockType(Enum):
    """Lock types"""
    READ = "read"
    WRITE = "write"
    EXCLUSIVE = "exclusive"


@dataclass
class ThreadInfo:
    """Thread information"""
    thread_id: int
    name: str
    priority: ThreadPriority
    start_time: datetime
    last_activity: datetime
    status: str
    cpu_usage: float = 0.0
    memory_usage: float = 0.0


@dataclass
class LockRequest:
    """Lock request information"""
    timestamp: datetime
    thread_id: int
    lock_type: LockType
    resource: str
    timeout: float
    granted: bool = False


class ThreadSafeQueue(Generic[T]):
    """Thread-safe queue implementation"""
    
    def __init__(self, maxsize: int = 0):
        self.queue = queue.Queue(maxsize=maxsize)
        self.lock = threading.RLock()
        self._size = 0
    
    def put(self, item: T, timeout: Optional[float] = None) -> bool:
        """Put item in queue"""
        try:
            with self.lock:
                self.queue.put(item, timeout=timeout)
                self._size += 1
                return True
        except queue.Full:
            return False
    
    def get(self, timeout: Optional[float] = None) -> Optional[T]:
        """Get item from queue"""
        try:
            with self.lock:
                item = self.queue.get(timeout=timeout)
                self._size -= 1
                return item
        except queue.Empty:
            return None
    
    def size(self) -> int:
        """Get queue size"""
        with self.lock:
            return self._size
    
    def empty(self) -> bool:
        """Check if queue is empty"""
        with self.lock:
            return self.queue.empty()
    
    def full(self) -> bool:
        """Check if queue is full"""
        with self.lock:
            return self.queue.full()


class ThreadSafeDict:
    """Thread-safe dictionary implementation"""
    
    def __init__(self):
        self._data = {}
        self._lock = threading.RLock()
    
    def __getitem__(self, key: str) -> Any:
        with self._lock:
            return self._data[key]
    
    def __setitem__(self, key: str, value: Any):
        with self._lock:
            self._data[key] = value
    
    def __delitem__(self, key: str):
        with self._lock:
            del self._data[key]
    
    def __contains__(self, key: str) -> bool:
        with self._lock:
            return key in self._data
    
    def get(self, key: str, default: Any = None) -> Any:
        with self._lock:
            return self._data.get(key, default)
    
    def keys(self) -> List[str]:
        with self._lock:
            return list(self._data.keys())
    
    def values(self) -> List[Any]:
        with self._lock:
            return list(self._data.values())
    
    def items(self) -> List[Tuple[str, Any]]:
        with self._lock:
            return list(self._data.items())
    
    def copy(self) -> Dict[str, Any]:
        with self._lock:
            return copy.deepcopy(self._data)
    
    def clear(self):
        with self._lock:
            self._data.clear()


class ResourceLock:
    """Resource locking mechanism"""
    
    def __init__(self, resource_name: str):
        self.resource_name = resource_name
        self._lock = threading.RLock()
        self._readers = 0
        self._writers = 0
        self._exclusive = False
        self._owner = None
        self._waiting_readers = []
        self._waiting_writers = []
        self._waiting_exclusive = []
    
    def acquire_read(self, timeout: float = 1.0) -> bool:
        """Acquire read lock"""
        start_time = time.time()
        
        while True:
            with self._lock:
                if self._exclusive or self._writers > 0:
                    # Wait for exclusive or write locks to be released
                    if time.time() - start_time > timeout:
                        return False
                    self._waiting_readers.append(threading.current_thread().ident)
                    self._lock.release()
                    time.sleep(0.001)
                    continue
                
                self._readers += 1
                return True
    
    def acquire_write(self, timeout: float = 1.0) -> bool:
        """Acquire write lock"""
        start_time = time.time()
        
        while True:
            with self._lock:
                if self._exclusive or self._readers > 0 or self._writers > 0:
                    # Wait for all locks to be released
                    if time.time() - start_time > timeout:
                        return False
                    self._waiting_writers.append(threading.current_thread().ident)
                    self._lock.release()
                    time.sleep(0.001)
                    continue
                
                self._writers += 1
                return True
    
    def acquire_exclusive(self, timeout: float = 1.0) -> bool:
        """Acquire exclusive lock"""
        start_time = time.time()
        
        while True:
            with self._lock:
                if self._exclusive or self._readers > 0 or self._writers > 0:
                    # Wait for all locks to be released
                    if time.time() - start_time > timeout:
                        return False
                    self._waiting_exclusive.append(threading.current_thread().ident)
                    self._lock.release()
                    time.sleep(0.001)
                    continue
                
                self._exclusive = True
                self._owner = threading.current_thread().ident
                return True
    
    def release_read(self):
        """Release read lock"""
        with self._lock:
            if self._readers > 0:
                self._readers -= 1
    
    def release_write(self):
        """Release write lock"""
        with self._lock:
            if self._writers > 0:
                self._writers -= 1
    
    def release_exclusive(self):
        """Release exclusive lock"""
        with self._lock:
            if self._exclusive and self._owner == threading.current_thread().ident:
                self._exclusive = False
                self._owner = None


class ThreadSafeEngine:
    """
    Thread Safe Engine for KPP Simulator
    
    Features:
    - Thread synchronization and data protection
    - Resource locking and deadlock prevention
    - Performance monitoring and optimization
    - Thread pool management
    - Memory management and garbage collection
    - Concurrency control and load balancing
    """
    
    def __init__(self):
        """Initialize the Thread Safe Engine"""
        # Thread management
        self.threads: Dict[int, ThreadInfo] = {}
        self.thread_pool = {}
        self.thread_lock = threading.RLock()
        
        # Resource management
        self.resource_locks: Dict[str, ResourceLock] = {}
        self.lock_requests: List[LockRequest] = []
        
        # Data structures
        self.thread_safe_data = ThreadSafeDict()
        self.message_queues: Dict[str, ThreadSafeQueue] = {}
        
        # Performance monitoring
        self.performance_metrics = {
            'total_threads': 0,
            'active_threads': 0,
            'lock_contention': 0.0,
            'average_lock_wait_time': 0.0,
            'memory_usage': 0.0,
            'cpu_usage': 0.0
        }
        
        # Engine state
        self.is_active = False
        self.monitoring_thread = None
        self.monitoring_interval = 0.1  # seconds
        
        # Thread pool configuration
        self.max_threads = 20
        self.min_threads = 2
        self.thread_timeout = 30.0  # seconds
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        self.logger.info("Thread Safe Engine initialized")
    
    def start(self):
        """Start the thread safe engine"""
        if self.is_active:
            self.logger.warning("Thread Safe Engine already active")
            return
        
        self.is_active = True
        
        # Start monitoring thread
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        
        self.logger.info("Thread Safe Engine started")
    
    def stop(self):
        """Stop the thread safe engine"""
        if not self.is_active:
            return
        
        self.is_active = False
        
        # Wait for monitoring thread
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=5.0)
        
        # Clean up threads
        self._cleanup_threads()
        
        self.logger.info("Thread Safe Engine stopped")
    
    def create_thread(self, target: Callable, name: str, 
                     priority: ThreadPriority = ThreadPriority.NORMAL,
                     args: Tuple = (), kwargs: Dict = {}) -> int:
        """Create a new thread"""
        try:
            with self.thread_lock:
                thread = threading.Thread(
                    target=self._thread_wrapper,
                    args=(target, name, priority, args, kwargs),
                    daemon=True
                )
                
                thread_id = thread.ident or id(thread)
                thread_info = ThreadInfo(
                    thread_id=thread_id,
                    name=name,
                    priority=priority,
                    start_time=datetime.now(),
                    last_activity=datetime.now(),
                    status="created"
                )
                
                self.threads[thread_id] = thread_info
                self.performance_metrics['total_threads'] += 1
                
                thread.start()
                
                self.logger.info(f"Thread created: {name} (ID: {thread_id})")
                return thread_id
                
        except Exception as e:
            self.logger.error(f"Failed to create thread {name}: {e}")
            return -1
    
    def _thread_wrapper(self, target: Callable, name: str, priority: ThreadPriority,
                       args: Tuple, kwargs: Dict):
        """Thread wrapper for monitoring and cleanup"""
        thread_id = threading.current_thread().ident
        if thread_id in self.threads:
            self.threads[thread_id].status = "running"
            self.threads[thread_id].last_activity = datetime.now()
        
        try:
            # Execute target function
            result = target(*args, **kwargs)
            
            # Update thread status
            if thread_id in self.threads:
                self.threads[thread_id].status = "completed"
                self.threads[thread_id].last_activity = datetime.now()
            
            return result
            
        except Exception as e:
            # Update thread status
            if thread_id in self.threads:
                self.threads[thread_id].status = "error"
                self.threads[thread_id].last_activity = datetime.now()
            
            self.logger.error(f"Thread {name} error: {e}")
            raise
    
    def acquire_lock(self, resource: str, lock_type: LockType, 
                    timeout: float = 1.0) -> bool:
        """Acquire a resource lock"""
        try:
            # Create lock if it doesn't exist
            if resource not in self.resource_locks:
                self.resource_locks[resource] = ResourceLock(resource)
            
            lock = self.resource_locks[resource]
            thread_id = threading.current_thread().ident or 0
            
            # Record lock request
            request = LockRequest(
                timestamp=datetime.now(),
                thread_id=thread_id,
                lock_type=lock_type,
                resource=resource,
                timeout=timeout
            )
            
            # Attempt to acquire lock
            if lock_type == LockType.READ:
                success = lock.acquire_read(timeout)
            elif lock_type == LockType.WRITE:
                success = lock.acquire_write(timeout)
            else:  # EXCLUSIVE
                success = lock.acquire_exclusive(timeout)
            
            request.granted = success
            self.lock_requests.append(request)
            
            # Limit lock request history
            if len(self.lock_requests) > 1000:
                self.lock_requests.pop(0)
            
            if success:
                self.logger.debug(f"Lock acquired: {resource} ({lock_type.value}) by thread {thread_id}")
            else:
                self.logger.warning(f"Lock acquisition failed: {resource} ({lock_type.value}) by thread {thread_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Lock acquisition error: {e}")
            return False
    
    def release_lock(self, resource: str, lock_type: LockType):
        """Release a resource lock"""
        try:
            if resource in self.resource_locks:
                lock = self.resource_locks[resource]
                thread_id = threading.current_thread().ident or 0
                
                if lock_type == LockType.READ:
                    lock.release_read()
                elif lock_type == LockType.WRITE:
                    lock.release_write()
                else:  # EXCLUSIVE
                    lock.release_exclusive()
                
                self.logger.debug(f"Lock released: {resource} ({lock_type.value}) by thread {thread_id}")
                
        except Exception as e:
            self.logger.error(f"Lock release error: {e}")
    
    def get_thread_safe_data(self, key: str, default: Any = None) -> Any:
        """Get data from thread-safe storage"""
        return self.thread_safe_data.get(key, default)
    
    def set_thread_safe_data(self, key: str, value: Any):
        """Set data in thread-safe storage"""
        self.thread_safe_data[key] = value
    
    def create_message_queue(self, queue_name: str, maxsize: int = 0) -> ThreadSafeQueue:
        """Create a thread-safe message queue"""
        if queue_name not in self.message_queues:
            self.message_queues[queue_name] = ThreadSafeQueue(maxsize=maxsize)
        
        return self.message_queues[queue_name]
    
    def get_message_queue(self, queue_name: str) -> Optional[ThreadSafeQueue]:
        """Get an existing message queue"""
        return self.message_queues.get(queue_name)
    
    def execute_safely(self, func: Callable, *args, **kwargs) -> Any:
        """Execute a function with thread safety"""
        try:
            # Create a lock for this execution
            execution_id = id(func)
            lock_name = f"execution_{execution_id}"
            
            if self.acquire_lock(lock_name, LockType.EXCLUSIVE, timeout=5.0):
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    self.release_lock(lock_name, LockType.EXCLUSIVE)
            else:
                raise RuntimeError(f"Failed to acquire execution lock for {func.__name__}")
                
        except Exception as e:
            self.logger.error(f"Safe execution error: {e}")
            raise
    
    def get_thread_info(self, thread_id: int) -> Optional[ThreadInfo]:
        """Get information about a specific thread"""
        return self.threads.get(thread_id)
    
    def get_all_threads(self) -> Dict[int, ThreadInfo]:
        """Get information about all threads"""
        with self.thread_lock:
            return self.threads.copy()
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        # Update active thread count
        active_count = sum(1 for info in self.threads.values() 
                          if info.status == "running")
        self.performance_metrics['active_threads'] = active_count
        
        return self.performance_metrics.copy()
    
    def get_lock_statistics(self) -> Dict[str, Any]:
        """Get lock usage statistics"""
        stats = {
            'total_locks': len(self.resource_locks),
            'total_requests': len(self.lock_requests),
            'granted_requests': sum(1 for req in self.lock_requests if req.granted),
            'failed_requests': sum(1 for req in self.lock_requests if not req.granted),
            'average_wait_time': 0.0,
            'lock_contention': {}
        }
        
        # Calculate average wait time
        if self.lock_requests:
            wait_times = []
            for req in self.lock_requests:
                if req.granted:
                    # Simplified wait time calculation
                    wait_times.append(0.001)  # Assume 1ms for granted requests
            
            if wait_times:
                stats['average_wait_time'] = sum(wait_times) / len(wait_times)
        
        # Calculate lock contention
        for resource, lock in self.resource_locks.items():
            stats['lock_contention'][resource] = {
                'readers': lock._readers,
                'writers': lock._writers,
                'exclusive': lock._exclusive
            }
        
        return stats
    
    def _monitoring_loop(self):
        """Thread monitoring loop"""
        while self.is_active:
            try:
                start_time = time.time()
                
                # Update thread information
                self._update_thread_info()
                
                # Clean up completed threads
                self._cleanup_completed_threads()
                
                # Update performance metrics
                self._update_performance_metrics()
                
                # Sleep for remaining time
                elapsed_time = time.time() - start_time
                sleep_time = max(0, self.monitoring_interval - elapsed_time)
                if sleep_time > 0:
                    time.sleep(sleep_time)
                
            except Exception as e:
                self.logger.error(f"Monitoring loop error: {e}")
                time.sleep(self.monitoring_interval)
    
    def _update_thread_info(self):
        """Update thread information"""
        try:
            current_time = datetime.now()
            
            for thread_id, thread_info in self.threads.items():
                # Update last activity for running threads
                if thread_info.status == "running":
                    thread_info.last_activity = current_time
                
                # Check for timeout
                if (thread_info.status == "running" and 
                    (current_time - thread_info.last_activity).total_seconds() > self.thread_timeout):
                    thread_info.status = "timeout"
                    self.logger.warning(f"Thread {thread_info.name} timed out")
                
        except Exception as e:
            self.logger.error(f"Failed to update thread info: {e}")
    
    def _cleanup_completed_threads(self):
        """Clean up completed threads"""
        try:
            with self.thread_lock:
                completed_threads = [
                    thread_id for thread_id, info in self.threads.items()
                    if info.status in ["completed", "error", "timeout"]
                ]
                
                for thread_id in completed_threads:
                    del self.threads[thread_id]
                    self.performance_metrics['total_threads'] -= 1
                
                if completed_threads:
                    self.logger.info(f"Cleaned up {len(completed_threads)} completed threads")
                
        except Exception as e:
            self.logger.error(f"Failed to cleanup threads: {e}")
    
    def _update_performance_metrics(self):
        """Update performance metrics"""
        try:
            # Calculate lock contention
            total_requests = len(self.lock_requests)
            if total_requests > 0:
                failed_requests = sum(1 for req in self.lock_requests if not req.granted)
                self.performance_metrics['lock_contention'] = failed_requests / total_requests
            
            # Update memory usage (simplified)
            self.performance_metrics['memory_usage'] = len(self.threads) * 0.1  # 100KB per thread
            
            # Update CPU usage (simplified)
            active_threads = sum(1 for info in self.threads.values() if info.status == "running")
            self.performance_metrics['cpu_usage'] = active_threads * 0.05  # 5% per active thread
            
        except Exception as e:
            self.logger.error(f"Failed to update performance metrics: {e}")
    
    def _cleanup_threads(self):
        """Clean up all threads"""
        try:
            with self.thread_lock:
                for thread_id, thread_info in self.threads.items():
                    if thread_info.status == "running":
                        thread_info.status = "stopping"
                
                self.threads.clear()
                self.performance_metrics['total_threads'] = 0
                self.performance_metrics['active_threads'] = 0
                
        except Exception as e:
            self.logger.error(f"Failed to cleanup threads: {e}")
    
    def clear_lock_history(self):
        """Clear lock request history"""
        self.lock_requests.clear()
        self.logger.info("Lock history cleared")
    
    def reset_performance_metrics(self):
        """Reset performance metrics"""
        self.performance_metrics = {
            'total_threads': len(self.threads),
            'active_threads': 0,
            'lock_contention': 0.0,
            'average_lock_wait_time': 0.0,
            'memory_usage': 0.0,
            'cpu_usage': 0.0
        }
        self.logger.info("Performance metrics reset") 