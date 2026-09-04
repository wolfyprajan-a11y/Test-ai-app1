import os
import sys
import threading
import traceback
import json
from pathlib import Path
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.clock import Clock

class AIShellApp(App):
    def build(self):
        # Establish isolated data directory
        self.app_dir = Path.home() / ".aishell"
        self.app_dir.mkdir(parents=True, exist_ok=True)
        
        self.layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Responsive output log
        self.scroll = ScrollView(size_hint=(1, 0.7))
        self.output_label = Label(
            text="AI Coding Shell Initialized.\n",
            size_hint_y=None,
            halign="left",
            valign="top",
            font_size='12sp'
        )
        self.output_label.bind(width=lambda *x: self.output_label.setter('text_size')(self.output_label, (self.output_label.width, None)))
        self.output_label.bind(texture_size=self.output_label.setter('size'))
        self.scroll.add_widget(self.output_label)
        self.layout.add_widget(self.scroll)
        
        # Input block with syntax highlighting hint
        self.code_input = TextInput(
            size_hint=(1, 0.2),
            hint_text="Enter Python code...",
            multiline=True,
            font_size='11sp'
        )
        self.layout.add_widget(self.code_input)
        
        # Execution control
        self.run_btn = Button(
            text="Execute Code",
            size_hint=(1, 0.1)
        )
        self.run_btn.bind(on_press=self.execute_code)
        self.layout.add_widget(self.run_btn)
        
        # Load config if exists
        self._load_config()
        
        return self.layout

    def _load_config(self):
        """Load configuration from ~/.aishell/config.json"""
        config_path = self.app_dir / "config.json"
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    self.config = json.load(f)
                    self._append_output(f"[INFO] Config loaded from {config_path}")
            except Exception as e:
                self._append_output(f"[WARNING] Failed to load config: {str(e)}")
                self.config = {}
        else:
            self.config = {}

    def execute_code(self, instance):
        """Execute user code in isolated thread"""
        code = self.code_input.text.strip()
        
        if not code:
            self._append_output("[WARNING] No code to execute")
            return
        
        self.run_btn.disabled = True
        self._append_output(f"\n>>> Executing...\n")
        
        # Thread-safe dispatch
        threading.Thread(target=self._run_code_thread, args=(code,), daemon=True).start()

    def _run_code_thread(self, code):
        """Execute code in restricted namespace"""
        # Enhanced safe namespace with common utilities
        safe_namespace = {
            "__builtins__": {
                "print": self._safe_print,
                "len": len,
                "range": range,
                "str": str,
                "int": int,
                "float": float,
                "list": list,
                "dict": dict,
                "sum": sum,
                "max": max,
                "min": min,
                "abs": abs,
                "round": round,
                "sorted": sorted,
                "enumerate": enumerate,
                "zip": zip,
                "map": map,
                "filter": filter,
                "reversed": reversed,
            },
            "config": self.config
        }
        
        try:
            exec(code, safe_namespace)
            self._append_output("[SUCCESS] Execution completed.")
        except SyntaxError as e:
            # Syntax errors need special handling
            self._append_output(f"[SYNTAX ERROR] {e.msg} at line {e.lineno}")
        except Exception as e:
            # Technical error trace
            error_msg = f"[ERROR] {type(e).__name__}: {str(e)}\n"
            error_msg += "".join(traceback.format_exc())
            self._append_output(error_msg)
        finally:
            Clock.schedule_once(lambda dt: self._re_enable_button())

    def _safe_print(self, *args, **kwargs):
        """Thread-safe print handler"""
        text = " ".join(map(str, args))
        self._append_output(text)

    def _append_output(self, message):
        """Thread-safe UI update"""
        Clock.schedule_once(lambda dt: self._update_ui(message))

    def _update_ui(self, message):
        """Update output label"""
        self.output_label.text += f"{message}\n"
        self.scroll.scroll_y = 0  # Auto-scroll to bottom

    def _re_enable_button(self):
        """Re-enable execute button after code execution"""
        self.run_btn.disabled = False

if __name__ == '__main__':
    AIShellApp().run()
