from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
import sys
import io

class AICodingShellApp(App):
    def build(self):
        self.layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        self.output_box = TextInput(text="[SYSTEM] AI Shell Initialized. Ready for code...\n", readonly=True, size_hint=(1, 0.75), background_color=(0.05, 0.05, 0.05, 1), foreground_color=(0, 1, 0, 1))
        self.layout.add_widget(self.output_box)
        self.input_box = TextInput(hint_text="Type Python code here...", size_hint=(1, 0.15), background_color=(0.9, 0.9, 0.9, 1))
        self.layout.add_widget(self.input_box)
        self.run_btn = Button(text="EXECUTE", size_hint=(1, 0.1), background_color=(0.2, 0.6, 1, 1), bold=True)
        self.run_btn.bind(on_press=self.execute_code)
        self.layout.add_widget(self.run_btn)
        return self.layout

    def execute_code(self, instance):
        user_code = self.input_box.text
        if not user_code.strip(): return
        self.output_box.text += f"\n>>> {user_code}\n"
        old_stdout = sys.stdout
        redirected_output = sys.stdout = io.StringIO()
        try:
            exec(user_code)
            self.output_box.text += redirected_output.getvalue()
        except Exception as e:
            self.output_box.text += f"ERROR: {str(e)}\n"
        finally:
            sys.stdout = old_stdout
        self.input_box.text = ""

if __name__ == '__main__':
    AICodingShellApp().run()
