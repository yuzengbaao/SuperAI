# SuperAI - Multi-Agent AI System

<div align="center">

![SuperAI Logo](https://img.shields.io/badge/SuperAI-Multi--Agent%20System-blue?style=for-the-badge)
![Version](https://img.shields.io/badge/version-1.0.0-green?style=for-the-badge)
![License](https://img.shields.io/badge/license-MIT-blue?style=for-the-badge)
![Docker](https://img.shields.io/badge/docker-ready-blue?style=for-the-badge&logo=docker)
![Python](https://img.shields.io/badge/python-3.11+-blue?style=for-the-badge&logo=python)

**A Production-Ready Multi-Agent AI System with Event-Driven Architecture**

[Features](#features) • [Quick Start](#quick-start) • [Documentation](#documentation) • [Contributing](#contributing) • [License](#license)

</div>

## 🚀 Overview

SuperAI is a sophisticated multi-agent artificial intelligence system built with a microservices architecture. It provides a scalable, event-driven platform for complex AI task processing, featuring intelligent task planning, distributed execution, and comprehensive monitoring.

### Key Highlights

- 🤖 **Multi-Agent Coordination**: Intelligent task planning and execution across multiple AI agents
- 🔄 **Event-Driven Architecture**: Redis-based EventBus for real-time communication
- 🐳 **Optimized Containerization**: Advanced Docker build system with 99%+ build time reduction
- 📊 **Production Monitoring**: Prometheus + Grafana monitoring stack
- ⚡ **High Performance**: Threading-based concurrent processing with unified architecture
- 🔧 **Unified Dependencies**: Streamlined dependency management with single requirements.txt
- 🛡️ **Production Ready**: Enhanced security, performance, and maintainability

## ✨ Features

### 🧠 Intelligent Agent System
- **Agent Planner**: Intelligent task analysis and execution plan generation
- **Agent Executor**: Distributed task execution with tool integration
- **Multi-Agent Coordination**: Seamless collaboration between specialized agents
- **Task Retry Mechanism**: Automatic retry with exponential backoff for failed tasks

### 🔧 Integrated Tools
- **Web Search**: Tavily API integration for real-time information retrieval
- **File Operations**: Comprehensive file management and processing
- **Mathematical Computing**: Advanced calculation and data analysis
- **Custom Tool Framework**: Easy integration of new tools and capabilities

### 🏗️ System Architecture

#### Core Services
- **agent-planner**: Task planning and coordination service
- **agent-executor**: Task execution and tool integration service
- **agi-qwen-service**: Large language model service (Core AI Engine)
- **agi-redis-lb**: Redis EventBus for inter-service communication

#### Infrastructure Services
- **agi-prometheus**: Metrics collection and monitoring
- **agi-grafana**: Visualization and dashboards
- **health-check-proxy**: Service health monitoring
- **Load Balancers**: NGINX-based load balancing for high availability

#### Monitoring & Management
- **agi-evolution-manager**: System evolution and learning management
- **agi-comprehensive-monitoring-enhanced**: Enhanced monitoring capabilities
- **agi-test-validation**: Automated testing and validation

## 📁 Project Structure

```
SuperAI/
├── 📂 core/                    # Core system components
│   ├── event_bus.py           # Redis EventBus implementation
│   ├── tools.py               # Tool integration framework
│   ├── web_tools.py           # Web search and API tools
│   └── file_tools.py          # File operation utilities
├── 📂 microservices/          # Microservice implementations
│   ├── agent-planner/         # Task planning service
│   ├── agent-executor/        # Task execution service
│   ├── agi-qwen-service/      # LLM service
│   └── [other services]/      # Additional microservices
├── 📂 scripts/                # Utility scripts
│   ├── start_multi_agent_task.py  # Task creation script
│   └── debug_*.py             # Debugging utilities
├── 📂 config/                 # Configuration files
├── 📂 docs/                   # Documentation
├── 📂 models/                 # AI model files
├── docker-compose.yml         # Service orchestration
├── .env                       # Environment configuration
└── README.md                  # This file
```

## 🚀 Quick Start

### Prerequisites

- **Docker Engine** 20.10+
- **Docker Compose** 2.0+
- **Python** 3.11+ (for development)
- **PowerShell** 5.0+ (Windows) or **Bash** (Linux/macOS)
- **Git** (for cloning)

### 🎯 Fast Installation (Recommended)

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/SuperAI.git
   cd SuperAI
   ```

2. **One-command build and start** ⚡
   ```powershell
   # Windows (PowerShell)
   .\build.ps1 && docker-compose up -d
   
   # Linux/macOS
   ./build.sh && docker-compose up -d
   ```

3. **Verify system health** ✅
   ```bash
   # Check service health (should return 200)
   curl http://localhost:8300/health  # agent-planner
   curl http://localhost:8400/health  # agent-executor
   
   # View monitoring dashboard
   open http://localhost:3000  # Grafana (admin/admin)
   ```

### 🔧 Development Setup

1. **Install dependencies**
   ```bash
   # Unified dependency management
   pip install -r requirements.txt
   ```

2. **Custom build options**
   ```powershell
   # Build specific services
   .\build.ps1 -Target base      # Build base image only
   .\build.ps1 -Target planner   # Build agent-planner
   .\build.ps1 -Target executor  # Build agent-executor
   
   # Development builds
   .\build.ps1 -Clean            # Clean build
   .\build.ps1 -NoCache          # No cache build
   ```

3. **Environment configuration**
   ```bash
   cp .env.example .env
   # Edit .env file with your API keys and configuration
   ```

### Basic Usage

#### Creating and Running Tasks

```bash
# Create a simple task
python scripts/start_multi_agent_task.py "Write a summary about artificial intelligence"

# Create a web search task
python scripts/start_multi_agent_task.py "Search: latest developments in quantum computing"

# Create a file operation task
python scripts/start_multi_agent_task.py "Create file: /tmp/report.txt with current system status"

# Create a mathematical computation task
python scripts/start_multi_agent_task.py "Calculate: What is the compound interest on $10,000 at 5% for 10 years?"
```

#### Monitoring Tasks

```bash
# View real-time logs
docker-compose logs -f agent-planner
docker-compose logs -f agent-executor

# Check system status
docker-compose ps

# View resource usage
docker stats
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file with the following configuration:

```bash
# Redis Configuration
REDIS_HOST=agi-redis-lb
REDIS_PORT=6379

# API Keys
TAVILY_API_KEY=your_tavily_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# Service Ports
AGENT_PLANNER_PORT=8300
AGENT_EXECUTOR_PORT=8400
GRAFANA_PORT=3000
PROMETHEUS_PORT=9090

# Logging
LOG_LEVEL=INFO
```

### Service Ports

| Service | Port | Description |
|---------|------|-------------|
| agent-planner | 8300 | Task planning service |
| agent-executor | 8400 | Task execution service |
| agi-qwen-service | 8201 | LLM service |
| Grafana | 3000 | Monitoring dashboard |
| Prometheus | 9090 | Metrics collection |
| Redis | 6379 | EventBus and caching |
| Health Check Proxy | 8105 | Health monitoring |

## 🛠️ Development

### Local Development Setup

1. **Install Python dependencies**
   ```bash
   pip install -r core/requirements.txt
   pip install -r microservices/agent-planner/requirements.txt
   pip install -r microservices/agent-executor/requirements.txt
   ```

2. **Run services individually**
   ```bash
   # Start Redis first
   docker-compose up -d agi-redis-lb
   
   # Run agent-planner locally
   cd microservices/agent-planner
   python app.py
   
   # Run agent-executor locally
   cd microservices/agent-executor
   python app.py
   ```

3. **Development tools**
   ```bash
   # Debug event listener
   python scripts/debug_event_listener.py
   
   # Test tool integration
   python scripts/test_tool_integration.py
   
   # Manual Redis operations
   python scripts/simple_redis_publish.py
   python scripts/simple_redis_subscribe.py
   ```

### Adding New Tools

1. **Create tool class in `core/tools.py`**
   ```python
   class MyCustomTool(BaseTool):
       def __init__(self):
           super().__init__("my_custom_tool", "Description of my tool")
       
       def execute(self, **kwargs):
           # Tool implementation
           return {"result": "success", "data": "..."}
   ```

2. **Register tool in agent-executor**
   ```python
   # In microservices/agent-executor/app.py
   from core.tools import MyCustomTool
   
   # Add to tool registry
   tool_registry["my_custom_tool"] = MyCustomTool()
   ```

3. **Update task recognition in agent-planner**
   ```python
   # In microservices/agent-planner/app.py
   def create_execution_plan(task_id: str, goal: str):
       if "my custom pattern" in goal.lower():
           return {"tool": "my_custom_tool", "params": {...}}
   ```

## 🔧 Troubleshooting

### Common Issues

#### Services Not Starting
```bash
# Check Docker status
docker --version
docker-compose --version

# Check port conflicts
netstat -tulpn | grep :8300

# Rebuild containers
docker-compose build --no-cache
docker-compose up -d
```

#### Redis Connection Issues
```bash
# Test Redis connectivity
docker-compose exec agi-redis-lb redis-cli ping

# Check Redis logs
docker-compose logs agi-redis-lb

# Restart Redis
docker-compose restart agi-redis-lb
```

#### Task Processing Issues
```bash
# Check agent logs
docker-compose logs -f agent-planner
docker-compose logs -f agent-executor

# Verify EventBus communication
python scripts/debug_event_listener.py

# Test task creation
python scripts/start_multi_agent_task.py "test task"
```

#### Performance Issues
```bash
# Monitor resource usage
docker stats

# Check service health
curl http://localhost:8300/health
curl http://localhost:8400/health

# Scale services
docker-compose up -d --scale agent-executor=3
```

### Logs and Debugging

```bash
# View all logs
docker-compose logs

# Follow specific service logs
docker-compose logs -f agent-planner

# Filter logs by level
docker-compose logs | grep ERROR

# Export logs
docker-compose logs > system.log
```

## 📚 Documentation

- **[User Manual](SuperAI_User_Manual.md)**: Detailed usage instructions
- **[Production Guide](SuperAI_Production_Readiness_Report.md)**: Production deployment guide
- **[API Documentation](docs/api.md)**: Service API reference
- **[Architecture Guide](docs/architecture.md)**: System design documentation
- **[Contributing Guide](CONTRIBUTING.md)**: Development contribution guidelines

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Quick Contribution Steps

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes
4. Add tests for new functionality
5. Commit your changes: `git commit -m 'Add amazing feature'`
6. Push to the branch: `git push origin feature/amazing-feature`
7. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [Docker](https://docker.com) and [Docker Compose](https://docs.docker.com/compose/)
- Powered by [Redis](https://redis.io) for event communication
- Monitoring with [Prometheus](https://prometheus.io) and [Grafana](https://grafana.com)
- Load balancing with [NGINX](https://nginx.org)
- AI capabilities enhanced by various LLM providers

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/your-username/SuperAI/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-username/SuperAI/discussions)
- **Documentation**: [Project Wiki](https://github.com/your-username/SuperAI/wiki)

---

<div align="center">

**SuperAI - Empowering the Future of Multi-Agent AI Systems** 🚀

Made with ❤️ by the SuperAI Team

</div>

## 智能体组合模式 (Agent Composition Patterns)

我们可以将这些微服务组件按功能进行组合，构建出几种典型的、有明确目标的Agent：

### 组合 1: 基础问答型 Agent (The Core Thinker)

这是最精简的智能组合，专注于响应外部请求。

- **核心组件:** `agi-qwen-service`, `agi-synergy-api-lb`, `agi-qwen-lb`
- **形成的 Agent:** 一个具备基本对话能力的智能体，可作为智能客服、内容生成器或问答机器人。

### 组合 2: 自我学习与迭代型 Agent (The Learner)

在基础之上，增加了学习和记忆能力。

- **核心组件:** 基础问答型Agent + `agi-learning-api-lb`, `agi-redis-lb`, `agi-v4-enhanced`
- **形成的 Agent:** 一个能够通过互动和反馈不断优化的智能体，是构建个性化助手或领域专家的基础。

### 组合 3: 自主任务规划与执行型 Agent (The Autonomous Worker)

最高级的组合，模拟一个有自主目标的“数字员工”。

- **核心组件:** 自我学习型Agent + `agi-evolution-manager`
- **形成的 Agent:** 一个可以理解并执行复杂指令的自主智能体，能将复杂目标分解为子任务并自主执行。

### 组合 4: 企业级高可用 Agent 系统 (The Enterprise-Grade System)

将上述任何一种Agent进行“企业化”改造，确保其稳定、可靠、可维护。

- **核心组件:** 以上任意一种Agent + `health-check-proxy`, `agi-prometheus`, `agi-grafana`, `agi-comprehensive-monitoring-enhanced`, `agi-test-validation`
- **形成的 Agent:** 一个完整的、生产环境可用的Agent服务系统，具备自我监控、故障预警和质量保障的能力。

## 通往AGI之路：愿景与路线图 (Road to AGI: Vision & Roadmap)

本项目的长远目标是探索通往通用人工智能（AGI）的路径。以下是我们对当前系统与AGI之间差距的分析，以及为跨越这一鸿沟而制定的战略蓝图。

### 当前系统与AGI的鸿沟 (The Gap to AGI)

| 能力维度 | 当前Agent系统 (Specialized AI) | 通用人工智能 (AGI) |
| :--- | :--- | :--- |
| **推理能力** | 高级模式匹配，关联性 | 因果推理，抽象思维，常识 |
| **学习能力** | 被动，数据密集，效率低 | 主动，小样本/零样本，高效率迁移 |
| **自主性** | 执行外部任务，目标预设 | 内在动机，自主设定长期目标 |
| **适应性** | 结构化数字环境 | 开放、不确定的物理/社会环境 |

### 跨越鸿沟的战略方案 (Strategic Plan)

#### 方案一：构建“世界模型”与“符号推理”双核驱动

- **核心思想:** 为LLM引入一个负责模拟世界规律和执行严格逻辑推理的“外部大脑”。
- **实施路径:** 开发 `agi-causal-engine` (因果推理引擎) 和 `agi-knowledge-graph` (符号知识图谱)，并升级 `agi-evolution-manager` 为“认知协调器”，智能地调度不同引擎以完成复杂任务。

#### 方案二：实施“内在动机”与“自主探索”学习框架

- **核心思想:** 为Agent注入“好奇心”，让它自主地去探索未知、学习新技能。
- **实施路径:** 创建 `agi-curiosity-driver` (好奇心驱动模块)，建立“自我博弈”与“自我纠错”的训练循环，并开发可复用的“技能库”。

#### 方案三：构建“分层目标”与“价值观对齐”的自主架构

- **核心思想:** 在赋予Agent自主能力的同时，确保其最高层目标与人类的价值观和意图高度对齐。
- **实施路径:** 设计“分层目标网络”，开发 `agi-alignment-monitor` (对齐监视器)作为“道德与伦理审查”服务，并赋予Agent“自我反思”能力。

### 三阶段研究路线图 (Three-Phase Research Roadmap)

1.  **第一阶段：整合、基线建立与度量 (Integration, Baseline & Measurement)**
    - **目标:** 建立一个可一键部署、可度量的“数字培养皿”。
    - **行动:** 完善`docker-compose.yml`，建立“基线智能体”，并利用`Prometheus`和`Grafana`建立“智能度量仪表盘”。

2.  **第二阶段：实施“AGI跨越方案”的最小可行版本 (MVP Implementation)**
    - **目标:** 逐一实现三大战略方案的核心组件原型。
    - **行动:** 创建`agi-causal-engine`, `agi-curiosity-driver`, `agi-alignment-monitor`的MVP版本，并在隔离环境中进行测试。

3.  **第三阶段：迭代、涌现与观察 (Iteration, Emergence & Observation)**
    - **目标:** 加速实验循环，观察、记录并理解系统在复杂交互中可能出现的“涌现行为”。
    - **行动:** 运行多个平行实验，聚焦于提升Agent的“元能力”（如学习如何学习）。
