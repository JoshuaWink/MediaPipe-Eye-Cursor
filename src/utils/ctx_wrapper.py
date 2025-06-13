"""
Comprehensive Context Wrapper System for ModuLink Migration

Automatically converts any function to ModuLink Ctx-compliant with full introspection,
capturing all metadata, execution context, and runtime information without
requiring changes to original code.
"""

import functools
import inspect
import asyncio
import traceback
import tracemalloc
import time
import sys
import gc
import re
from typing import Callable, List, Dict, Any, Optional, Union, Pattern
from modulink import Ctx
from datetime import datetime
import copy

class IntrospectionCapture:
    """Comprehensive introspection and metadata capture system."""
    
    def __init__(self):
        self.trace_enabled = False
        self.local_vars_history = []
        
    def capture_function_metadata(self, func: Callable) -> Dict[str, Any]:
        """Capture complete function metadata."""
        try:
            signature = inspect.signature(func)
            source_lines = inspect.getsourcelines(func)
            
            metadata = {
                'name': func.__name__,
                'qualname': getattr(func, '__qualname__', func.__name__),
                'module': getattr(func, '__module__', 'unknown'),
                'file': inspect.getfile(func) if hasattr(func, '__code__') else 'unknown',
                'line_number': func.__code__.co_firstlineno if hasattr(func, '__code__') else 0,
                'signature': str(signature),
                'parameters': {
                    name: {
                        'annotation': str(param.annotation) if param.annotation != param.empty else None,
                        'default': str(param.default) if param.default != param.empty else None,
                        'kind': str(param.kind)
                    }
                    for name, param in signature.parameters.items()
                },
                'return_annotation': str(signature.return_annotation) if signature.return_annotation != signature.empty else None,
                'docstring': inspect.getdoc(func),
                'source_code': ''.join(source_lines[0]) if source_lines else None,
                'source_line_start': source_lines[1] if source_lines else None,
                'is_async': asyncio.iscoroutinefunction(func),
                'is_generator': inspect.isgeneratorfunction(func),
                'is_method': inspect.ismethod(func),
                'is_builtin': inspect.isbuiltin(func),
                'code_info': {
                    'argcount': func.__code__.co_argcount if hasattr(func, '__code__') else 0,
                    'varnames': func.__code__.co_varnames if hasattr(func, '__code__') else [],
                    'filename': func.__code__.co_filename if hasattr(func, '__code__') else 'unknown',
                    'flags': func.__code__.co_flags if hasattr(func, '__code__') else 0
                }
            }
            
            return metadata
        except Exception as e:
            return {'error': f"Failed to capture metadata: {e}", 'name': getattr(func, '__name__', 'unknown')}
    
    def capture_execution_context(self, frame: Optional[object] = None) -> Dict[str, Any]:
        """Capture complete execution context."""
        if frame is None:
            frame = inspect.currentframe().f_back
            
        context = {
            'stack_info': [],
            'local_variables': {},
            'global_variables': {},
            'builtin_variables': {},
            'frame_info': {}
        }
        
        try:
            # Capture stack trace
            stack = inspect.stack()
            for i, frame_info in enumerate(stack[:10]):  # Limit to 10 frames
                context['stack_info'].append({
                    'index': i,
                    'filename': frame_info.filename,
                    'line_number': frame_info.lineno,
                    'function': frame_info.function,
                    'code_context': frame_info.code_context
                })
            
            # Capture variables from current frame
            if frame:
                context['local_variables'] = self._safe_copy_variables(frame.f_locals)
                context['global_variables'] = self._safe_copy_variables(frame.f_globals)
                
                context['frame_info'] = {
                    'filename': frame.f_code.co_filename,
                    'function_name': frame.f_code.co_name,
                    'line_number': frame.f_lineno,
                    'instruction': frame.f_lasti
                }
            
            # Capture builtin variables
            import builtins
            context['builtin_variables'] = {
                name: str(getattr(builtins, name, 'N/A'))
                for name in dir(builtins)
                if not name.startswith('_')
            }
            
        except Exception as e:
            context['capture_error'] = str(e)
        
        return context
    
    def _safe_copy_variables(self, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Safely copy variables, handling non-serializable objects."""
        safe_vars = {}
        
        for name, value in variables.items():
            try:
                # Try to create a safe representation
                if isinstance(value, (str, int, float, bool, type(None))):
                    safe_vars[name] = value
                elif isinstance(value, (list, tuple)):
                    safe_vars[name] = {
                        '_type': type(value).__name__,
                        '_length': len(value),
                        '_preview': str(value)[:200] + '...' if len(str(value)) > 200 else str(value)
                    }
                elif isinstance(value, dict):
                    safe_vars[name] = {
                        '_type': 'dict',
                        '_length': len(value),
                        '_keys': list(value.keys())[:20],  # First 20 keys
                        '_preview': str(value)[:200] + '...' if len(str(value)) > 200 else str(value)
                    }
                else:
                    safe_vars[name] = {
                        '_type': type(value).__name__,
                        '_module': getattr(type(value), '__module__', 'unknown'),
                        '_repr': str(value)[:200] + '...' if len(str(value)) > 200 else str(value),
                        '_id': id(value),
                        '_size': sys.getsizeof(value) if hasattr(sys, 'getsizeof') else 'unknown'
                    }
            except Exception as e:
                safe_vars[name] = {
                    '_type': 'uncapturable',
                    '_error': str(e)
                }
        
        return safe_vars
    
    def capture_performance_metrics(self) -> Dict[str, Any]:
        """Capture performance and memory metrics."""
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'process_time': time.process_time(),
            'perf_counter': time.perf_counter(),
            'thread_time': time.thread_time() if hasattr(time, 'thread_time') else None,
        }
        
        # Memory metrics
        try:
            if tracemalloc.is_tracing():
                current, peak = tracemalloc.get_traced_memory()
                metrics['memory'] = {
                    'current': current,
                    'peak': peak,
                    'traced': True
                }
            else:
                metrics['memory'] = {'traced': False}
                
            # Garbage collection info
            metrics['gc_info'] = {
                'counts': gc.get_count(),
                'stats': gc.get_stats() if hasattr(gc, 'get_stats') else None
            }
        except Exception as e:
            metrics['memory_error'] = str(e)
        
        return metrics

class FilteringSystem:
    """Whitelist/blacklist filtering system for metadata capture."""
    
    def __init__(self, 
                 whitelist_params: Optional[List[str]] = None,
                 blacklist_params: Optional[List[str]] = None,
                 whitelist_regex: Optional[List[str]] = None,
                 blacklist_regex: Optional[List[str]] = None):
        
        self.whitelist_params = set(whitelist_params or [])
        self.blacklist_params = set(blacklist_params or [])
        self.whitelist_regex = [re.compile(pattern) for pattern in (whitelist_regex or [])]
        self.blacklist_regex = [re.compile(pattern) for pattern in (blacklist_regex or [])]
    
    def should_capture(self, param_name: str) -> bool:
        """Determine if a parameter should be captured based on filtering rules."""
        # If no filters are set, capture everything
        if not any([self.whitelist_params, self.blacklist_params, self.whitelist_regex, self.blacklist_regex]):
            return True
        
        # Check blacklist first
        if param_name in self.blacklist_params:
            return False
            
        for pattern in self.blacklist_regex:
            if pattern.match(param_name):
                return False
        
        # Check whitelist (if whitelist exists, param must be whitelisted)
        if self.whitelist_params or self.whitelist_regex:
            if param_name in self.whitelist_params:
                return True
            
            for pattern in self.whitelist_regex:
                if pattern.match(param_name):
                    return True
            
            return False  # Not in whitelist
        
        return True  # Passed blacklist and no whitelist restrictions

class CtxWrapper:
    """Comprehensive ModuLink context wrapper with full introspection."""
    
    def __init__(self, 
                 whitelist_params: Optional[List[str]] = None,
                 blacklist_params: Optional[List[str]] = None,
                 whitelist_regex: Optional[List[str]] = None,
                 blacklist_regex: Optional[List[str]] = None,
                 enable_memory_tracing: bool = True):
        
        self.introspector = IntrospectionCapture()
        self.filter_system = FilteringSystem(whitelist_params, blacklist_params, whitelist_regex, blacklist_regex)
        self.enable_memory_tracing = enable_memory_tracing
        
        if enable_memory_tracing and not tracemalloc.is_tracing():
            tracemalloc.start()
    
    def ctx_comprehensive_wrap(self,
                              input_keys: Optional[List[str]] = None,
                              output_key: Optional[str] = None,
                              capture_locals: bool = True,
                              capture_globals: bool = True,
                              capture_performance: bool = True,
                              preserve_original: bool = True):
        """
        Comprehensive wrapper with full introspection capabilities.
        
        Args:
            input_keys: Keys to extract from context for function parameters
            output_key: Key to store function result
            capture_locals: Whether to capture local variables
            capture_globals: Whether to capture global variables
            capture_performance: Whether to capture performance metrics
            preserve_original: Whether to preserve original context
        """
        def decorator(func: Callable):
            # Capture function metadata once at decoration time
            func_metadata = self.introspector.capture_function_metadata(func)
            
            # Determine input keys
            actual_input_keys = input_keys
            if actual_input_keys is None:
                # Auto-detect from function signature
                sig = inspect.signature(func)
                actual_input_keys = [name for name in sig.parameters.keys() if name != 'self']
            
            # Determine output key
            actual_output_key = output_key or f"{func.__name__}_result"
            
            if func_metadata.get('is_async', False):
                @functools.wraps(func)
                async def async_comprehensive_wrapper(ctx: Ctx) -> Ctx:
                    return await self._execute_with_introspection(
                        func, ctx, actual_input_keys, actual_output_key,
                        func_metadata, capture_locals, capture_globals, 
                        capture_performance, preserve_original, is_async=True
                    )
                return async_comprehensive_wrapper
            else:
                @functools.wraps(func)
                async def sync_comprehensive_wrapper(ctx: Ctx) -> Ctx:
                    return await self._execute_with_introspection(
                        func, ctx, actual_input_keys, actual_output_key,
                        func_metadata, capture_locals, capture_globals,
                        capture_performance, preserve_original, is_async=False
                    )
                return sync_comprehensive_wrapper
        
        return decorator
    
    async def _execute_with_introspection(self,
                                        func: Callable,
                                        ctx: Ctx,
                                        input_keys: List[str],
                                        output_key: str,
                                        func_metadata: Dict[str, Any],
                                        capture_locals: bool,
                                        capture_globals: bool,
                                        capture_performance: bool,
                                        preserve_original: bool,
                                        is_async: bool) -> Ctx:
        """Execute function with comprehensive introspection."""
        
        # Start performance tracking
        start_metrics = self.introspector.capture_performance_metrics() if capture_performance else {}
        
        # Capture pre-execution context
        pre_execution_context = self.introspector.capture_execution_context() if capture_locals or capture_globals else {}
        
        # Build introspection metadata
        introspection_data = {
            'function_metadata': func_metadata,
            'execution_id': f"{func.__name__}_{int(time.time() * 1000000)}",
            'wrapper_config': {
                'input_keys': input_keys,
                'output_key': output_key,
                'capture_locals': capture_locals,
                'capture_globals': capture_globals,
                'capture_performance': capture_performance,
                'is_async': is_async
            },
            'pre_execution': {
                'context': pre_execution_context,
                'metrics': start_metrics,
                'input_context_keys': list(ctx.keys()),
                'input_context_size': len(ctx)
            }
        }
        
        try:
            # Extract function arguments from context
            kwargs = {}
            missing_keys = []
            
            for key in input_keys:
                if self.filter_system.should_capture(key):
                    if key in ctx:
                        kwargs[key] = ctx[key]
                    else:
                        missing_keys.append(key)
            
            introspection_data['parameter_extraction'] = {
                'extracted_keys': list(kwargs.keys()),
                'missing_keys': missing_keys,
                'parameter_values': {
                    key: {
                        '_type': type(value).__name__,
                        '_repr': str(value)[:100] + '...' if len(str(value)) > 100 else str(value)
                    }
                    for key, value in kwargs.items()
                    if self.filter_system.should_capture(key)
                }
            }
            
            # Execute the function
            if is_async:
                result = await func(**kwargs)
            else:
                result = func(**kwargs)
            
            # Capture post-execution context
            post_execution_context = self.introspector.capture_execution_context() if capture_locals or capture_globals else {}
            end_metrics = self.introspector.capture_performance_metrics() if capture_performance else {}
            
            # Analyze result
            result_analysis = {
                '_type': type(result).__name__,
                '_repr': str(result)[:200] + '...' if len(str(result)) > 200 else str(result),
                '_size': sys.getsizeof(result) if hasattr(sys, 'getsizeof') else 'unknown'
            }
            
            if isinstance(result, dict):
                result_analysis['_keys'] = list(result.keys())
                result_analysis['_length'] = len(result)
            elif hasattr(result, '__len__'):
                result_analysis['_length'] = len(result)
            
            introspection_data['post_execution'] = {
                'context': post_execution_context,
                'metrics': end_metrics,
                'result_analysis': result_analysis,
                'execution_successful': True
            }
            
            # Calculate performance deltas
            if capture_performance and start_metrics and end_metrics:
                introspection_data['performance_delta'] = {
                    'execution_time': end_metrics.get('perf_counter', 0) - start_metrics.get('perf_counter', 0),
                    'process_time_delta': end_metrics.get('process_time', 0) - start_metrics.get('process_time', 0)
                }
                
                if 'memory' in start_metrics and 'memory' in end_metrics:
                    start_mem = start_metrics['memory'].get('current', 0)
                    end_mem = end_metrics['memory'].get('current', 0)
                    introspection_data['performance_delta']['memory_delta'] = end_mem - start_mem
            
            # Build result context
            new_ctx = {**ctx} if preserve_original else {}
            
            # Add function result
            if isinstance(result, dict):
                new_ctx.update(result)
            else:
                new_ctx[output_key] = result
            
            # Add comprehensive introspection data
            new_ctx['_introspection'] = introspection_data
            
            return new_ctx
            
        except Exception as e:
            # Capture error context
            error_context = self.introspector.capture_execution_context() if capture_locals or capture_globals else {}
            error_metrics = self.introspector.capture_performance_metrics() if capture_performance else {}
            
            introspection_data['error_execution'] = {
                'context': error_context,
                'metrics': error_metrics,
                'exception': {
                    'type': type(e).__name__,
                    'message': str(e),
                    'repr': repr(e),
                    'traceback': traceback.format_exc()
                },
                'execution_successful': False
            }
            
            # Build error context
            error_ctx = {**ctx} if preserve_original else {}
            error_ctx['error'] = e
            error_ctx['_introspection'] = introspection_data
            
            return error_ctx

# Convenience functions for common patterns
def ctx_wrap(input_keys=None, output_key=None, **kwargs):
    """Simple comprehensive wrapper."""
    wrapper = CtxWrapper()
    return wrapper.ctx_comprehensive_wrap(input_keys=input_keys, output_key=output_key, **kwargs)

def ctx_wrap_filtered(whitelist_params=None, blacklist_params=None, 
                     whitelist_regex=None, blacklist_regex=None, **kwargs):
    """Comprehensive wrapper with filtering."""
    wrapper = CtxWrapper(whitelist_params, blacklist_params, whitelist_regex, blacklist_regex)
    return wrapper.ctx_comprehensive_wrap(**kwargs)

# Example usage patterns
def create_config_loader():
    """Example: Config loading with full introspection."""
    @ctx_wrap(input_keys=['config_path'], output_key='config')
    def load_config(config_path='config.json'):
        from src.utils.config import Config
        return Config.load(config_path)
    
    return load_config

def create_detector_initializer():
    """Example: Detector initialization with full introspection."""
    @ctx_wrap(input_keys=['config'], output_key='detector')
    def initialize_detector(config):
        from src.eye_tracker.detector import EyeDetector
        return EyeDetector(config)
    
    return initialize_detector
