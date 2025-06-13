"""
Context Logger for ModuLink Chains

Provides comprehensive logging of context flow through ModuLink chains,
including full serialization of complex objects like numpy arrays and MediaPipe detectors.
"""

import json
import logging
import os
import uuid
from datetime import datetime
from typing import Any, Dict, Optional
import numpy as np
import cv2
import inspect
from modulink import Ctx

class ContextJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles complex objects in ModuLink contexts."""
    
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return {
                "_type": "numpy.ndarray",
                "shape": obj.shape,
                "dtype": str(obj.dtype),
                "data": obj.tolist() if obj.size < 10000 else f"<large_array_shape_{obj.shape}>",
                "size": obj.size
            }
        elif hasattr(obj, '__class__') and 'mediapipe' in str(type(obj)):
            return {
                "_type": "mediapipe.object",
                "class": str(type(obj)),
                "repr": repr(obj)
            }
        elif hasattr(obj, '__class__') and 'cv2' in str(type(obj)):
            return {
                "_type": "opencv.object", 
                "class": str(type(obj)),
                "repr": repr(obj)
            }
        elif callable(obj):
            return {
                "_type": "callable",
                "name": getattr(obj, '__name__', str(obj)),
                "module": getattr(obj, '__module__', 'unknown')
            }
        elif hasattr(obj, '__dict__'):
            # For custom objects, serialize their attributes
            try:
                return {
                    "_type": "custom_object",
                    "class": str(type(obj)),
                    "attributes": {k: v for k, v in obj.__dict__.items() if not k.startswith('_')}
                }
            except:
                return {
                    "_type": "custom_object",
                    "class": str(type(obj)),
                    "repr": repr(obj)
                }
        else:
            # Fallback for anything else
            try:
                return str(obj)
            except:
                return f"<unserializable_object_{type(obj)}>"

class ContextLogger:
    """Comprehensive context logger for ModuLink chains."""
    
    def __init__(self, log_dir: str = "logs", log_level: str = "DEBUG"):
        self.log_dir = log_dir
        self.execution_id = str(uuid.uuid4())
        self.setup_logging(log_level)
        
        # Ensure log directory exists
        os.makedirs(log_dir, exist_ok=True)
        
        # Create log file with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = os.path.join(log_dir, f"context_{timestamp}_{self.execution_id[:8]}.jsonl")
        
        # Track chain execution
        self.chain_stack = []
        self.link_counter = 0
    
    def setup_logging(self, log_level: str):
        """Setup Python logging configuration."""
        # Ensure log directory exists before creating file handlers
        os.makedirs(self.log_dir, exist_ok=True)
        
        self.logger = logging.getLogger(f"context_logger_{self.execution_id[:8]}")
        self.logger.setLevel(getattr(logging, log_level.upper(), logging.DEBUG))
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_format = logging.Formatter(
            '%(asctime)s - CONTEXT - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_format)
        self.logger.addHandler(console_handler)
        
        # File handler
        file_handler = logging.FileHandler(
            os.path.join(self.log_dir, f"context_summary_{datetime.now().strftime('%Y%m%d')}.log")
        )
        file_handler.setLevel(logging.DEBUG)
        file_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_format)
        self.logger.addHandler(file_handler)
    
    def get_caller_info(self):
        """Get information about the calling function."""
        frame = inspect.currentframe()
        try:
            # Go up the stack to find the actual calling function
            # Skip: get_caller_info -> log_context -> middleware -> actual_function
            for i in range(4):
                frame = frame.f_back
                if frame is None:
                    break
            
            if frame:
                return {
                    "file": frame.f_code.co_filename,
                    "function": frame.f_code.co_name,
                    "line": frame.f_lineno
                }
        finally:
            del frame
        
        return {"file": "unknown", "function": "unknown", "line": 0}
    
    def serialize_context(self, ctx: Ctx) -> Dict[str, Any]:
        """Serialize context to JSON-compatible format."""
        try:
            # Create a copy and serialize
            serialized = json.loads(json.dumps(ctx, cls=ContextJSONEncoder, indent=2))
            return serialized
        except Exception as e:
            self.logger.error(f"Failed to serialize context: {e}")
            return {
                "_serialization_error": str(e),
                "_context_keys": list(ctx.keys()) if isinstance(ctx, dict) else "not_dict",
                "_context_type": str(type(ctx))
            }
    
    def log_context(self, ctx: Ctx, phase: str, link_name: str = "unknown", 
                   error: Optional[Exception] = None, chain_name: str = "unknown"):
        """Log complete context with metadata."""
        self.link_counter += 1
        
        # Get caller information
        caller_info = self.get_caller_info()
        
        # Create log entry
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "execution_id": self.execution_id,
            "link_counter": self.link_counter,
            "chain_name": chain_name,
            "link_name": link_name,
            "phase": phase,  # "before", "after", "error"
            "context": self.serialize_context(ctx),
            "metadata": {
                "caller_file": caller_info["file"],
                "caller_function": caller_info["function"], 
                "caller_line": caller_info["line"],
                "chain_stack": self.chain_stack.copy()
            }
        }
        
        # Add error information if present
        if error:
            log_entry["error"] = {
                "type": type(error).__name__,
                "message": str(error),
                "repr": repr(error)
            }
        
        # Write to JSONL file
        try:
            with open(self.log_file, 'a') as f:
                f.write(json.dumps(log_entry, cls=ContextJSONEncoder) + '\n')
        except Exception as e:
            self.logger.error(f"Failed to write to log file: {e}")
        
        # Console summary
        summary = f"{phase.upper()} {link_name} | Keys: {list(ctx.keys()) if isinstance(ctx, dict) else 'N/A'}"
        if error:
            summary += f" | ERROR: {error}"
        
        if phase == "error":
            self.logger.error(summary)
        elif phase == "before":
            self.logger.debug(summary)
        else:
            self.logger.info(summary)
    
    def enter_chain(self, chain_name: str):
        """Mark entering a chain."""
        self.chain_stack.append(chain_name)
        self.logger.info(f"🔗 ENTERING CHAIN: {chain_name}")
    
    def exit_chain(self, chain_name: str):
        """Mark exiting a chain."""
        if self.chain_stack and self.chain_stack[-1] == chain_name:
            self.chain_stack.pop()
        self.logger.info(f"✅ COMPLETED CHAIN: {chain_name}")
    
    def get_log_summary(self) -> Dict[str, Any]:
        """Get summary of logging session."""
        return {
            "execution_id": self.execution_id,
            "log_file": self.log_file,
            "total_links_executed": self.link_counter,
            "current_chain_stack": self.chain_stack
        }

# Global logger instance
_context_logger: Optional[ContextLogger] = None

def get_context_logger() -> ContextLogger:
    """Get the global context logger instance."""
    global _context_logger
    if _context_logger is None:
        _context_logger = ContextLogger()
    return _context_logger

def init_context_logger(log_dir: str = "logs", log_level: str = "DEBUG") -> ContextLogger:
    """Initialize a new context logger."""
    global _context_logger
    _context_logger = ContextLogger(log_dir, log_level)
    return _context_logger

def log_context(ctx: Ctx, phase: str, link_name: str = "unknown", 
               error: Optional[Exception] = None, chain_name: str = "unknown"):
    """Convenience function to log context."""
    logger = get_context_logger()
    logger.log_context(ctx, phase, link_name, error, chain_name)

def enter_chain(chain_name: str):
    """Convenience function to mark entering a chain."""
    logger = get_context_logger()
    logger.enter_chain(chain_name)

def exit_chain(chain_name: str):
    """Convenience function to mark exiting a chain."""
    logger = get_context_logger()
    logger.exit_chain(chain_name)
