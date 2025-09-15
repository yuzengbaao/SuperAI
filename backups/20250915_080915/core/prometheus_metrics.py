#!/usr/bin/env python3
"""
SuperAI Prometheus监控指标模块
为SuperAI系统提供统一的监控指标收集和暴露功能
"""

import time
import functools
from typing import Dict, Any, Optional, Callable
from prometheus_client import (
    Counter, Histogram, Gauge, Info, Enum,
    CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST,
    start_http_server
)
import logging
import threading
from datetime import datetime

logger = logging.getLogger(__name__)

class SuperAIMetrics:
    """SuperAI系统监控指标收集器"""
    
    def __init__(self, service_name: str, registry: Optional[CollectorRegistry] = None):
        self.service_name = service_name
        self.registry = registry or CollectorRegistry()
        self._setup_metrics()
        
    def _setup_metrics(self):
        """初始化监控指标"""
        
        # === 系统信息指标 ===
        self.service_info = Info(
            'superai_service_info',
            'SuperAI服务基本信息',
            registry=self.registry
        )
        
        # === 请求相关指标 ===
        self.request_total = Counter(
            'superai_requests_total',
            'HTTP请求总数',
            ['method', 'endpoint', 'status_code'],
            registry=self.registry
        )
        
        self.request_duration = Histogram(
            'superai_request_duration_seconds',
            'HTTP请求处理时间',
            ['method', 'endpoint'],
            buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0],
            registry=self.registry
        )
        
        # === 任务处理指标 ===
        self.task_total = Counter(
            'superai_tasks_total',
            '任务处理总数',
            ['task_type', 'status'],
            registry=self.registry
        )
        
        self.task_duration = Histogram(
            'superai_task_duration_seconds',
            '任务处理时间',
            ['task_type'],
            buckets=[1.0, 5.0, 10.0, 30.0, 60.0, 300.0],
            registry=self.registry
        )
        
        self.active_tasks = Gauge(
            'superai_active_tasks',
            '当前活跃任务数',
            ['task_type'],
            registry=self.registry
        )
        
        # === EventBus指标 ===
        self.eventbus_messages_total = Counter(
            'superai_eventbus_messages_total',
            'EventBus消息总数',
            ['event_type', 'direction'],  # direction: sent/received
            registry=self.registry
        )
        
        self.eventbus_message_duration = Histogram(
            'superai_eventbus_message_duration_seconds',
            'EventBus消息处理时间',
            ['event_type'],
            buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 5.0],
            registry=self.registry
        )
        
        # === Redis连接指标 ===
        self.redis_connections = Gauge(
            'superai_redis_connections',
            'Redis连接数',
            registry=self.registry
        )
        
        self.redis_operations_total = Counter(
            'superai_redis_operations_total',
            'Redis操作总数',
            ['operation', 'status'],
            registry=self.registry
        )
        
        # === AI模型指标 ===
        self.ai_model_requests_total = Counter(
            'superai_ai_model_requests_total',
            'AI模型请求总数',
            ['model_name', 'status'],
            registry=self.registry
        )
        
        self.ai_model_response_time = Histogram(
            'superai_ai_model_response_time_seconds',
            'AI模型响应时间',
            ['model_name'],
            buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
            registry=self.registry
        )
        
        self.ai_model_tokens = Histogram(
            'superai_ai_model_tokens',
            'AI模型Token使用量',
            ['model_name', 'token_type'],  # token_type: input/output
            buckets=[10, 50, 100, 500, 1000, 5000],
            registry=self.registry
        )
        
        # === 工具执行指标 ===
        self.tool_executions_total = Counter(
            'superai_tool_executions_total',
            '工具执行总数',
            ['tool_name', 'status'],
            registry=self.registry
        )
        
        self.tool_execution_duration = Histogram(
            'superai_tool_execution_duration_seconds',
            '工具执行时间',
            ['tool_name'],
            buckets=[0.1, 0.5, 1.0, 5.0, 10.0, 30.0],
            registry=self.registry
        )
        
        # === 系统资源指标 ===
        self.memory_usage = Gauge(
            'superai_memory_usage_bytes',
            '内存使用量',
            registry=self.registry
        )
        
        self.cpu_usage = Gauge(
            'superai_cpu_usage_percent',
            'CPU使用率',
            registry=self.registry
        )
        
        # === 健康状态指标 ===
        self.health_status = Enum(
            'superai_health_status',
            '服务健康状态',
            states=['healthy', 'unhealthy', 'degraded'],
            registry=self.registry
        )
        
        self.last_health_check = Gauge(
            'superai_last_health_check_timestamp',
            '最后健康检查时间戳',
            registry=self.registry
        )
        
        # 设置服务信息
        self.service_info.info({
            'service_name': self.service_name,
            'version': '1.0.0',
            'build_time': datetime.now().isoformat(),
            'python_version': '3.11+'
        })
        
        # 初始化健康状态
        self.health_status.state('healthy')
        self.last_health_check.set_to_current_time()
        
    def record_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """记录HTTP请求指标"""
        self.request_total.labels(
            method=method,
            endpoint=endpoint,
            status_code=str(status_code)
        ).inc()
        
        self.request_duration.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)
        
    def record_task(self, task_type: str, status: str, duration: Optional[float] = None):
        """记录任务处理指标"""
        self.task_total.labels(
            task_type=task_type,
            status=status
        ).inc()
        
        if duration is not None:
            self.task_duration.labels(task_type=task_type).observe(duration)
            
    def set_active_tasks(self, task_type: str, count: int):
        """设置活跃任务数"""
        self.active_tasks.labels(task_type=task_type).set(count)
        
    def record_eventbus_message(self, event_type: str, direction: str, duration: Optional[float] = None):
        """记录EventBus消息指标"""
        self.eventbus_messages_total.labels(
            event_type=event_type,
            direction=direction
        ).inc()
        
        if duration is not None:
            self.eventbus_message_duration.labels(event_type=event_type).observe(duration)
            
    def set_redis_connections(self, count: int):
        """设置Redis连接数"""
        self.redis_connections.set(count)
        
    def record_redis_operation(self, operation: str, status: str):
        """记录Redis操作"""
        self.redis_operations_total.labels(
            operation=operation,
            status=status
        ).inc()
        
    def record_ai_model_request(self, model_name: str, status: str, response_time: float, 
                               input_tokens: int = 0, output_tokens: int = 0):
        """记录AI模型请求指标"""
        self.ai_model_requests_total.labels(
            model_name=model_name,
            status=status
        ).inc()
        
        self.ai_model_response_time.labels(model_name=model_name).observe(response_time)
        
        if input_tokens > 0:
            self.ai_model_tokens.labels(
                model_name=model_name,
                token_type='input'
            ).observe(input_tokens)
            
        if output_tokens > 0:
            self.ai_model_tokens.labels(
                model_name=model_name,
                token_type='output'
            ).observe(output_tokens)
            
    def record_tool_execution(self, tool_name: str, status: str, duration: float):
        """记录工具执行指标"""
        self.tool_executions_total.labels(
            tool_name=tool_name,
            status=status
        ).inc()
        
        self.tool_execution_duration.labels(tool_name=tool_name).observe(duration)
        
    def update_system_metrics(self, memory_bytes: int, cpu_percent: float):
        """更新系统资源指标"""
        self.memory_usage.set(memory_bytes)
        self.cpu_usage.set(cpu_percent)
        
    def set_health_status(self, status: str):
        """设置健康状态"""
        self.health_status.state(status)
        self.last_health_check.set_to_current_time()
        
    def get_metrics(self) -> str:
        """获取Prometheus格式的指标数据"""
        return generate_latest(self.registry)
        
    def start_metrics_server(self, port: int = 8080):
        """启动指标暴露服务器"""
        try:
            start_http_server(port, registry=self.registry)
            logger.info(f"Prometheus指标服务器已启动，端口: {port}")
        except Exception as e:
            logger.error(f"启动Prometheus指标服务器失败: {e}")
            

def metrics_decorator(metrics: SuperAIMetrics, metric_type: str = 'request'):
    """监控装饰器"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            status = 'success'
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                status = 'error'
                raise
            finally:
                duration = time.time() - start_time
                
                if metric_type == 'request':
                    # 从函数名或参数中提取信息
                    method = kwargs.get('method', 'GET')
                    endpoint = kwargs.get('endpoint', func.__name__)
                    status_code = 200 if status == 'success' else 500
                    metrics.record_request(method, endpoint, status_code, duration)
                    
                elif metric_type == 'task':
                    task_type = kwargs.get('task_type', func.__name__)
                    metrics.record_task(task_type, status, duration)
                    
                elif metric_type == 'tool':
                    tool_name = kwargs.get('tool_name', func.__name__)
                    metrics.record_tool_execution(tool_name, status, duration)
                    
        return wrapper
    return decorator


class MetricsMiddleware:
    """Flask监控中间件"""
    
    def __init__(self, app, metrics: SuperAIMetrics):
        self.app = app
        self.metrics = metrics
        self.setup_middleware()
        
    def setup_middleware(self):
        """设置Flask中间件"""
        @self.app.before_request
        def before_request():
            from flask import g
            g.start_time = time.time()
            
        @self.app.after_request
        def after_request(response):
            from flask import request, g
            
            if hasattr(g, 'start_time'):
                duration = time.time() - g.start_time
                self.metrics.record_request(
                    method=request.method,
                    endpoint=request.endpoint or 'unknown',
                    status_code=response.status_code,
                    duration=duration
                )
                
            return response
            
        # 添加指标端点
        @self.app.route('/metrics')
        def metrics_endpoint():
            from flask import Response
            return Response(
                self.metrics.get_metrics(),
                mimetype=CONTENT_TYPE_LATEST
            )


# 全局指标实例
_metrics_instances: Dict[str, SuperAIMetrics] = {}
_lock = threading.Lock()

def get_metrics(service_name: str) -> SuperAIMetrics:
    """获取或创建指标实例"""
    with _lock:
        if service_name not in _metrics_instances:
            _metrics_instances[service_name] = SuperAIMetrics(service_name)
        return _metrics_instances[service_name]


def setup_metrics_for_flask_app(app, service_name: str, metrics_port: int = 8080):
    """为Flask应用设置监控"""
    metrics = get_metrics(service_name)
    
    # 设置中间件
    MetricsMiddleware(app, metrics)
    
    # 启动指标服务器（在单独线程中）
    def start_metrics_server():
        try:
            metrics.start_metrics_server(metrics_port)
        except Exception as e:
            logger.error(f"启动指标服务器失败: {e}")
            
    metrics_thread = threading.Thread(
        target=start_metrics_server,
        daemon=True,
        name=f'metrics-server-{service_name}'
    )
    metrics_thread.start()
    
    logger.info(f"已为 {service_name} 设置Prometheus监控，指标端口: {metrics_port}")
    
    return metrics