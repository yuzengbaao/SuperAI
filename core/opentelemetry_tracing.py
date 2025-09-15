#!/usr/bin/env python3
"""
SuperAI OpenTelemetry分布式追踪集成
提供完整的分布式追踪、指标收集和日志关联功能
"""

import os
import time
from typing import Dict, Any, Optional, Callable
from functools import wraps
import logging

# OpenTelemetry核心组件
from opentelemetry import trace, metrics, baggage
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader, ConsoleMetricExporter
from opentelemetry.sdk.resources import Resource

# 导出器
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.exporter.zipkin.json import ZipkinExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.prometheus import PrometheusMetricReader

# 自动仪表化
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor

# 传播器
from opentelemetry.propagate import set_global_textmap
from opentelemetry.propagators.b3 import B3MultiFormat
from opentelemetry.propagators.jaeger import JaegerPropagator
from opentelemetry.propagators.composite import CompositePropagator

# 语义约定
from opentelemetry.semconv.trace import SpanAttributes
from opentelemetry.semconv.resource import ResourceAttributes

logger = logging.getLogger(__name__)

class SuperAITracing:
    """SuperAI分布式追踪管理器"""
    
    def __init__(self, service_name: str = "superai", service_version: str = "1.0.0"):
        self.service_name = service_name
        self.service_version = service_version
        self.tracer = None
        self.meter = None
        self._initialized = False
        
    def initialize(self, 
                  jaeger_endpoint: Optional[str] = None,
                  zipkin_endpoint: Optional[str] = None,
                  otlp_endpoint: Optional[str] = None,
                  enable_console: bool = False,
                  enable_prometheus: bool = True):
        """初始化OpenTelemetry追踪"""
        
        if self._initialized:
            logger.warning("OpenTelemetry already initialized")
            return
        
        # 创建资源
        resource = Resource.create({
            ResourceAttributes.SERVICE_NAME: self.service_name,
            ResourceAttributes.SERVICE_VERSION: self.service_version,
            ResourceAttributes.SERVICE_NAMESPACE: "superai",
            ResourceAttributes.SERVICE_INSTANCE_ID: os.getenv('HOSTNAME', 'localhost'),
            ResourceAttributes.DEPLOYMENT_ENVIRONMENT: os.getenv('ENVIRONMENT', 'development'),
            "superai.component": "microservice",
            "superai.team": "ai-platform"
        })
        
        # 设置追踪提供者
        trace_provider = TracerProvider(resource=resource)
        trace.set_tracer_provider(trace_provider)
        
        # 配置Span导出器
        span_processors = []
        
        # Jaeger导出器
        if jaeger_endpoint:
            jaeger_exporter = JaegerExporter(
                agent_host_name=jaeger_endpoint.split(':')[0],
                agent_port=int(jaeger_endpoint.split(':')[1]) if ':' in jaeger_endpoint else 14268,
                collector_endpoint=f"http://{jaeger_endpoint}/api/traces"
            )
            span_processors.append(BatchSpanProcessor(jaeger_exporter))
            logger.info(f"Jaeger exporter configured: {jaeger_endpoint}")
        
        # Zipkin导出器
        if zipkin_endpoint:
            zipkin_exporter = ZipkinExporter(
                endpoint=f"http://{zipkin_endpoint}/api/v2/spans"
            )
            span_processors.append(BatchSpanProcessor(zipkin_exporter))
            logger.info(f"Zipkin exporter configured: {zipkin_endpoint}")
        
        # OTLP导出器
        if otlp_endpoint:
            otlp_exporter = OTLPSpanExporter(
                endpoint=otlp_endpoint,
                insecure=True
            )
            span_processors.append(BatchSpanProcessor(otlp_exporter))
            logger.info(f"OTLP exporter configured: {otlp_endpoint}")
        
        # 控制台导出器（开发环境）
        if enable_console:
            console_exporter = ConsoleSpanExporter()
            span_processors.append(BatchSpanProcessor(console_exporter))
            logger.info("Console exporter enabled")
        
        # 添加所有Span处理器
        for processor in span_processors:
            trace_provider.add_span_processor(processor)
        
        # 设置指标提供者
        metric_readers = []
        
        # Prometheus指标读取器
        if enable_prometheus:
            prometheus_reader = PrometheusMetricReader()
            metric_readers.append(prometheus_reader)
            logger.info("Prometheus metrics reader enabled")
        
        # OTLP指标导出器
        if otlp_endpoint:
            otlp_metric_exporter = OTLPMetricExporter(
                endpoint=otlp_endpoint,
                insecure=True
            )
            otlp_metric_reader = PeriodicExportingMetricReader(
                exporter=otlp_metric_exporter,
                export_interval_millis=30000
            )
            metric_readers.append(otlp_metric_reader)
            logger.info("OTLP metrics exporter configured")
        
        # 控制台指标导出器（开发环境）
        if enable_console:
            console_metric_exporter = ConsoleMetricExporter()
            console_metric_reader = PeriodicExportingMetricReader(
                exporter=console_metric_exporter,
                export_interval_millis=60000
            )
            metric_readers.append(console_metric_reader)
        
        metrics_provider = MeterProvider(
            resource=resource,
            metric_readers=metric_readers
        )
        metrics.set_meter_provider(metrics_provider)
        
        # 设置传播器
        propagators = [
            JaegerPropagator(),
            B3MultiFormat()
        ]
        set_global_textmap(CompositePropagator(propagators))
        
        # 获取追踪器和指标器
        self.tracer = trace.get_tracer(self.service_name, self.service_version)
        self.meter = metrics.get_meter(self.service_name, self.service_version)
        
        # 设置自动仪表化
        self._setup_auto_instrumentation()
        
        self._initialized = True
        logger.info(f"OpenTelemetry initialized for service: {self.service_name}")
    
    def _setup_auto_instrumentation(self):
        """设置自动仪表化"""
        try:
            # Flask自动仪表化
            FlaskInstrumentor().instrument()
            logger.info("Flask auto-instrumentation enabled")
        except Exception as e:
            logger.warning(f"Flask instrumentation failed: {e}")
        
        try:
            # Requests自动仪表化
            RequestsInstrumentor().instrument()
            logger.info("Requests auto-instrumentation enabled")
        except Exception as e:
            logger.warning(f"Requests instrumentation failed: {e}")
        
        try:
            # Redis自动仪表化
            RedisInstrumentor().instrument()
            logger.info("Redis auto-instrumentation enabled")
        except Exception as e:
            logger.warning(f"Redis instrumentation failed: {e}")
        
        try:
            # 日志自动仪表化
            LoggingInstrumentor().instrument(set_logging_format=True)
            logger.info("Logging auto-instrumentation enabled")
        except Exception as e:
            logger.warning(f"Logging instrumentation failed: {e}")
    
    def create_span(self, name: str, 
                   kind: trace.SpanKind = trace.SpanKind.INTERNAL,
                   attributes: Optional[Dict[str, Any]] = None) -> trace.Span:
        """创建新的Span"""
        if not self._initialized:
            raise RuntimeError("OpenTelemetry not initialized")
        
        span = self.tracer.start_span(
            name=name,
            kind=kind,
            attributes=attributes or {}
        )
        return span
    
    def get_current_span(self) -> Optional[trace.Span]:
        """获取当前活跃的Span"""
        return trace.get_current_span()
    
    def get_trace_id(self) -> Optional[str]:
        """获取当前追踪ID"""
        span = self.get_current_span()
        if span and span.get_span_context().is_valid:
            return format(span.get_span_context().trace_id, '032x')
        return None
    
    def get_span_id(self) -> Optional[str]:
        """获取当前Span ID"""
        span = self.get_current_span()
        if span and span.get_span_context().is_valid:
            return format(span.get_span_context().span_id, '016x')
        return None
    
    def add_span_attribute(self, key: str, value: Any):
        """向当前Span添加属性"""
        span = self.get_current_span()
        if span:
            span.set_attribute(key, value)
    
    def add_span_event(self, name: str, attributes: Optional[Dict[str, Any]] = None):
        """向当前Span添加事件"""
        span = self.get_current_span()
        if span:
            span.add_event(name, attributes or {})
    
    def record_exception(self, exception: Exception):
        """记录异常到当前Span"""
        span = self.get_current_span()
        if span:
            span.record_exception(exception)
            span.set_status(trace.Status(trace.StatusCode.ERROR, str(exception)))
    
    def set_baggage(self, key: str, value: str):
        """设置Baggage"""
        baggage.set_baggage(key, value)
    
    def get_baggage(self, key: str) -> Optional[str]:
        """获取Baggage"""
        return baggage.get_baggage(key)

# 全局追踪实例
_tracing_instance: Optional[SuperAITracing] = None

def initialize_tracing(service_name: str = "superai", **kwargs) -> SuperAITracing:
    """初始化全局追踪实例"""
    global _tracing_instance
    
    if _tracing_instance is None:
        _tracing_instance = SuperAITracing(service_name)
        _tracing_instance.initialize(**kwargs)
    
    return _tracing_instance

def get_tracer() -> SuperAITracing:
    """获取全局追踪实例"""
    if _tracing_instance is None:
        raise RuntimeError("Tracing not initialized. Call initialize_tracing() first.")
    return _tracing_instance

def trace_function(name: Optional[str] = None, 
                  attributes: Optional[Dict[str, Any]] = None,
                  record_exception: bool = True):
    """函数追踪装饰器"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            tracer = get_tracer()
            span_name = name or f"{func.__module__}.{func.__name__}"
            
            span_attributes = {
                "function.name": func.__name__,
                "function.module": func.__module__,
                "function.args_count": len(args),
                "function.kwargs_count": len(kwargs)
            }
            
            if attributes:
                span_attributes.update(attributes)
            
            with tracer.tracer.start_as_current_span(
                span_name,
                kind=trace.SpanKind.INTERNAL,
                attributes=span_attributes
            ) as span:
                try:
                    # 记录函数开始事件
                    span.add_event("function.start")
                    
                    # 执行函数
                    result = func(*args, **kwargs)
                    
                    # 记录成功事件
                    span.add_event("function.success", {
                        "result.type": type(result).__name__
                    })
                    
                    span.set_status(trace.Status(trace.StatusCode.OK))
                    return result
                    
                except Exception as e:
                    # 记录异常
                    if record_exception:
                        span.record_exception(e)
                        span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                    
                    span.add_event("function.error", {
                        "error.type": type(e).__name__,
                        "error.message": str(e)
                    })
                    
                    raise
        
        return wrapper
    return decorator

def trace_ai_model_call(model_name: str, **extra_attributes):
    """AI模型调用追踪装饰器"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            tracer = get_tracer()
            
            attributes = {
                "ai.model.name": model_name,
                "ai.operation.type": "inference",
                "ai.system": "superai",
                **extra_attributes
            }
            
            # 尝试从参数中提取prompt信息
            if args and isinstance(args[0], str):
                attributes["ai.prompt.length"] = len(args[0])
            
            with tracer.tracer.start_as_current_span(
                f"ai.model.{model_name}.call",
                kind=trace.SpanKind.CLIENT,
                attributes=attributes
            ) as span:
                try:
                    start_time = time.time()
                    result = func(*args, **kwargs)
                    duration = time.time() - start_time
                    
                    # 记录响应信息
                    if isinstance(result, str):
                        span.set_attribute("ai.response.length", len(result))
                    
                    span.set_attribute("ai.response.duration_ms", duration * 1000)
                    span.add_event("ai.model.response_received")
                    
                    return result
                    
                except Exception as e:
                    span.record_exception(e)
                    span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                    raise
        
        return wrapper
    return decorator

def trace_tool_execution(tool_name: str, **extra_attributes):
    """工具执行追踪装饰器"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            tracer = get_tracer()
            
            attributes = {
                "tool.name": tool_name,
                "tool.operation": "execute",
                "tool.system": "superai",
                **extra_attributes
            }
            
            with tracer.tracer.start_as_current_span(
                f"tool.{tool_name}.execute",
                kind=trace.SpanKind.INTERNAL,
                attributes=attributes
            ) as span:
                try:
                    start_time = time.time()
                    result = func(*args, **kwargs)
                    duration = time.time() - start_time
                    
                    span.set_attribute("tool.execution.duration_ms", duration * 1000)
                    span.add_event("tool.execution.completed")
                    
                    return result
                    
                except Exception as e:
                    span.record_exception(e)
                    span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                    raise
        
        return wrapper
    return decorator

def trace_task_processing(task_type: str, **extra_attributes):
    """任务处理追踪装饰器"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            tracer = get_tracer()
            
            attributes = {
                "task.type": task_type,
                "task.operation": "process",
                "task.system": "superai",
                **extra_attributes
            }
            
            # 尝试从参数中提取任务ID
            if kwargs.get('task_id'):
                attributes["task.id"] = kwargs['task_id']
            
            with tracer.tracer.start_as_current_span(
                f"task.{task_type}.process",
                kind=trace.SpanKind.INTERNAL,
                attributes=attributes
            ) as span:
                try:
                    start_time = time.time()
                    result = func(*args, **kwargs)
                    duration = time.time() - start_time
                    
                    span.set_attribute("task.processing.duration_ms", duration * 1000)
                    span.add_event("task.processing.completed")
                    
                    return result
                    
                except Exception as e:
                    span.record_exception(e)
                    span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                    raise
        
        return wrapper
    return decorator

# 便捷函数
def get_current_trace_id() -> Optional[str]:
    """获取当前追踪ID"""
    try:
        tracer = get_tracer()
        return tracer.get_trace_id()
    except RuntimeError:
        return None

def get_current_span_id() -> Optional[str]:
    """获取当前Span ID"""
    try:
        tracer = get_tracer()
        return tracer.get_span_id()
    except RuntimeError:
        return None

def add_trace_attribute(key: str, value: Any):
    """向当前Span添加属性"""
    try:
        tracer = get_tracer()
        tracer.add_span_attribute(key, value)
    except RuntimeError:
        pass

def add_trace_event(name: str, attributes: Optional[Dict[str, Any]] = None):
    """向当前Span添加事件"""
    try:
        tracer = get_tracer()
        tracer.add_span_event(name, attributes)
    except RuntimeError:
        pass