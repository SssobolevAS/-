import sys
import os
from pathlib import Path
import json
import socket
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Создаем директории
Path("static").mkdir(exist_ok=True)
Path("templates").mkdir(exist_ok=True)

# Подключаем статические файлы и шаблоны
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Словарь ошибок
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
        
        # 1. Пробелы в конце строки (W291)
        if line != stripped:
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
        if '=' in line and not '==' in line and not '!=' in line:
            pos = line.find('=')
            if pos > 0:
                if pos > 0 and line[pos-1] != ' ' and not line[:pos].rstrip().endswith(('def', 'if', 'for', 'while')):
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
                if char == ',' and j + 1 < len(line) and line[j + 1] not in [' ', ')', ']', '}']:
                    errors.append({
                        'line': i,
                        'column': j + 1,
                        'code': 'E231',
                        'message': 'Нет пробела после запятой',
                        'name': ERRORS['E231']['name'],
                        'severity': ERRORS['E231']['severity']
                    })
                    break
        
        # 6. Пробел перед '(' (E211)
        if '(' in line:
            pos = line.find('(')
            if pos > 0 and line[pos - 1] == ' ':
                if not line[:pos].strip().endswith(('def', 'if', 'for', 'while')):
                    errors.append({
                        'line': i,
                        'column': pos,
                        'code': 'E211',
                        'message': 'Пробел перед (',
                        'name': ERRORS['E211']['name'],
                        'severity': ERRORS['E211']['severity']
                    })
        
        # 7. Пробел после '(' (E201)
        if '(' in line:
            pos = line.find('(')
            if pos + 1 < len(line) and line[pos + 1] == ' ':
                errors.append({
                    'line': i,
                    'column': pos + 1,
                    'code': 'E201',
                    'message': 'Пробел после (',
                    'name': ERRORS['E201']['name'],
                    'severity': ERRORS['E201']['severity']
                })
        
        # 8. Пробел перед ')' (E202)
        if ')' in line:
            pos = line.rfind(')')
            if pos > 0 and line[pos - 1] == ' ':
                errors.append({
                    'line': i,
                    'column': pos,
                    'code': 'E202',
                    'message': 'Пробел перед )',
                    'name': ERRORS['E202']['name'],
                    'severity': ERRORS['E202']['severity']
                })
        
        # 9. Длина строки (E501)
        if len(line) > 79 and not line.strip().startswith('#'):
            errors.append({
                'line': i,
                'column': 79,
                'code': 'E501',
                'message': f'Строка {len(line)} > 79 символов',
                'name': ERRORS['E501']['name'],
                'severity': ERRORS['E501']['severity']
            })
        
        # 10. Пробелы перед комментарием (E261)
        if '#' in line and not line.strip().startswith('#'):
            pos = line.find('#')
            if pos > 0:
                if line[pos - 1] != ' ':
                    errors.append({
                        'line': i,
                        'column': pos,
                        'code': 'E261',
                        'message': 'Нужно 2 пробела перед #',
                        'name': ERRORS['E261']['name'],
                        'severity': ERRORS['E261']['severity']
                    })
                elif pos > 1 and line[pos - 2] != ' ':
                    errors.append({
                        'line': i,
                        'column': pos,
                        'code': 'E261',
                        'message': 'Нужно 2 пробела перед #',
                        'name': ERRORS['E261']['name'],
                        'severity': ERRORS['E261']['severity']
                    })
        
        # 11. Пробел после # (E262)
        if '#' in line:
            pos = line.find('#')
            if pos + 1 < len(line) and line[pos + 1] not in [' ', '\n']:
                errors.append({
                    'line': i,
                    'column': pos + 1,
                    'code': 'E262',
                    'message': 'Нет пробела после #',
                    'name': ERRORS['E262']['name'],
                    'severity': ERRORS['E262']['severity']
                })
    
    # 12. Пустая строка в конце (W292)
    if lines and lines[-1].strip() != '':
        errors.append({
            'line': len(lines),
            'column': len(lines[-1]),
            'code': 'W292',
            'message': 'Нет пустой строки в конце файла',
            'name': ERRORS['W292']['name'],
            'severity': ERRORS['W292']['severity']
        })
    
    # 13. Две пустые строки между функциями (E302)
    for i in range(1, len(lines)):
        if lines[i].strip().startswith('def ') and i > 0:
            empty_count = 0
            j = i - 1
            while j >= 0 and not lines[j].strip():
                empty_count += 1
                j -= 1
            if empty_count < 2:
                errors.append({
                    'line': i + 1,
                    'column': 0,
                    'code': 'E302',
                    'message': 'Нужно 2 пустых строки перед функцией',
                    'name': ERRORS['E302']['name'],
                    'severity': ERRORS['E302']['severity']
                })
                break
    
    return errors

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Главная страница"""
    return templates.TemplateResponse("index.html", {"request": request})

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
        
        # Убираем дубликаты
        unique = []
        seen = set()
        for e in errors:
            key = (e['line'], e['code'])
            if key not in seen:
                seen.add(key)
                unique.append(e)
        
        # Сортируем по строке
        unique.sort(key=lambda x: x['line'])
        
        # Считаем строки кода
        code_lines = len([l for l in code.split('\n') if l.strip()])
        
        # Оценка качества
        score = 100
        if unique:
            score = max(0, 100 - len(unique) * 3)
        
        return JSONResponse({
            "success": True,
            "errors": unique,
            "summary": {
                "total": len(unique),
                "lines": code_lines,
                "score": score
            }
        })
        
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        })

@app.get("/health")
async def health():
    """Проверка здоровья"""
    return {"status": "ok", "version": "1.0.0"}

def find_free_port():
    """Находит свободный порт"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port

if __name__ == "__main__":
    import uvicorn
    
    # Пробуем разные порты
    ports = [8000, 8001, 8002, 8003, 8004, 8005]
    
    for port in ports:
        try:
            print(f"🔍 Пробуем порт {port}...")
            
            # Проверяем, свободен ли порт
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('0.0.0.0', port))
                s.close()
            
            # Если дошли сюда - порт свободен
            print("=" * 50)
            print("🚀 PEP 8 Analyzer v1.0")
            print("=" * 50)
            print(f"✅ Сервер запущен!")
            print(f"🌐 Откройте в браузере: http://localhost:{port}")
            print("=" * 50)
            
            uvicorn.run(app, host="0.0.0.0", port=port)
            break
            
        except OSError:
            print(f"❌ Порт {port} занят, пробуем следующий...")
            continue
    else:
        print("❌ Все порты заняты! Закройте другие приложения и попробуйте снова.")
        input("Нажмите Enter для выхода...")