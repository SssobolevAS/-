import sys
import os
from pathlib import Path
import json
import socket
import logging
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="PEP 8 Analyzer")

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Создаем необходимые директории
BASE_DIR = Path(__file__).parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

TEMPLATES_DIR.mkdir(exist_ok=True)
STATIC_DIR.mkdir(exist_ok=True)

# Подключаем шаблоны
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Словарь ошибок PEP8
ERRORS = {
    "E111": {
        "name": "Отступ не кратен 4",
        "desc": "Используйте 4 пробела для отступа",
        "severity": "high"
    },
    "E112": {
        "name": "Ожидается отступ",
        "desc": "Добавьте отступ после двоеточия",
        "severity": "high"
    },
    "E201": {
        "name": "Пробел после '('",
        "desc": "Удалите пробел после открывающей скобки",
        "severity": "medium"
    },
    "E202": {
        "name": "Пробел перед ')'",
        "desc": "Удалите пробел перед закрывающей скобкой",
        "severity": "medium"
    },
    "E211": {
        "name": "Пробел перед '('",
        "desc": "Удалите пробел перед открывающей скобкой",
        "severity": "medium"
    },
    "E225": {
        "name": "Нет пробелов вокруг оператора",
        "desc": "Добавьте пробелы вокруг оператора",
        "severity": "medium"
    },
    "E231": {
        "name": "Нет пробела после запятой",
        "desc": "Добавьте пробел после запятой",
        "severity": "medium"
    },
    "E261": {
        "name": "Мало пробелов перед комментарием",
        "desc": "Добавьте 2 пробела перед #",
        "severity": "low"
    },
    "E262": {
        "name": "Нет пробела после #",
        "desc": "Добавьте пробел после #",
        "severity": "low"
    },
    "E302": {
        "name": "Ожидается 2 пустых строки",
        "desc": "Добавьте 2 пустых строки между функциями",
        "severity": "medium"
    },
    "E401": {
        "name": "Несколько импортов на одной строке",
        "desc": "Разделите импорты на отдельные строки",
        "severity": "high"
    },
    "E501": {
        "name": "Строка слишком длинная",
        "desc": "Максимальная длина строки 79 символов",
        "severity": "medium"
    },
    "W291": {
        "name": "Пробелы в конце строки",
        "desc": "Удалите пробелы в конце строки",
        "severity": "low"
    },
    "W292": {
        "name": "Нет новой строки в конце файла",
        "desc": "Добавьте пустую строку в конце",
        "severity": "low"
    }
}

def analyze_pep8(code):
    """Анализ кода на соответствие PEP 8"""
    errors = []
    lines = code.split('\n')
    
    for i, line in enumerate(lines, 1):
        stripped = line.rstrip()
        original_line = line
        
        # 1. Пробелы в конце строки (W291)
        if line != stripped and len(stripped) > 0:
            errors.append({
                'line': i,
                'column': len(stripped),
                'code': 'W291',
                'message': 'Пробелы в конце строки',
                'name': ERRORS['W291']['name'],
                'severity': ERRORS['W291']['severity']
            })
        
        # 2. Несколько импортов (E401)
        if line.strip().startswith('import ') and ',' in line:
            errors.append({
                'line': i,
                'column': line.find('import') + 7,
                'code': 'E401',
                'message': 'Несколько импортов на одной строке',
                'name': ERRORS['E401']['name'],
                'severity': ERRORS['E401']['severity']
            })
        
        # 3. Отступ не кратен 4 (E111)
        if line.strip() and not line.strip().startswith('#'):
            indent = len(line) - len(line.lstrip())
            if indent > 0 and indent % 4 != 0:
                errors.append({
                    'line': i,
                    'column': 0,
                    'code': 'E111',
                    'message': f'Отступ {indent} пробелов (должен быть кратен 4)',
                    'name': ERRORS['E111']['name'],
                    'severity': ERRORS['E111']['severity']
                })
        
        # 4. Пробелы вокруг оператора (E225)
        if '=' in line and not '==' in line and not '!=' in line and not '<=' in line and not '>=' in line:
            pos = line.find('=')
            if pos > 0:
                if pos > 0 and line[pos-1] != ' ' and not line[:pos].rstrip().endswith(('def', 'if', 'for', 'while', 'with')):
                    errors.append({
                        'line': i,
                        'column': pos,
                        'code': 'E225',
                        'message': 'Нет пробела перед =',
                        'name': ERRORS['E225']['name'],
                        'severity': ERRORS['E225']['severity']
                    })
                if pos + 1 < len(line) and line[pos+1] != ' ':
                    errors.append({
                        'line': i,
                        'column': pos + 1,
                        'code': 'E225',
                        'message': 'Нет пробела после =',
                        'name': ERRORS['E225']['name'],
                        'severity': ERRORS['E225']['severity']
                    })
        
        # 5. Пробел после запятой (E231)
        if ',' in line:
            for j, char in enumerate(line):
                if char == ',' and j + 1 < len(line) and line[j + 1] not in [' ', ')', ']', '}', '\n']:
                    errors.append({
                        'line': i,
                        'column': j + 1,
                        'code': 'E231',
                        'message': 'Нет пробела после запятой',
                        'name': ERRORS['E231']['name'],
                        'severity': ERRORS['E231']['severity']
                    })
                    break
        
        # 6. Длина строки (E501)
        if len(line) > 79 and not line.strip().startswith('#'):
            errors.append({
                'line': i,
                'column': 79,
                'code': 'E501',
                'message': f'Строка {len(line)} > 79 символов',
                'name': ERRORS['E501']['name'],
                'severity': ERRORS['E501']['severity']
            })
    
    # 7. Пустая строка в конце (W292)
    if lines and lines[-1].strip() != '':
        errors.append({
            'line': len(lines),
            'column': len(lines[-1]),
            'code': 'W292',
            'message': 'Нет пустой строки в конце файла',
            'name': ERRORS['W292']['name'],
            'severity': ERRORS['W292']['severity']
        })
    
    # Убираем дубликаты
    unique_errors = []
    seen = set()
    for error in errors:
        key = (error['line'], error['code'])
        if key not in seen:
            seen.add(key)
            unique_errors.append(error)
    
    return unique_errors

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Главная страница"""
    try:
        return templates.TemplateResponse("index.html", {"request": request})
    except Exception as e:
        logger.error(f"Error loading template: {e}")
        return HTMLResponse(content="<h1>Error loading page</h1>", status_code=500)

@app.post("/analyze")
async def analyze(request: Request):
    """Анализ кода"""
    try:
        data = await request.json()
        code = data.get("code", "")
        
        if not code.strip():
            return JSONResponse({
                "success": False,
                "error": "Код не может быть пустым"
            })
        
        # Анализируем код
        errors = analyze_pep8(code)
        
        # Сортируем по строке
        errors.sort(key=lambda x: (x['line'], x['column']))
        
        # Считаем строки кода (не пустые)
        code_lines = len([l for l in code.split('\n') if l.strip()])
        
        # Оценка качества
        score = 100
        if errors:
            score = max(0, 100 - len(errors) * 3)
        
        return JSONResponse({
            "success": True,
            "errors": errors,
            "summary": {
                "total": len(errors),
                "lines": code_lines,
                "score": score
            }
        })
        
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        return JSONResponse({
            "success": False,
            "error": f"Ошибка анализа: {str(e)}"
        })

@app.get("/health")
async def health():
    """Проверка здоровья"""
    return {"status": "ok", "version": "1.0.0"}

def find_free_port(start_port=8000, max_attempts=10):
    """Находит свободный порт"""
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('127.0.0.1', port))
                return port
        except OSError:
            continue
    return None

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 PEP 8 Analyzer v1.0")
    print("=" * 60)
    
    # Находим свободный порт
    port = find_free_port(8000)
    
    if port is None:
        print("❌ Не удалось найти свободный порт!")
        print("💡 Закройте другие приложения и попробуйте снова.")
        input("\nНажмите Enter для выхода...")
        sys.exit(1)
    
    print(f"✅ Сервер запускается на порту {port}")
    print(f"🌐 Откройте в браузере: http://localhost:{port}")
    print("=" * 60)
    print("Нажмите Ctrl+C для остановки сервера")
    print("=" * 60)
    
    try:
        uvicorn.run(
            "main:app",
            host="127.0.0.1",
            port=port,
            reload=False,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 Сервер остановлен")
    except Exception as e:
        print(f"❌ Ошибка запуска: {e}")
        input("\nНажмите Enter для выхода...")