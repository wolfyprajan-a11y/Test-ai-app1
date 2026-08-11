from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.clock import Clock
import threading
import json
import os
import requests
import sys
import io

SETTINGS_FILE = "app_settings.json"
API_URL = "https://api.openai.com/v1/chat/completions"
MODEL = "gpt-4o-mini"

class AIApp(App):
    def build(self):
        self.chat_history = []
        self.root_box = BoxLayout(orientation="vertical", padding=10, spacing=8)
        
        # --- Top Settings Section ---
        self.title = Label(text="AI Coding Shell & Cloud Sync", size_hint_y=None, height=30)
        
        self.keys_input = TextInput(
            hint_text="Paste OpenAI API Keys here (one per line)...",
            multiline=True,
            size_hint_y=0.15
        )
        
        self.cloud_url_input = TextInput(
            hint_text="Google Apps Script WebApp URL (for Google Drive Sync)...",
            multiline=False,
            size_hint_y=None,
            height=40
        )
        
        self.save_settings_btn = Button(text="Save Keys & Settings", size_hint_y=None, height=40)
        self.save_settings_btn.bind(on_press=self.save_settings)
        
        # --- Main Chat & Code Section ---
        self.input_box = TextInput(
            hint_text="Ask AI to write code or answer a question...",
            multiline=True,
            size_hint_y=0.2
        )
        
        # Control Buttons
        btn_box = BoxLayout(orientation="horizontal", size_hint_y=None, height=45, spacing=8)
        self.ask_button = Button(text="Generate Code")
        self.ask_button.bind(on_press=self.ask_ai)
        
        self.run_button = Button(text="Run Code", disabled=True)
        self.run_button.bind(on_press=self.run_code)
        
        self.export_button = Button(text="Save Log to Drive")
        self.export_button.bind(on_press=self.export_to_cloud)
        
        btn_box.add_widget(self.ask_button)
        btn_box.add_widget(self.run_button)
        btn_box.add_widget(self.export_button)
        
        self.status_label = Label(text="Ready", size_hint_y=None, height=25)
        self.output_box = TextInput(text="", readonly=False, multiline=True, size_hint_y=0.45)
        
        # Assemble Layout
        self.root_box.add_widget(self.title)
        self.root_box.add_widget(self.keys_input)
        self.root_box.add_widget(self.cloud_url_input)
        self.root_box.add_widget(self.save_settings_btn)
        self.root_box.add_widget(self.input_box)
        self.root_box.add_widget(btn_box)
        self.root_box.add_widget(self.status_label)
        self.root_box.add_widget(self.output_box)
        
        self.load_settings()
        return self.root_box

    def load_settings(self):
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r") as f:
                    data = json.load(f)
                    self.keys_input.text = "\n".join(data.get("api_keys", []))
                    self.cloud_url_input.text = data.get("cloud_url", "")
            except Exception:
                pass

    def save_settings(self, instance=None):
        keys = [k.strip() for k in self.keys_input.text.split("\n") if k.strip()]
        cloud_url = self.cloud_url_input.text.strip()
        
        data = {"api_keys": keys, "cloud_url": cloud_url}
        with open(SETTINGS_FILE, "w") as f:
            json.dump(data, f)
            
        self.status_label.text = f"Saved {len(keys)} API Key(s) & Settings!"

    def get_api_keys(self):
        return [k.strip() for k in self.keys_input.text.split("\n") if k.strip()]

    def ask_ai(self, instance):
        prompt = self.input_box.text.strip()
        if not prompt:
            self.status_label.text = "Please enter a prompt."
            return
            
        keys = self.get_api_keys()
        if not keys:
            self.status_label.text = "Error: Please paste at least one API key above."
            return

        self.ask_button.disabled = True
        self.run_button.disabled = True
        self.status_label.text = "Thinking..."
        
        threading.Thread(target=self.call_api_with_rotation, args=(prompt, keys), daemon=True).start()

    def call_api_with_rotation(self, prompt, keys):
        last_error = ""
        
        for idx, key in enumerate(keys):
            try:
                Clock.schedule_once(lambda dt, i=idx: setattr(self.status_label, 'text', f"Trying API Key #{i+1}..."))
                
                headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
                payload = {
                    "model": MODEL,
                    "messages": [
                        {"role": "system", "content": "You are a Python coding assistant. Output ONLY raw, executable Python code without markdown syntax."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.2
                }
                
                response = requests.post(API_URL, headers=headers, json=payload, timeout=25)
                response.raise_for_status()
                
                answer = response.json()["choices"][0]["message"]["content"].strip()
                
                # Strip markdown blocks if present
                if answer.startswith("```python"):
                    answer = answer[9:]
                if answer.startswith("```"):
                    answer = answer[3:]
                if answer.endswith("```"):
                    answer = answer[:-3]
                
                answer = answer.strip()
                
                # Save to history
                self.chat_history.append(f"PROMPT:\n{prompt}\n\nRESPONSE:\n{answer}\n" + "="*40)
                
                Clock.schedule_once(lambda dt: self.show_answer(answer))
                return
                
            except Exception as e:
                last_error = str(e)
                continue  # Key failed, automatically rotate to the next key!

        Clock.schedule_once(lambda dt: self.show_error(f"All keys failed. Last error: {last_error}"))

    def show_answer(self, answer):
        self.output_box.text = answer
        self.status_label.text = "Code Generated Successfully"
        self.ask_button.disabled = False
        self.run_button.disabled = False

    def show_error(self, message):
        self.output_box.text = message
        self.status_label.text = "Request Failed"
        self.ask_button.disabled = False
        self.run_button.disabled = False

    def run_code(self, instance):
        code = self.output_box.text.strip()
        if not code:
            return
            
        self.status_label.text = "Executing Code..."
        old_stdout = sys.stdout
        redirected_output = sys.stdout = io.StringIO()
        
        try:
            exec(code)
            result = redirected_output.getvalue()
            output_text = f"--- OUTPUT ---\n{result}"
            self.output_box.text = output_text
            self.chat_history.append(f"EXECUTION RESULT:\n{result}\n" + "="*40)
            self.status_label.text = "Execution Complete"
        except Exception as e:
            self.output_box.text = f"--- EXECUTION ERROR ---\n{str(e)}"
            self.status_label.text = "Execution Error"
        finally:
            sys.stdout = old_stdout

    def export_to_cloud(self, instance):
        url = self.cloud_url_input.text.strip()
        if not url:
            self.status_label.text = "Error: Missing Google WebApp URL above."
            return
            
        if not self.chat_history:
            self.status_label.text = "No chat history to save yet."
            return

        self.status_label.text = "Uploading Log to Google Drive..."
        full_log = "\n\n".join(self.chat_history)
        
        threading.Thread(target=self.post_to_google_drive, args=(url, full_log), daemon=True).start()

    def post_to_google_drive(self, url, log_content):
        try:
            payload = {
                "filename": f"AIShell_Log_{os.urandom(2).hex()}.txt",
                "content": log_content
            }
            response = requests.post(url, json=payload, timeout=20)
            if response.status_code == 200 and "SUCCESS" in response.text:
                Clock.schedule_once(lambda dt: setattr(self.status_label, 'text', "Log Saved to Google Drive!"))
            else:
                Clock.schedule_once(lambda dt: setattr(self.status_label, 'text', f"Upload failed: {response.text}"))
        except Exception as e:
            Clock.schedule_once(lambda dt: setattr(self.status_label, 'text', f"Cloud Sync Error: {e}"))

if __name__ == "__main__":
    AIApp().run()
