import webbrowser
import os
import shutil
import time
import zipfile
import io
import platform  # ДОБАВИЛИ ДЛЯ СБОРА ИНФО ОБ УСТРОЙСТВЕ
import sys       # ДОБАВИЛИ ДЛЯ ОПРЕДЕЛЕНИЯ ВЕРСИИ PYTHON
from contextlib import redirect_stdout
from kivy.app import App
from kivy.uix.textinput import TextInput
from kivy.core.window import Window
from kivy.cache import Cache
from kivy.animation import Animation 

class RainyConsole(TextInput):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.start_time = time.time()
        self.history = []
        self.editing = False
        self.current_edit_file = ""
        self.terminal_buffer = ""
        
        # Переменная буфера обмена для путей картинок
        self.copied_visual_file = ""
        
        # Переменная буфера обмена для путей шрифтов
        self.copied_font_file = ""
        
        # --- УМНОЕ ОПРЕДЕЛЕНИЕ ПУТЕЙ (ДЛЯ НОУТА И АНДРОИДА) ---
        if os.path.exists("/storage/emulated/0"):
            # Если мы на Android, работаем в стандартной папке
            self.base_patcher_dir = "/storage/emulated/0/patcher/visual"
        else:
            # Если мы на ноуте (Windows/Linux), берем папку visual прямо рядом с main.py
            self.base_patcher_dir = os.path.join(os.getcwd(), "visual")
        
        if not os.path.exists(self.base_patcher_dir):
            os.makedirs(self.base_patcher_dir, exist_ok=True)
        
        # Динамические пути к конфигам
        self.config_path = os.path.join(self.base_patcher_dir, "active_bg.txt")
        self.font_config_path = os.path.join(self.base_patcher_dir, "active_font.txt")
        self.color_config_path = os.path.join(self.base_patcher_dir, "active_color.txt")
        
        # Переменная для отслеживания состояния Glow-эффекта
        self.glow_active = False
        self.glow_anim = None
        
        # --- ЗАТЕМНЕНИЕ НА 50% ---
        self.background_color = (0.5, 0.5, 0.5, 1) 
        self.foreground_color = (0.8, 0.8, 0.8, 1) # Дефолтный цвет (серый)
        self.cursor_color = (1, 1, 1, 1)
        self.font_name = 'Roboto'
        self.font_size = '14sp'
        
        # --- ФИКС СКРОЛЛА ---
        self.multiline = True
        self.readonly = False
        self.padding = [20, 20] 
        
        # ПРИНУДИТЕЛЬНАЯ УСТАНОВКА ФОНА ДЛЯ ВСЕХ СОСТОЯНИЙ
        default_bg = os.path.join(self.base_patcher_dir, "black.png")
        self.background_normal = default_bg
        self.background_active = default_bg
        self.background_disabled_normal = default_bg
        self.background_disabled_active = default_bg
        
        self.load_saved_wallpaper()
        self.load_saved_font()
        # Загрузка сохранённого цвета при старте
        self.load_saved_color()
        
        # Стартуем сразу с красивым динамическим путем
        self.text = "[ Rainy OS v0.7 Initialized ]\n[ Python Engine: Active ]\n\n" + self.get_prompt()

    def load_saved_wallpaper(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    bg_name = f.read().strip()
                full_path = os.path.join(self.base_patcher_dir, bg_name)
                if os.path.exists(full_path):
                    self.background_normal = full_path
                    self.background_active = full_path
                    self.background_disabled_normal = full_path
                    self.background_disabled_active = full_path
            except:
                pass

    def load_saved_font(self):
        if os.path.exists(self.font_config_path):
            try:
                with open(self.font_config_path, 'r') as f:
                    font_name = f.read().strip()
                full_path = os.path.join(self.base_patcher_dir, font_name)
                if os.path.exists(full_path):
                    self.font_name = full_path
            except:
                pass

    # Метод восстановления цвета при перезапуске
    def load_saved_color(self):
        if os.path.exists(self.color_config_path):
            try:
                with open(self.color_config_path, 'r') as f:
                    color_name = f.read().strip().lower()
                
                color_map = {
                    "green": (0.0, 1.0, 0.0, 1),
                    "amber": (1.0, 0.75, 0.0, 1),
                    "cyan": (0.0, 1.0, 1.0, 1),
                    "white": (1.0, 1.0, 1.0, 1),
                    "reset": (0.8, 0.8, 0.8, 1),
                    "red": (1.0, 0.2, 0.2, 1),
                    "pink": (1.0, 0.0, 1.0, 1),
                    "purple": (0.6, 0.2, 1.0, 1),
                    "yellow": (1.0, 1.0, 0.0, 1),
                    "blue": (0.2, 0.4, 1.0, 1),
                    "mint": (0.4, 1.0, 0.7, 1),
                    "lava": (1.0, 0.3, 0.0, 1)
                }
                if color_name in color_map:
                    self.foreground_color = color_map[color_name]
                    self.cursor_color = color_map[color_name]
            except:
                pass

    def get_prompt(self):
        current_dir = os.getcwd()
        if current_dir == "/storage/emulated/0":
            display_dir = "~"
        elif current_dir.startswith("/storage/emulated/0/"):
            display_dir = current_dir.replace("/storage/emulated/0", "~")
        else:
            display_dir = current_dir
        return f"rainy@mikha:{display_dir}$ "

    def on_text(self, instance, value):
        if not self.editing:
            lines = self.text.split('\n')
            if len(lines) > 30:
                self.text = '\n'.join(lines[-30:])
        
        # Сбрасываем скролл в самый низ
        self.scroll_y = 0

    def keyboard_on_key_down(self, window, keycode, text, modifiers):
        current_prompt = self.get_prompt()

        if self.editing:
            if keycode[1] == 'enter':
                lines = self.text.split('\n')
                if lines[-1].strip() == ":q":
                    self.save_and_exit()
                    return True
            return super().keyboard_on_key_down(window, keycode, text, modifiers)

        if keycode[1] == 'backspace':
            if self.text.endswith(current_prompt):
                return True
        
        if keycode[1] == 'enter':
            lines = self.text.split('\n')
            current_line = lines[-1] if lines else ""
            
            command = current_line.replace(current_prompt, "").strip()
            self.text += "\n"
            self.process_command(command)
            
            if not self.editing:
                self.text += "\n" + self.get_prompt()
            return True
        
        return super().keyboard_on_key_down(window, keycode, text, modifiers)

    def insert_text(self, substring, from_undo=False):
        if not self.editing and self.cursor_index() < len(self.text):
            self.cursor = self.get_cursor_from_index(len(self.text))
        return super().insert_text(substring, from_undo=from_undo)

    def process_command(self, cmd_input):
        self.history.append(cmd_input)
        parts = cmd_input.split()
        if not parts: return
        
        main_cmd = parts[0]
        args = parts[1:] if len(parts) > 1 else []
        res = ""

        try:
            # --- ИСПОЛНЕНИЕ (PYTHON ENGINE) ---
            if main_cmd == "+s" and args:
                filename = args[0]
                if os.path.exists(filename):
                    res = f"--- Executing {filename} ---\n"
                    try:
                        with open(filename, 'r') as f:
                            code = f.read()
                        
                        output = io.StringIO()
                        with redirect_stdout(output):
                            exec(code, {"__name__": "__main__"}) 
                        res += output.getvalue()
                        res += "--- Finished ---"
                    except Exception as script_e:
                        res += f"Python Error: {str(script_e)}"
                else:
                    res = f"Error: File '{filename}' not found."
            
            elif main_cmd == "+py" and args:
                code_to_eval = " ".join(args)
                try:
                    output = io.StringIO()
                    with redirect_stdout(output):
                        try:
                            result = eval(code_to_eval, {"__name__": "__main__"})
                            if result is not None:
                                print(result)
                        except SyntaxError:
                            exec(code_to_eval, {"__name__": "__main__"})
                    res = output.getvalue().strip()
                    if not res:
                        res = "Success (No output)"
                except Exception as py_e:
                    res = f"Eval Error: {str(py_e)}"

            elif main_cmd == "+ff" and args:
                if args[0] == "browser":
                    try:
                        webbrowser.open("https://www.google.com")
                        res = "Opening browser..."
                    except Exception as e:
                        res = f"Browser error: {str(e)}"
                else:
                    res = "Usage: +ff browser"

            # --- ВИЗУАЛЬНЫЙ КОНФИГУРАТОР ---
            elif main_cmd == "+vc" and args:
                filename = args[0]
                if filename.lower().endswith('.png'):
                    if os.path.exists(filename):
                        self.copied_visual_file = os.path.abspath(filename)
                        res = f"Visual buffer: '{filename}' loaded."
                    else:
                        res = f"Error: File '{filename}' not found."
                elif filename.lower().endswith('.ttf'):
                    if os.path.exists(filename):
                        self.copied_font_file = os.path.abspath(filename)
                        res = f"Font buffer: '{filename}' loaded."
                    else:
                        res = f"Error: File '{filename}' not found."
                else:
                    res = "Error: Only PNG and TTF files are supported."
            
            elif main_cmd == "+vp":
                if not self.copied_visual_file and not self.copied_font_file:
                    res = "Error: Buffers are empty. Use '+vc [file]' first."
                else:
                    res = ""
                    if self.copied_visual_file:
                        original_name = os.path.basename(self.copied_visual_file)
                        dest_path = os.path.join(self.base_patcher_dir, original_name)
                        shutil.copy(self.copied_visual_file, dest_path)
                        res += f"File '{original_name}' pasted into visual directory.\n"
                    if self.copied_font_file:
                        original_name = os.path.basename(self.copied_font_file)
                        dest_path = os.path.join(self.base_patcher_dir, original_name)
                        shutil.copy(self.copied_font_file, dest_path)
                        res += f"Font '{original_name}' pasted into visual directory."
                    res = res.strip()
            
            elif main_cmd == "+bg" and args:
                filename = args[0]
                target_image = os.path.join(self.base_patcher_dir, filename)
                if os.path.exists(target_image):
                    Cache.remove('kv.image')
                    Cache.remove('kv.texture')
                    self.background_normal = target_image
                    self.background_active = target_image
                    self.background_disabled_normal = target_image
                    self.background_disabled_active = target_image
                    self.canvas.ask_update()
                    with open(self.config_path, 'w') as f:
                        f.write(filename)
                    res = f"Background changed to '{filename}'!"
                else:
                    res = f"Error: File '{filename}' not found in visual directory."

            elif main_cmd == "+tf" and args:
                filename = args[0]
                if not filename.lower().endswith('.ttf'):
                    res = "Error: Only TTF fonts are supported."
                else:
                    target_font = os.path.join(self.base_patcher_dir, filename)
                    if os.path.exists(target_font):
                        self.font_name = target_font
                        self.canvas.ask_update()
                        with open(self.font_config_path, 'w') as f:
                            f.write(filename)
                        res = f"Font changed to '{filename}'!"
                    else:
                        res = f"Error: Font '{filename}' not found in visual directory."

            elif main_cmd == "+cc" and args:
                color_name = args[0].lower()
                color_map = {
                    "green": (0.0, 1.0, 0.0, 1),
                    "amber": (1.0, 0.75, 0.0, 1),
                    "cyan": (0.0, 1.0, 1.0, 1),
                    "white": (1.0, 1.0, 1.0, 1),
                    "reset": (0.8, 0.8, 0.8, 1),
                    "red": (1.0, 0.2, 0.2, 1),
                    "pink": (1.0, 0.0, 1.0, 1),
                    "purple": (0.6, 0.2, 1.0, 1),
                    "yellow": (1.0, 1.0, 0.0, 1),
                    "blue": (0.2, 0.4, 1.0, 1),
                    "mint": (0.4, 1.0, 0.7, 1),
                    "lava": (1.0, 0.3, 0.0, 1)
                }
                
                if color_name in color_map:
                    chosen_color = color_map[color_name]
                    anim = Animation(foreground_color=chosen_color, cursor_color=chosen_color, duration=0.5)
                    anim.start(self)
                    
                    with open(self.color_config_path, 'w') as f:
                        f.write(color_name)
                    res = f"Text color smoothly changed to '{color_name}'!"
                else:
                    res = "Unknown color. Available:\n" + ", ".join(color_map.keys())

            elif main_cmd == "+g" and args:
                mode = args[0].lower()
                if mode == "on":
                    if not self.glow_active:
                        self.glow_active = True
                        self.glow_anim = Animation(background_color=(0.75, 0.75, 0.75, 1), duration=1.2) + \
                                         Animation(background_color=(0.5, 0.5, 0.5, 1), duration=1.2)
                        self.glow_anim.repeat = True
                        self.glow_anim.start(self)
                        res = "Glow background effect enabled!"
                    else:
                        res = "Glow is already active."
                elif mode == "off":
                    if self.glow_active:
                        self.glow_active = False
                        if self.glow_anim:
                            self.glow_anim.cancel(self)
                        Animation(background_color=(0.5, 0.5, 0.5, 1), duration=0.3).start(self)
                        res = "Glow background effect disabled."
                    else:
                        res = "Glow is already disabled."
                else:
                    res = "Usage: +g on / +g off"

            # --- СОЗИДАНИЕ И РЕДАКТИРОВАНИЕ ---
            elif main_cmd == "+n" and args:
                open(args[0], 'a').close()
                res = f"File '{args[0]}' created."
            
            elif main_cmd == "+f" and args:
                filename = args[0]
                if os.path.exists(filename):
                    with open(filename, 'r') as f:
                        content = f.read()
                    self.terminal_buffer = self.text
                    self.current_edit_file = filename
                    self.editing = True
                    self.text = content
                    return 
                else:
                    res = f"Error: File '{filename}' not found."

            elif main_cmd == "+b" and args:
                shutil.copy(args[0], args[1] if len(args)>1 else args[0] + ".bak")
                res = f"Backup created."

            elif main_cmd == "+z" and args:
                with zipfile.ZipFile(args[0] + '.zip', 'w') as myzip:
                    myzip.write(args[0])
                res = f"Zipped to {args[0]}.zip"

            # --- УДАЛЕНИЕ / ИЗМЕНЕНИЕ ---
            elif main_cmd == "-d" and args:
                os.remove(args[0])
                res = f"File '{args[0]}' deleted."
            elif main_cmd == "-r" and len(args) >= 2:
                os.rename(args[0], args[1])
                res = f"Renamed to {args[1]}."

            # --- ИНФОРМАЦИЯ ---
            elif main_cmd == "?":
                res = self.get_fetch()
            elif main_cmd == "?w" and args:
                files = [f for f in os.listdir('.') if args[0] in f]
                res = "Found: " + ", ".join(files) if files else "Not found."
            elif main_cmd == "?v" and args:
                with open(args[0], 'r') as f:
                    res = f"--- {args[0]} ---\n" + f.read()
            elif main_cmd == "?f":
                res = "Files: " + ", ".join(os.listdir('.'))

            # --- НАВИГАЦИЯ ---
            elif main_cmd == ">>g" and args:
                target = args[0]
                if target.lower() == "downloads" and not os.path.exists(target):
                    target = "/storage/emulated/0/Download"
                if os.path.exists(target):
                    os.chdir(target)
                    res = "Directory changed."
                else:
                    res = f"Error: Path '{target}' not found."

            elif main_cmd == "<<w":
                os.chdir("..")
                res = "Moved back."
                
            elif main_cmd == ">c":
                self.text = "[ Rainy OS Cleared ]\n"
                return

            # --- СИСТЕМА ---
            elif main_cmd == "#h":
                res = "History:\n" + "\n".join(self.history[-5:])
            elif main_cmd == "#t":
                res = f"Uptime: {int(time.time() - self.start_time)}s"
            elif main_cmd == "!q" or main_cmd == "!!!s":
                App.get_running_app().stop()

            else:
                res = f"Rainy: unknown command '{main_cmd}'"

        except Exception as e:
            res = f"Error: {str(e)}"

        self.text += res

    def save_and_exit(self):
        lines = self.text.split('\n')
        content = "\n".join(lines[:-1])
        with open(self.current_edit_file, 'w') as f:
            f.write(content)
        
        self.editing = False
        self.text = self.terminal_buffer + f"\n[ File '{self.current_edit_file}' saved ]"
        self.current_edit_file = ""

    def get_fetch(self):
        uptime = int(time.time() - self.start_time)
        os_type = platform.system()
        
        if os_type == "Linux" and "android" in sys.platform:
            os_display = "Android Kernel"
        else:
            os_display = f"{os_type} {platform.release()}"
            
        py_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        device_arch = platform.machine() or "Unknown"

        return (
            "     ________  \n"
            "   (                )   \n"
            " (                    ) \n"
            " (____________) \n"
            "   /    /    /   /      \n"
            "                           \n"
            f"OS: {os_display}\n"
            f"Arch: {device_arch}\n"
            f"Engine: Python {py_version}\n"
            f"Uptime: {uptime}s\n"
            "Rainy OS v0.7 | Live Environment\n"
        )

class RainyApp(App):
    def build(self):
        return RainyConsole()

if __name__ == "__main__":
    RainyApp().run()