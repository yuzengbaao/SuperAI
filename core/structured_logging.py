#!/usr/bin/env python3
"""
SuperAI 结构化日志系统
提供统一的结构化日志记录和分布式追踪支持
"""

import json
import logging
import time
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, Union
from contextvars import ContextVar
from functools import wraps
import threading
import os

# 上下文变量用于存储追踪信息
trace_context: ContextVar[Dict[str, Any]] = ContextVar('trace_context', default={})
request_context: ContextVar[Dict[str, Any]] = ContextVar('request_context', default={})

class StructuredFormatter(logging.Formatter):
    """结构化日志格式化器"""
    
    def __init__(self, service_name: str = "superai", version: str = "1.0.0"):
        super().__init__()
        self.service_name = service_name
        self.version = version
        self.hostname = os.getenv('HOSTNAME', 'localhost')
        
    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录为JSON结构"""
        
        # 获取当前追踪上下文
        trace_ctx = trace_context.get({})
        request_ctx = request_context.get({})
        
        # 基础日志结构
        log_entry = {
            # 时间戳信息
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "@timestamp": datetime.utcnow().isoformat() + "Z",
            
            # 服务信息
            "service": {
                "name": self.service_name,
                "version": self.version,
                "hostname": self.hostname,
                "environment": os.getenv('ENVIRONMENT', 'development')
            },
            
            # 日志级别和消息
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            
            # 代码位置信息
            "source": {
                "file": record.pathname,
                "line": record.lineno,
                "function": record.funcName,
                "module": record.module
            },
            
            # 线程信息
            "thread": {
                "id": record.thread,
                "name": record.threadName
            },
            
            # 进程信息
            "process": {
                "id": record.process,
                "name": record.processName
            }
        }
        
        # 添加追踪信息
        if trace_ctx:
            log_entry["trace"] = {
                "trace_id": trace_ctx.get('trace_id'),
                "span_id": trace_ctx.get('span_id'),
                "parent_span_id": trace_ctx.get('parent_span_id'),
                "operation_name": trace_ctx.get('operation_name'),
                "tags": trace_ctx.get('tags', {})
            }
        
        # 添加请求上下文
        if request_ctx:
            log_entry["request"] = {
                "id": request_ctx.get('request_id'),
                "method": request_ctx.get('method'),
                "path": request_ctx.get('path'),
                "user_id": request_ctx.get('user_id'),
                "session_id": request_ctx.get('session_id'),
                "ip_address": request_ctx.get('ip_address'),
                "user_agent": request_ctx.get('user_agent')
            }
        
        # 添加异常信息
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": self.formatException(record.exc_info)
            }
        
        # 添加自定义字段
        if hasattr(record, 'extra_fields'):
            log_entry.update(record.extra_fields)
        
        # 添加性能指标
        if hasattr(record, 'duration'):
            log_entry["performance"] = {
                "duration_ms": record.duration * 1000,
                "duration_seconds": record.duration
            }
        
        # 添加业务标签
        if hasattr(record, 'business_tags'):
            log_entry["business"] = record.business_tags
        
        return json.dumps(log_entry, ensure_ascii=False, separators=(',', ':'))

class StructuredLogger:
    """结构化日志记录器"""
    
    def __init__(self, name: str, service_name: str = "superai"):
        self.logger = logging.getLogger(name)
        self.service_name = service_name
        
        # 配置结构化格式化器
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = StructuredFormatter(service_name)
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def _log_with_context(self, level: int, message: str, 
                         extra_fields: Optional[Dict[str, Any]] = None,
                         business_tags: Optional[Dict[str, Any]] = None,
                         duration: Optional[float] = None,
                         **kwargs):
        """带上下文的日志记录"""
        
        extra = {}
        if extra_fields:
            extra['extra_fields'] = extra_fields
        if business_tags:
            extra['business_tags'] = business_tags
        if duration is not None:
            extra['duration'] = duration
        
        self.logger.log(level, message, extra=extra, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """调试日志"""
        self._log_with_context(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """信息日志"""
        self._log_with_context(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """警告日志"""
        self._log_with_context(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """错误日志"""
        self._log_with_context(logging.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """严重错误日志"""
        self._log_with_context(logging.CRITICAL, message, **kwargs)
    
    def exception(self, message: str, **kwargs):
        """异常日志"""
        self._log_with_context(logging.ERROR, message, exc_info=True, **kwargs)

class TraceContext:
    """追踪上下文管理器"""
    
    def __init__(self, operation_name: str, 
                 trace_id: Optional[str] = None,
                 parent_span_id: Optional[str] = None,
                 tags: Optional[Dict[str, Any]] = None):
        self.operation_name = operation_name
        self.trace_id = trace_id or self._generate_trace_id()
        self.span_id = self._generate_span_id()
        self.parent_span_id = parent_span_id
        self.tags = tags or {}
        self.start_time = time.time()
        self.token = None
    
    def _generate_trace_id(self) -> str:
        """生成追踪ID"""
        return str(uuid.uuid4()).replace('-', '')
    
    def _generate_span_id(self) -> str:
        """生成Span ID"""
        return str(uuid.uuid4()).replace('-', '')[:16]
    
    def __enter__(self):
        """进入上下文"""
        ctx = {
            'trace_id': self.trace_id,
            'span_id': self.span_id,
            'parent_span_id': self.parent_span_id,
            'operation_name': self.operation_name,
            'tags': self.tags,
            'start_time': self.start_time
        }
        self.token = trace_context.set(ctx)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文"""
        if self.token:
            trace_context.reset(self.token)
        
        # 记录Span完成
        duration = time.time() - self.start_time
        logger = StructuredLogger(f"trace.{self.operation_name}")
        
        if exc_type:
            logger.error(
                f"Operation {self.operation_name} failed",
                duration=duration,
                business_tags={
                    "operation": self.operation_name,
                    "status": "error",
                    "error_type": exc_type.__name__ if exc_type else None
                }
            )
        else:
            logger.info(
                f"Operation {self.operation_name} completed",
                duration=duration,
                business_tags={
                    "operation": self.operation_name,
                    "status": "success"
                }
            )
    
    def add_tag(self, key: str, value: Any):
        """添加标签"""
        self.tags[key] = value
        # 更新上下文
        ctx = trace_context.get({})
        ctx['tags'] = self.tags
        trace_context.set(ctx)
    
    def log_event(self, event_name: str, **kwargs):
        """记录事件"""
        logger = StructuredLogger(f"event.{event_name}")
        logger.info(
            f"Event: {event_name}",
            business_tags={
                "event_name": event_name,
                "operation": self.operation_name,
                **kwargs
            }
        )

class RequestContext:
    """请求上下文管理器"""
    
    def __init__(self, request_id: Optional[str] = None, **kwargs):
        self.request_id = request_id or str(uuid.uuid4())
        self.context_data = kwargs
        self.token = None
    
    def __enter__(self):
        """进入上下文"""
        ctx = {
            'request_id': self.request_id,
            **self.context_data
        }
        self.token = request_context.set(ctx)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文"""
        if self.token:
            request_context.reset(self.token)

def trace_operation(operation_name: str, tags: Optional[Dict[str, Any]] = None):
    """操作追踪装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with TraceContext(operation_name, tags=tags) as trace:
                # 添加函数参数作为标签
                if args:
                    trace.add_tag('args_count', len(args))
                if kwargs:
                    trace.add_tag('kwargs_keys', list(kwargs.keys()))
                
                try:
                    result = func(*args, **kwargs)
                    trace.add_tag('result_type', type(result).__name__)
                    return result
                except Exception as e:
                    trace.add_tag('error', str(e))
                    raise
        return wrapper
    return decorator

def log_performance(operation_name: str):
    """性能日志装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            logger = StructuredLogger(f"performance.{operation_name}")
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                logger.info(
                    f"Performance: {operation_name} completed",
                    duration=duration,
                    business_tags={
                        "operation": operation_name,
                        "status": "success",
                        "function": func.__name__
                    }
                )
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(
                    f"Performance: {operation_name} failed",
                    duration=duration,
                    business_tags={
                        "operation": operation_name,
                        "status": "error",
                        "function": func.__name__,
                        "error": str(e)
                    }
                )
                raise
        return wrapper
    return decorator

# 全局日志记录器实例
_loggers = {}
_lock = threading.Lock()

def get_logger(name: str, service_name: str = "superai") -> StructuredLogger:
    """获取结构化日志记录器"""
    with _lock:
        key = f"{service_name}.{name}"
        if key not in _loggers:
            _loggers[key] = StructuredLogger(name, service_name)
        return _loggers[key]

def setup_logging(service_name: str = "superai", 
                 log_level: str = "INFO",
                 log_format: str = "structured"):
    """设置全局日志配置"""
    
    # 设置根日志级别
    level = getattr(logging, log_level.upper(), logging.INFO)
    logging.getLogger().setLevel(level)
    
    # 如果是结构化格式，配置所有现有的日志记录器
    if log_format == "structured":
        for logger_name in logging.Logger.manager.loggerDict:
            logger = logging.getLogger(logger_name)
            if not logger.handlers:
                handler = logging.StreamHandler()
                formatter = StructuredFormatter(service_name)
                handler.setFormatter(formatter)
                logger.addHandler(handler)
                logger.setLevel(level)

# 便捷函数
def create_trace(operation_name: str, **kwargs) -> TraceContext:
    """创建追踪上下文"""
    return TraceContext(operation_name, **kwargs)

def create_request_context(request_id: Optional[str] = None, **kwargs) -> RequestContext:
    """创建请求上下文"""
    return RequestContext(request_id, **kwargs)

def get_current_trace_id() -> Optional[str]:
    """获取当前追踪ID"""
    ctx = trace_context.get({})
    return ctx.get('trace_id')

def get_current_request_id() -> Optional[str]:
    """获取当前请求ID"""
    ctx = request_context.get({})
    return ctx.get('request_id')