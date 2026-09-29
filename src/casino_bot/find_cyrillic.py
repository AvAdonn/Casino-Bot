import pathlib
import re


def scan_project_for_cyrillic(root_dir: str):
    # Патерн, який шукає хоча б одну кириличну літеру (включно з українськими)
    cyrillic_pattern = re.compile(r'[а-яА-ЯіІїЇєЄґҐ]')
    
    # Визначаємо стартову директорію
    base_path = pathlib.Path(root_dir)
    
    # Директорії, які ми категорично ігноруємо (щоб не сканувати бібліотеки та git)
    ignore_dirs = {'.venv', 'venv', '.git', '__pycache__', '.idea'}
    
    total_found = 0

    # rglob('*.py') рекурсивно пройдеться по всіх папках і знайде всі Python-файли
    for file_path in base_path.rglob('*.py'):
        
        # Перевіряємо, чи не лежить файл у папці, яку треба ігнорувати
        if any(ignored in file_path.parts for ignored in ignore_dirs):
            continue
            
        try:
            # Обов'язково вказуємо utf-8, інакше на Windows можуть бути проблеми з кодуванням
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            file_has_cyrillic = False
            for line_num, line in enumerate(lines, 1):
                # Якщо в рядку є збіг з нашим патерном
                if cyrillic_pattern.search(line):
                    if not file_has_cyrillic:
                        print(f"\n📄 Файл: {file_path}")
                        file_has_cyrillic = True
                    
                    # Виводимо номер рядка і сам текст (очищений від зайвих пробілів по краях)
                    print(f"  Рядок {line_num}: {line.strip()}")
                    total_found += 1
                    
        except UnicodeDecodeError:
            # Якщо випадково натрапили на бінарний файл, просто пропускаємо
            pass

    print(f"\n🔍 Сканування завершено. Знайдено рядків із кирилицею: {total_found}")

if __name__ == '__main__':
    # Запускаємо сканування поточної директорії (там, де лежить скрипт)
    scan_project_for_cyrillic('.')