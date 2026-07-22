@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo 正在启动数据分析 Agent...
start /b python -m streamlit run app.py --server.port 8502 --server.headless true
timeout /t 3 /nobreak >nul
explorer "http://localhost:8502"
pause
