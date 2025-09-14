@echo off
echo ===  启动超级AI系统 ===
echo.

echo  检查Docker服务...
docker --version >nul 2>&1
if errorlevel 1 (
    echo  Docker未安装或未启动
    pause
    exit /b 1
)

echo  Docker服务正常

echo  启动超级AI微服务...
docker-compose up -d

echo  等待服务启动...
timeout /t 30 /nobreak >nul

echo  检查服务状态:
docker-compose ps

echo.
echo ===  超级AI系统启动完成 ===
echo  监控面板: http://localhost:3000 (admin/admin)
echo  指标监控: http://localhost:9090
echo  千问服务: http://localhost:8201
echo  健康检查: http://localhost:8105
echo.
pause
