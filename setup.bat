@echo off
echo Установка PEP 8 Analyzer...
echo.

REM Создаем виртуальное окружение если его нет
if not exist venv (
    echo Создание виртуального окружения...
    python -m venv venv
)

REM Активируем виртуальное окружение
echo Активация виртуального окружения...
call venv\Scripts\activate.bat

REM Обновляем pip
echo Обновление pip...
python -m pip install --upgrade pip

REM Удаляем конфликтующие пакеты
echo Удаление конфликтующих пакетов...
pip uninstall autopep8 -y

REM Устанавливаем зависимости
echo Установка зависимостей...
pip install fastapi==0.104.1
pip install uvicorn[standard]==0.24.0
pip install flake8==6.1.0
pip install pycodestyle==2.11.1
pip install pyflakes==3.1.0
pip install python-multipart==0.0.6

REM Проверяем установку
echo.
echo Проверка установки...
python -c "import flake8, pycodestyle; print('flake8:', flake8.__version__); print('pycodestyle:', pycodestyle.__version__); print('✅ Все пакеты установлены!')"

echo.
echo Запуск приложения...
echo python main.py
pause