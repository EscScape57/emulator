import tkinter as tk
import os
import socket
import shlex
import sys
import argparse
import time
from vfs import VFS # Импортируем наш класс VFS

# Глобальная переменная для VFS
vfs = None

# --- Функции-обработчики для наших команд ---

def command_ls(args):
    """Реализация команды ls для VFS."""
    global vfs
    if vfs is None:
        return "Ошибка: VFS не инициализирована."

    path = args[0] if args else None
    entries, error = vfs.list_directory(path)
    if error:
        return f"Ошибка ls: {error}"
    
    if not entries:
        return ""
    return "  ".join(entries)

def command_cd(args):
    """Реализация команды cd для VFS."""
    global vfs
    if vfs is None:
        return "Ошибка: VFS не инициализирована."

    if not args:
        return "Ошибка cd: требуется аргумент (путь)."
    
    path = args[0]
    success, error = vfs.change_directory(path)
    if not success:
        return f"Ошибка cd: {error}"
    return ""

def command_exit(args):
    """Команда для выхода из приложения."""
    window.quit()
    return "Завершение работы..."

def command_echo(args):
    """Реализация команды echo."""
    return " ".join(args)

# --- Словарь для связи имени команды с функцией ---
COMMANDS = {
    'ls': command_ls,
    'cd': command_cd,
    'exit': command_exit,
    'echo': command_echo,
}

def parse_command(command_string):
    parts = shlex.split(command_string)
    expanded_parts = []
    for part in parts:
        if part.startswith('$') and len(part) > 1:
            var_name = part[1:]
            expanded_value = os.environ.get(var_name, '')
            expanded_parts.append(expanded_value)
        else:
            expanded_parts.append(part)
    return expanded_parts

def execute_command(command_string):
    command_parts = parse_command(command_string)
    
    if not command_parts:
        return "", False # Пустая команда, не ошибка

    command_name = command_parts[0]
    command_args = command_parts[1:]

    if command_name in COMMANDS:
        function_to_call = COMMANDS[command_name]
        result = function_to_call(command_args)
        return result, False
    else:
        result = f"Ошибка: неизвестная команда '{command_name}'"
        return result, True # Возвращаем True, если это ошибка

def process_command(event=None, command_string=None):
    if command_string is None:
        command_string = input_field.get()
    
    if not command_string:
        return

    output_area.config(state='normal')
    output_area.insert(tk.END, f"[{username}@{hostname}]$ {command_string}\n")

    result, is_error = execute_command(command_string)
    output_area.insert(tk.END, f"{result}\n")
    output_area.insert(tk.END, "\n")
    
    output_area.config(state='disabled')
    output_area.see(tk.END)
    input_field.delete(0, tk.END)
    return is_error # Возвращаем статус ошибки

def run_startup_script(script_path):
    output_area.config(state='normal')
    output_area.insert(tk.END, f"Запуск стартового скрипта: {script_path}\n\n")
    output_area.config(state='disabled')
    output_area.see(tk.END)

    try:
        with open(script_path, 'r') as f:
            commands = f.readlines()
        
        for cmd_line in commands:
            cmd_line = cmd_line.strip()
            if not cmd_line or cmd_line.startswith('#'): # Пропускаем пустые строки и комментарии
                continue
            
            output_area.config(state='normal')
            output_area.insert(tk.END, f"Выполнение скрипта: {cmd_line}\n")
            output_area.config(state='disabled')
            output_area.see(tk.END)
            window.update_idletasks() # Обновляем GUI, чтобы пользователь видел вывод
            time.sleep(0.1) # Небольшая задержка для имитации работы

            is_error = process_command(command_string=cmd_line)
            if is_error:
                output_area.config(state='normal')
                output_area.insert(tk.END, f"\nОшибка выполнения скрипта. Остановка.\n")
                output_area.config(state='disabled')
                output_area.see(tk.END)
                return False # Ошибка, скрипт остановлен
            window.update_idletasks()
            time.sleep(0.1)

    except FileNotFoundError:
        output_area.config(state='normal')
        output_area.insert(tk.END, f"Ошибка: стартовый скрипт '{script_path}' не найден.\n")
        output_area.config(state='disabled')
        output_area.see(tk.END)
        return False
    except Exception as e:
        output_area.config(state='normal')
        output_area.insert(tk.END, f"Ошибка при чтении или выполнении скрипта: {e}\n")
        output_area.config(state='disabled')
        output_area.see(tk.END)
        return False
    
    output_area.config(state='normal')
    output_area.insert(tk.END, f"\nСтартовый скрипт '{script_path}' выполнен успешно.\n")
    output_area.config(state='disabled')
    output_area.see(tk.END)
    return True

# --- Парсинг аргументов командной строки ---
parser = argparse.ArgumentParser(description="Эмулятор командной оболочки ОС.")
parser.add_argument('--vfs_path', type=str, help="Путь к физическому расположению VFS.")
parser.add_argument('--startup_script', type=str, help="Путь к стартовому скрипту.")
args = parser.parse_args()

# --- Отладочный вывод параметров ---
print("--- Отладочный вывод параметров ---")
print(f"VFS Path: {args.vfs_path if args.vfs_path else 'Не указан'}")
print(f"Startup Script: {args.startup_script if args.startup_script else 'Не указан'}")
print("----------------------------------")

# --- Инициализация VFS ---
vfs = VFS()
vfs_name = "Default VFS"
if args.vfs_path:
    try:
        vfs.load_from_json(args.vfs_path)
        vfs_name = os.path.basename(args.vfs_path) # Имя VFS из имени файла
    except FileNotFoundError as e:
        print(f"Ошибка загрузки VFS: {e}")
        # Создаем VFS по умолчанию, если файл не найден
        vfs.create_default_vfs()
        vfs_name = "Default VFS (file not found)"
    except ValueError as e:
        print(f"Ошибка загрузки VFS: {e}")
        # Создаем VFS по умолчанию, если формат неверный
        vfs.create_default_vfs()
        vfs_name = "Default VFS (invalid format)"
    except Exception as e:
        print(f"Неизвестная ошибка при загрузке VFS: {e}")
        vfs.create_default_vfs()
        vfs_name = "Default VFS (unknown error)"
else:
    vfs.create_default_vfs()

username = os.getenv('USER', 'user') # Используем переменную окружения USER, или 'user' по умолчанию
hostname = socket.gethostname()

window = tk.Tk()
# Обновляем заголовок окна, чтобы он содержал имя VFS
window.title(f"Эмулятор - [{username}@{hostname}] - VFS: {vfs_name}")
window.geometry("600x400")

output_area = tk.Text(window, state='disabled', bg='black', fg='white', font=("Courier New", 10))
output_area.pack(fill=tk.BOTH, expand=True)

input_field = tk.Entry(window, bg='black', fg='white', insertbackground='white', font=("Courier New", 10))
input_field.pack(fill=tk.X, side=tk.BOTTOM)

input_field.bind("<Return>", process_command)
input_field.focus_set()

# --- Запуск стартового скрипта, если указан (отложенный) ---
def start_script_after_gui_init():
    if args.startup_script:
        run_startup_script(args.startup_script)

window.protocol("WM_DELETE_WINDOW", window.quit)

# Вызываем функцию запуска скрипта через некоторое время после старта mainloop
window.after(100, start_script_after_gui_init) # 100 мс задержка

window.mainloop()