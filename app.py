from flask import Flask, render_template, request, jsonify
import subprocess
import tempfile
import os
import json

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    code = request.json.get("code", "")

    if not code:
        return jsonify({"error": "Пожалуйста, вставьте код для анализа."}), 400

    # Создаем временный файл
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
        f.write(code)
        temp_file_path = f.name

    try:
        # Запускаем flake8 через subprocess
        result = subprocess.run(
            ['flake8', '--format=json', temp_file_path],
            capture_output=True,
            text=True,
            encoding='utf-8'
        )

        errors = []

        # Если есть вывод, парсим JSON
        if result.stdout and result.stdout.strip():
            try:
                flake8_output = json.loads(result.stdout)

                # Обрабатываем структуру JSON от flake8
                for file_errors in flake8_output:
                    for error in file_errors:
                        errors.append({
                            'line': error['line_number'],
                            'column': error['column_number'],
                            'message': error['text'],
                            'type': error['code']
                        })

            except json.JSONDecodeError as e:
                print(f"Ошибка парсинга JSON: {e}")
                print(f"Вывод flake8: {result.stdout}")
                print(f"Ошибки flake8: {result.stderr}")

                # Попробуем текстовый формат
                for line in result.stdout.split('\n'):
                    if line and ':' in line:
                        parts = line.split(':', 3)
                        if len(parts) >= 4:
                            try:
                                errors.append({
                                    'line': int(parts[1]),
                                    'column': int(parts[2]),
                                    'type': parts[0].strip(),
                                    'message': parts[3].strip()
                                })
                            except (ValueError, IndexError):
                                continue

        return jsonify({"errors": errors})

    except Exception as e:
        print(f"Исключение при анализе: {str(e)}")
        return jsonify({"error": f"Ошибка при анализе: {str(e)}"}), 500

    finally:
        # Удаляем временный файл
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)

if __name__ == "__main__":
    app.run(debug=True, port=5000)