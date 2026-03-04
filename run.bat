@echo off
chcp 65001 >nul
title PEP 8 Analyzer
echo ===================================================
echo        Установка и запуск PEP 8 Analyzer
echo ===================================================
echo.

REM Проверяем наличие Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python не установлен!
    echo Скачайте Python с https://www.python.org/downloads/
    pause
    exit /b 1
)

echo ✅ Python найден

REM Создаем виртуальное окружение если его нет
if not exist venv (
    echo 📦 Создание виртуального окружения...
    python -m venv venv
    if errorlevel 1 (
        echo ❌ Ошибка создания виртуального окружения
        pause
        exit /b 1
    )
)

REM Активируем виртуальное окружение
echo 🔧 Активация виртуального окружения...
call venv\Scripts\activate.bat

REM Обновляем pip
echo 📦 Обновление pip...
python -m pip install --upgrade pip >nul 2>&1

REM Устанавливаем зависимости
echo 📦 Установка зависимостей...
pip install fastapi==0.104.1 uvicorn[standard]==0.24.0 >nul 2>&1

if errorlevel 1 (
    echo ❌ Ошибка установки зависимостей
    pause
    exit /b 1
)

echo ✅ Зависимости установлены

echo.
echo ===================================================
echo 🚀 Запуск сервера...
echo ===================================================
echo.

REM Создаем необходимые папки
if not exist templates mkdir templates
if not exist static mkdir static

REM Запускаем сервер
python main.py

if errorlevel 1 (
    echo.
    echo ❌ Ошибка запуска сервера
    pause
)