# SuperAI多智能体系统使用说明书

## 📋 产品概述

### 主要功能
SuperAI是一个基于微服务架构的多智能体协作系统，主要功能包括：
- **智能任务规划**：自动分析任务需求并生成执行计划
- **多智能体协作**：多个AI智能体协同完成复杂任务
- **实时事件处理**：基于Redis的异步事件总线系统
- **工具集成**：支持网络搜索、文件操作、数学计算等多种工具
- **负载均衡**：高可用性的分布式服务架构

### 主要用途
- 智能内容生产和自动化写作
- 复杂业务流程自动化
- 数据分析和处理
- 智能决策支持
- API集成和系统互联

### 技术架构
- **容器化部署**：基于Docker Compose的微服务架构
- **异步通信**：Redis EventBus事件驱动架构
- **高并发处理**：Gunicorn + Gevent协程处理
- **负载均衡**：NGINX反向代理和负载分发
- **监控体系**：Prometheus + Grafana全面监控

## ⚠️ 安全注意事项

### 系统安全
1. **网络安全**
   - 确保Redis端口(6379)仅在内网访问
   - 配置防火墙规则，限制外部访问
   - 定期更新系统和依赖包

2. **数据安全**
   - 敏感数据传输使用加密连接
   - 定期备份Redis数据
   - 避免在日志中记录敏感信息

3. **访问控制**
   - 使用强密码和访问令牌
   - 定期轮换API密钥
   - 限制管理员权限范围

### 运行环境
1. **硬件要求**
   - 最低配置：4核CPU，8GB内存，50GB存储
   - 推荐配置：8核CPU，16GB内存，100GB SSD
   - 网络带宽：100Mbps以上

2. **软件依赖**
   - Docker Engine 20.10+
   - Docker Compose 2.0+
   - Python 3.11+
   - 操作系统：Linux/Windows/macOS

## 🚀 操作步骤

### 步骤1：环境准备

#### 1.1 安装Docker
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install docker.io docker-compose

# Windows
# 下载并安装Docker Desktop
# https://www.docker.com/products/docker-desktop

# macOS
brew install docker docker-compose
```

#### 1.2 克隆项目
```bash
git clone <repository-url>
cd SuperAI
```

#### 1.3 配置环境变量
```bash
# 复制环境配置文件
cp .env.example .env

# 编辑配置文件
vim .env
```

**⚠️ 重要提示**：确保所有必要的环境变量都已正确配置

### 步骤2：系统启动

#### 2.1 构建服务镜像
```bash
# 构建所有服务镜像
docker-compose build
```

#### 2.2 启动系统服务
```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps
```

#### 2.3 验证服务健康
```bash
# 检查所有服务状态
docker-compose logs --tail=50

# 验证核心服务
curl http://localhost:8300/health  # agent-planner
curl http://localhost:8400/health  # agent-executor
```

**✅ 成功标志**：所有服务显示为"healthy"状态

### 步骤3：创建和执行任务

#### 3.1 使用脚本创建任务
```bash
# 创建简单任务
python scripts/start_multi_agent_task.py "写一首关于春天的诗"

# 创建搜索任务
python scripts/start_multi_agent_task.py "搜索：人工智能最新发展趋势"

# 创建文件操作任务
python scripts/start_multi_agent_task.py "创建文件：/tmp/test.txt，内容为当前时间"
```

#### 3.2 监控任务执行
```bash
# 查看agent-planner日志
docker-compose logs -f agent-planner

# 查看agent-executor日志
docker-compose logs -f agent-executor
```

#### 3.3 任务执行流程
1. **任务创建** → 发布`task.created`事件
2. **计划生成** → agent-planner分析任务并生成执行计划
3. **计划批准** → 发布`plan.approved`事件
4. **任务执行** → agent-executor执行具体操作
5. **任务完成** → 发布`task.completed`事件

**📊 监控面板**：访问 http://localhost:3000 查看Grafana监控面板

### 步骤4：高级配置

#### 4.1 扩展服务实例
```bash
# 扩展agent-executor服务
docker-compose up -d --scale agent-executor=3

# 扩展agent-planner服务
docker-compose up -d --scale agent-planner=2
```

#### 4.2 自定义工具集成
1. 在`core/tools.py`中添加新工具
2. 在`agent-executor/app.py`中注册工具
3. 重新构建并部署服务

#### 4.3 配置外部API
```bash
# 编辑环境配置
vim .env

# 添加API密钥
TAVILY_API_KEY=your_api_key
OPENAI_API_KEY=your_openai_key
```

### 步骤5：系统维护

#### 5.1 日常检查
```bash
# 检查服务状态
docker-compose ps

# 检查资源使用
docker stats

# 检查日志
docker-compose logs --tail=100
```

#### 5.2 数据备份
```bash
# 备份Redis数据
docker-compose exec agi-redis-lb redis-cli BGSAVE

# 导出配置
cp docker-compose.yml docker-compose.backup.yml
```

#### 5.3 系统更新
```bash
# 拉取最新代码
git pull origin main

# 重新构建服务
docker-compose build

# 滚动更新
docker-compose up -d
```

## ❓ 常见问题解答

### Q1: 服务启动失败怎么办？
**A1**: 
1. 检查Docker是否正常运行：`docker --version`
2. 查看具体错误日志：`docker-compose logs [service-name]`
3. 确认端口未被占用：`netstat -tulpn | grep :8300`
4. 重新构建镜像：`docker-compose build --no-cache`

### Q2: 任务执行没有响应？
**A2**:
1. 检查Redis连接：`docker-compose logs agi-redis-lb`
2. 验证EventBus状态：`docker-compose logs agent-planner | grep EventBus`
3. 确认服务健康：`curl http://localhost:8300/health`
4. 重启相关服务：`docker-compose restart agent-planner agent-executor`

### Q3: 出现greenlet错误？
**A3**:
1. 这通常是gevent兼容性问题
2. 检查event_bus.py中是否包含`gevent.monkey.patch_socket()`
3. 重启agent-planner服务：`docker-compose restart agent-planner`

### Q4: 内存使用过高？
**A4**:
1. 监控资源使用：`docker stats`
2. 调整worker数量：编辑`gunicorn.conf.py`中的workers参数
3. 增加系统内存或优化任务复杂度

### Q5: 网络搜索功能不可用？
**A5**:
1. 检查TAVILY_API_KEY是否配置：`echo $TAVILY_API_KEY`
2. 验证网络连接：`curl https://api.tavily.com`
3. 查看agent-executor日志中的SSL错误

### Q6: 如何添加新的工具？
**A6**:
1. 在`core/tools.py`中定义新工具类
2. 在`agent-executor/app.py`中注册工具
3. 在`agent-planner/app.py`中添加任务识别逻辑
4. 重新构建并部署服务

## 🔧 维护保养

### 日常维护

#### 每日检查
- [ ] 检查所有服务运行状态
- [ ] 监控系统资源使用情况
- [ ] 查看错误日志并及时处理
- [ ] 验证关键功能正常运行

#### 每周维护
- [ ] 清理Docker无用镜像和容器
- [ ] 备份重要配置和数据
- [ ] 检查系统安全更新
- [ ] 性能监控和优化

#### 每月维护
- [ ] 更新系统依赖包
- [ ] 检查和轮换API密钥
- [ ] 系统性能评估和调优
- [ ] 灾难恢复测试

### 性能优化

#### 1. 资源配置优化
```yaml
# docker-compose.yml中调整资源限制
services:
  agent-executor:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
```

#### 2. 并发处理优化
```python
# gunicorn.conf.py中调整worker配置
workers = 4  # 根据CPU核心数调整
worker_class = "gevent"
worker_connections = 1000
```

#### 3. Redis性能优化
```bash
# 调整Redis配置
docker-compose exec agi-redis-lb redis-cli CONFIG SET maxmemory 2gb
docker-compose exec agi-redis-lb redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

### 故障排除

#### 系统诊断命令
```bash
# 系统健康检查脚本
#!/bin/bash
echo "=== SuperAI系统健康检查 ==="
echo "1. Docker服务状态:"
docker-compose ps

echo "\n2. 服务健康检查:"
curl -s http://localhost:8300/health | jq .
curl -s http://localhost:8400/health | jq .

echo "\n3. Redis连接测试:"
docker-compose exec agi-redis-lb redis-cli ping

echo "\n4. 资源使用情况:"
docker stats --no-stream

echo "\n5. 最近错误日志:"
docker-compose logs --tail=10 | grep -i error
```

#### 常用维护命令
```bash
# 清理系统
docker system prune -f
docker volume prune -f

# 重启所有服务
docker-compose restart

# 查看详细日志
docker-compose logs -f --tail=100

# 进入容器调试
docker-compose exec agent-planner /bin/bash
```

### 备份和恢复

#### 数据备份
```bash
# 创建备份脚本
#!/bin/bash
BACKUP_DIR="/backup/superai/$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR

# 备份Redis数据
docker-compose exec agi-redis-lb redis-cli BGSAVE
docker cp $(docker-compose ps -q agi-redis-lb):/data/dump.rdb $BACKUP_DIR/

# 备份配置文件
cp docker-compose.yml $BACKUP_DIR/
cp .env $BACKUP_DIR/

echo "备份完成: $BACKUP_DIR"
```

#### 系统恢复
```bash
# 恢复Redis数据
docker-compose stop agi-redis-lb
docker cp backup/dump.rdb $(docker-compose ps -q agi-redis-lb):/data/
docker-compose start agi-redis-lb

# 恢复配置
cp backup/docker-compose.yml .
cp backup/.env .
docker-compose up -d
```

## 📞 技术支持

### 联系方式
- **技术文档**: 查看项目README.md
- **问题反馈**: 提交GitHub Issue
- **社区支持**: 加入技术交流群

### 版本信息
- **当前版本**: v1.0.0
- **更新日期**: 2025年9月14日
- **兼容性**: Docker 20.10+, Python 3.11+

---

**⚠️ 重要提醒**: 在生产环境中使用前，请务必进行充分的测试和性能评估。建议先在测试环境中熟悉系统操作，确保理解所有功能和限制后再部署到生产环境。