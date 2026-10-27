@echo off
title Campus Placement Portal - AI Resume Matcher
color 0A

echo =======================================================
echo   🚀 STARTING CAMPUS PLACEMENT PORTAL ENVIRONMENT
echo =======================================================
echo.

:: === STEP 1: Start Redis Server ===
echo [1/3] Starting Redis Server...
start cmd /k "cd C:\Program Files\Redis && redis-server.exe"

timeout /t 5 >nul

:: === STEP 2: Start Celery Worker ===
echo [2/3] Starting Celery Worker...
start cmd /k "cd /d E:\SEM 7\placement_project = 2\placement_project\placement_project && celery -A placement_project worker -l info --pool=solo"

timeout /t 5 >nul

:: === STEP 3: Start Django Server ===
echo [3/3] Starting Django Development Server...
cd /d E:\SEM 7\placement_project = 2\placement_project\placement_project
start cmd /k "python manage.py runserver"

echo.
echo =======================================================
echo ✅ All services started successfully!
echo    - Redis Server
echo    - Celery Worker
echo    - Django Web App
echo -------------------------------------------------------
echo  Open your browser and visit: http://127.0.0.1:8000/
echo =======================================================
pause
