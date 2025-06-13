"""
Logging Middleware for ModuLink Chains

Provides middleware functions that automatically log context flow through ModuLink chains
with full context serialization before and after each link execution.
"""

import functools
import inspect
from typing import Callable, Any
from modulink import Ctx
from .context_logger import log_context, enter_chain, exit_chain

async def comprehensive_logging_middleware(ctx: Ctx) -> Ctx:
    """
    Comprehensive logging middleware that logs full context.
    
    This middleware is designed to be used with ModuLink's before/after middleware system.
    It automatically detects the link name and logs the complete context.
    """
    # Get the current function/link name from the call stack
    frame = inspect.currentframe()
    link_name = "unknown_link"
    
    try:
        # Go up the stack to find the actual link function
        # Stack: middleware -> chain execution -> actual link
        if frame and frame.f_back and frame.f_back.f_back:
            caller_frame = frame.f_back.f_back
            if hasattr(caller_frame, 'f_code'):
                link_name = caller_frame.f_code.co_name
    finally:
        del frame
    
    # Log the context before link execution
    chain_name = ctx.get('_current_chain', 'unknown_chain')
    log_context(ctx, "before", link_name, None, chain_name)
    
    return ctx

async def error_logging_middleware(ctx: Ctx) -> Ctx:
    """
    Error logging middleware that captures context when errors occur.
    
    This should be used as an after middleware to catch any errors that occurred
    during link execution.
    """
    if ctx.get('error'):
        # Get the current function/link name
        frame = inspect.currentframe()
        link_name = "unknown_link"
        
        try:
            if frame and frame.f_back and frame.f_back.f_back:
                caller_frame = frame.f_back.f_back
                if hasattr(caller_frame, 'f_code'):
                    link_name = caller_frame.f_code.co_name
        finally:
            del frame
        
        chain_name = ctx.get('_current_chain', 'unknown_chain')
        error = ctx.get('error')
        log_context(ctx, "error", link_name, error, chain_name)
    
    return ctx

async def result_logging_middleware(ctx: Ctx) -> Ctx:
    """
    Result logging middleware that logs context after successful link execution.
    """
    if not ctx.get('error'):  # Only log if no error occurred
        frame = inspect.currentframe()
        link_name = "unknown_link"
        
        try:
            if frame and frame.f_back and frame.f_back.f_back:
                caller_frame = frame.f_back.f_back
                if hasattr(caller_frame, 'f_code'):
                    link_name = caller_frame.f_code.co_name
        finally:
            del frame
        
        chain_name = ctx.get('_current_chain', 'unknown_chain')
        log_context(ctx, "after", link_name, None, chain_name)
    
    return ctx

def create_logged_chain(chain_instance, chain_name: str):
    """
    Wrap a ModuLink chain with comprehensive logging.
    
    Args:
        chain_instance: The ModuLink chain instance to wrap
        chain_name: Name of the chain for logging purposes
        
    Returns:
        Wrapped chain with logging middleware applied
    """
    # Add logging middleware to the chain
    chain_instance.use.before([comprehensive_logging_middleware])
    chain_instance.use.after([result_logging_middleware, error_logging_middleware])
    
    # Create a wrapper that adds chain tracking
    original_call = chain_instance.__call__
    
    async def logged_chain_call(ctx: Ctx) -> Ctx:
        # Add chain name to context for logging
        ctx_with_chain = {**ctx, '_current_chain': chain_name}
        
        # Enter chain logging
        enter_chain(chain_name)
        
        try:
            # Execute the original chain
            result = await original_call(ctx_with_chain)
            return result
        finally:
            # Exit chain logging
            exit_chain(chain_name)
    
    # Replace the chain's call method
    chain_instance.__call__ = logged_chain_call
    
    return chain_instance

def logged_link(link_name: str = None):
    """
    Decorator to add logging to individual ModuLink links.
    
    Usage:
        @logged_link("my_custom_link")
        async def my_link(ctx: Ctx) -> Ctx:
            # link implementation
            return ctx
    """
    def decorator(func: Callable[[Ctx], Ctx]):
        name = link_name or func.__name__
        
        @functools.wraps(func)
        async def wrapper(ctx: Ctx) -> Ctx:
            # Log before execution
            chain_name = ctx.get('_current_chain', 'individual_link')
            log_context(ctx, "before", name, None, chain_name)
            
            try:
                # Execute the original link
                if inspect.iscoroutinefunction(func):
                    result = await func(ctx)
                else:
                    result = func(ctx)
                
                # Log after successful execution
                log_context(result, "after", name, None, chain_name)
                return result
                
            except Exception as error:
                # Log error with context
                error_ctx = {**ctx, 'error': error}
                log_context(error_ctx, "error", name, error, chain_name)
                return error_ctx
        
        return wrapper
    return decorator

class LoggingConfig:
    """Configuration for logging behavior."""
    
    def __init__(self, 
                 log_before: bool = True,
                 log_after: bool = True, 
                 log_errors: bool = True,
                 log_chains: bool = True,
                 log_dir: str = "logs",
                 log_level: str = "DEBUG"):
        self.log_before = log_before
        self.log_after = log_after
        self.log_errors = log_errors
        self.log_chains = log_chains
        self.log_dir = log_dir
        self.log_level = log_level

# Global logging configuration
_logging_config = LoggingConfig()

def configure_logging(**kwargs):
    """Configure global logging settings."""
    global _logging_config
    for key, value in kwargs.items():
        if hasattr(_logging_config, key):
            setattr(_logging_config, key, value)

def get_logging_config() -> LoggingConfig:
    """Get current logging configuration."""
    return _logging_config
