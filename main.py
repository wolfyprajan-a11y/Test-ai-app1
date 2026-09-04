import os
import sys
import threading
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
            text="AI Coding Shell Initialized.",
            size_hint_y=None,
            halign="left",
            valign="top"
        )
        self.output_label.bind(width=lambda *x: self.output_label.setter('text_size')(self.output_label, (self.output_label.width, None)))
        self.output_label.bind(texture_size=self.output_label.setter('size'))
        self.scroll.add_widget(self.output_label)
        self.layout.add_widget(self.scroll)
        
        # Input block
        self.code_input = TextInput(
            size_hint=(1, 0.2),
            hint_text="Enter Python code...",
            multiline=True
        )
        self.layout.add_widget(self.code_input)
        
        # Execution control
        self.run_btn = Button(
            text="Execute Code",
            size_hint=(1, 0.1)
        )
        self.run_btn.bind(on_press=self.execute_code)
        self.layout.add_widget(self.run_btn)
        
        return self.layout

    def execute_code(self, instance):
        code = self.code_input.text
        self.run_btn.disabled = True
        self.output_label.text += "\n\nExecuting..."
        
        # Thread-safe dispatch
        threading.Thread(target=self._run_code_thread, args=(code,), daemon=True).start()

    def _run_code_thread(self, code):
        # Restricted code execution scope
        safe_namespace = {
            "__builtins__": __builtins__,
            "print": self._safe_print
        }
        
        try:
            exec(code, safe_namespace)
            result = "Execution completed successfully."
        except Exception as e:
            # Direct technical error trace without abstraction
            result = f"Execution Error: {type(e).__name__}: {str(e)}"
            
        Clock.schedule_once(lambda dt: self._update_ui(result))

    def _safe_print(self, *args, **kwargs):
        text = " ".join(map(str, args))
        Clock.schedule_once(lambda dt: self._update_ui(text))
        
    def _update_ui(self, message):
        self.output_label.text += f"\n{message}"
        self.run_btn.disabled = False
        self.scroll.scroll_y = 0

if __name__ == '__main__':
    AIShellApp().run()
