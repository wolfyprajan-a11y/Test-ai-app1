import os
import sys
import re
import json
import threading
import socket
import webbrowser
from pathlib import Path
import requests
from http.server import BaseHTTPRequestHandler, HTTPServer

# Map Android SSL certificates for secure cloud API access
import certifi
os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout
from kivy.uix.widget import Widget
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp, sp
from kivy.graphics import Color, RoundedRectangle

API_URL = "https://api.openai.com/v1/chat/completions"

# Cleaned Emojis to prevent Android square box rendering bugs
DEFAULT_AGENTS = {
    "✦ Game Architect": {
        "model": "gpt-4o-mini",
        "api_key": "",
        "system_prompt": "You are a game architect. Output clean, modular code.",
        "chips": ["Balance Waves", "Procedural Logic"]
    },
    "▶ Video Director": {
        "model": "gpt-4o-mini",
        "api_key": "",
        "system_prompt": "You are a video director. Output shot lists and pacing notes.",
        "chips": ["Shot List", "Storyboard"]
    },
    "⬢ Minecraft Modder": {
        "model": "gpt-4o-mini",
        "api_key": "",
        "system_prompt": "You are a Minecraft modder. Write custom loot tables.",
        "chips": ["Resolve Forge Conflict", "Recipe Script"]
    },
    "★ Photo & Visuals": {
        "model": "gpt-4o-mini",
        "api_key": "",
        "system_prompt": "You are a master visual prompt engineer.",
        "chips": ["Cinematic Asset", "Environment Prompt"]
    }
}

def get_local_ip():
    """Auto-detects the device's local Wi-Fi IP address."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

class MeshHandler(BaseHTTPRequestHandler):
    """Listens for incoming payloads from the Phone Client."""
    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            phone_payload = json.loads(post_data)
            
            app = App.get_running_app()
            
            def inject_prompt(dt):
                app.open_chat(app.active_agent_name)
                chat_screen = app.sm.get_screen("chat")
                chat_screen.prompt_input.text = phone_payload.get("prompt", "")
                chat_screen.send_prompt(None)
                
            Clock.schedule_once(inject_prompt)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "received"}).encode())
        except Exception:
            self.send_response(500)
            self.end_headers()

    def log_message(self, format, *args):
        return  # Suppress internal server logs

def start_mesh_server():
    """Runs the tablet's local listening server silently."""
    try:
        server = HTTPServer(("0.0.0.0", 5000), MeshHandler)
        server.serve_forever()
    except Exception:
        pass


# --- PREMIUM UI COMPONENTS ---

class RoundedButton(Button):
    def __init__(self, bg_color=(0.14, 0.15, 0.18, 1), radius=12, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_color = (0, 0, 0, 0)
        self.bg_color = bg_color
        self.radius = radius
        with self.canvas.before:
            Color(*self.bg_color)
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(self.radius)])
        self.bind(pos=self._update_rect, size=self._update_rect)

    def _update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

class RoundedInput(TextInput):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_active = ''
        self.background_color = (0, 0, 0, 0)
        self.foreground_color = (1, 1, 1, 1)
        self.cursor_color = (1, 1, 1, 1)
        with self.canvas.before:
            Color(0.16, 0.17, 0.19, 1)
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(22)])
        self.bind(pos=self._update_rect, size=self._update_rect)

    def _update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size


class ChatBubble(BoxLayout):
    def __init__(self, text="", is_user=False, on_handoff=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.size_hint_y = None
        self.padding = [dp(16), dp(12), dp(16), dp(12)]
        self.spacing = dp(6)
        self.is_user = is_user
        self.on_handoff = on_handoff
        self.raw_text = text

        bg_color = (0.16, 0.17, 0.19, 1) if is_user else (0.07, 0.07, 0.08, 1)
        sender_title = "You" if is_user else "AI Shell"
        sender_color = (0.8, 0.8, 0.8, 1) if is_user else (0.4, 0.8, 0.6, 1)

        with self.canvas.before:
            Color(*bg_color)
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(18)])
        self.bind(pos=self._update_rect, size=self._update_rect)

        if not is_user:
            self.add_widget(Label(
                text=f"✦ {sender_title}", size_hint_y=None, height=dp(18),
                font_size=sp(12), bold=True, color=sender_color,
                halign="left", text_size=(Window.width - dp(60), None)
            ))

        self.msg_label = Label(
            text=text, size_hint_y=None, font_size=sp(15),
            color=(0.95, 0.95, 0.95, 1), halign="left", valign="top"
        )
        self.msg_label.bind(width=lambda *x: self.msg_label.setter("text_size")(self.msg_label, (self.msg_label.width, None)))
        self.msg_label.bind(texture_size=lambda *x: self._adjust_height())
        self.add_widget(self.msg_label)

        self.actions_box = BoxLayout(size_hint_y=None, height=dp(34), spacing=dp(8))
        self.add_widget(self.actions_box)
        self._refresh_actions()

    def append_chunk(self, chunk):
        self.raw_text += chunk
        self.msg_label.text = self.raw_text
        self._adjust_height()

    def finalize_stream(self):
        self._refresh_actions()
        self._adjust_height()

    def _refresh_actions(self):
        self.actions_box.clear_widgets()
        if self.is_user or not self.raw_text.strip():
            self.actions_box.height = 0
            return

        has_actions = False
        urls = re.findall(r"https?://[^\s<>\"']+", self.raw_text)
        if urls:
            first_url = urls[0]
            cloud_btn = RoundedButton(
                text="🌐 Open Link", size_hint_x=None, width=dp(120),
                bg_color=(0.15, 0.35, 0.25, 1), font_size=sp(11), bold=True
            )
            cloud_btn.bind(on_press=lambda inst, u=first_url: webbrowser.open(u))
            self.actions_box.add_widget(cloud_btn)
            has_actions = True

        if self.on_handoff:
            handoff_btn = RoundedButton(
                text="✦ Pass to Agent", size_hint_x=None, width=dp(120),
                bg_color=(0.2, 0.25, 0.35, 1), font_size=sp(11)
            )
            handoff_btn.bind(on_press=lambda inst: self.on_handoff(self.raw_text))
            self.actions_box.add_widget(handoff_btn)
            has_actions = True

        self.actions_box.height = dp(34) if has_actions else 0

    def _adjust_height(self):
        self.msg_label.height = self.msg_label.texture_size[1]
        self.height = self.msg_label.height + (dp(40) if not self.is_user else dp(20)) + self.actions_box.height

    def _update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size


# --- SCREENS ---

class HomeScreen(Screen):
    def on_pre_enter(self):
        self.clear_widgets()
        app = App.get_running_app()

        main_layout = BoxLayout(orientation="vertical", padding=[dp(20), dp(20), dp(20), dp(10)], spacing=dp(15))

        # 1. Clean Top Bar
        top_bar = BoxLayout(size_hint_y=None, height=dp(40))
        title = Label(text="✦ AI Shell", font_size=sp(20), bold=True, halign="left", color=(0.9, 0.9, 0.9, 1))
        title.bind(width=lambda *x: title.setter("text_size")(title, (title.width, None)))
        
        settings_btn = Button(text="⚙", size_hint_x=None, width=dp(40), background_normal='', background_color=(0,0,0,0), font_size=sp(24), color=(0.6, 0.6, 0.6, 1))
        settings_btn.bind(on_press=lambda x: app.open_settings_modal())
        
        top_bar.add_widget(title)
        top_bar.add_widget(settings_btn)
        main_layout.add_widget(top_bar)

        main_layout.add_widget(Widget(size_hint_y=None, height=dp(20)))

        # 2. Hero Greeting
        greeting = Label(text="How can I help you today?", font_size=sp(28), bold=True, halign="center", size_hint_y=None, height=dp(40))
        main_layout.add_widget(greeting)

        subtitle = Label(text="Select a persona or start typing below", font_size=sp(14), color=(0.5, 0.5, 0.5, 1), halign="center", size_hint_y=None, height=dp(30))
        main_layout.add_widget(subtitle)

        # 3. 2x2 Agent Card Grid
        grid = GridLayout(cols=2, spacing=dp(12), size_hint_y=None)
        grid.bind(minimum_height=grid.setter("height"))

        for agent_name, agent_data in app.agents.items():
            card = RoundedButton(
                text=agent_name, 
                bg_color=(0.12, 0.13, 0.15, 1), 
                color=(0.85, 0.85, 0.85, 1), 
                font_size=sp(14), 
                bold=True, 
                size_hint_y=None, 
                height=dp(70)
            )
            card.bind(on_press=lambda inst, name=agent_name: app.open_chat(name))
            grid.add_widget(card)

        scroll = ScrollView(size_hint=(1, 1))
        scroll.add_widget(grid)
        main_layout.add_widget(scroll)

        create_btn = Button(text="+ Create custom persona", size_hint_y=None, height=dp(40), background_normal='', background_color=(0,0,0,0), color=(0.4, 0.6, 1, 1), font_size=sp(14))
        create_btn.bind(on_press=lambda x: app.open_create_screen())
        main_layout.add_widget(create_btn)

        # 4. Floating Bottom Prompt Bar
        input_box = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        
        self.prompt_input = RoundedInput(hint_text="Message AI Shell...", padding=[dp(20), dp(15), dp(20), dp(15)])
        self.prompt_input.bind(on_text_validate=self.send_from_home)
        
        send_btn = RoundedButton(text="➤", bg_color=(0.9, 0.9, 0.9, 1), color=(0.1, 0.1, 0.1, 1), size_hint_x=None, width=dp(50), radius=25, bold=True, font_size=sp(18))
        send_btn.bind(on_press=self.send_from_home)
        
        input_box.add_widget(self.prompt_input)
        input_box.add_widget(send_btn)
        
        main_layout.add_widget(input_box)
        self.add_widget(main_layout)

    def send_from_home(self, instance):
        prompt = self.prompt_input.text.strip()
        if prompt:
            app = App.get_running_app()
            app.open_chat(app.active_agent_name)
            chat_screen = app.sm.get_screen("chat")
            chat_screen.prompt_input.text = prompt
            chat_screen.send_prompt(None)
            self.prompt_input.text = ""


class CreateAgentScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation="vertical", padding=dp(20), spacing=dp(15))

        title = Label(text="Create Persona", size_hint_y=None, height=dp(36), font_size=sp(20), bold=True, halign="left")
        title.bind(width=lambda *x: title.setter("text_size")(title, (title.width, None)))
        self.layout.add_widget(title)

        self.name_input = RoundedInput(hint_text="Agent Name...", size_hint_y=None, height=dp(46), multiline=False, font_size=sp(14), padding=[dp(15), dp(12), dp(15), dp(12)])
        self.layout.add_widget(self.name_input)

        self.prompt_input = RoundedInput(hint_text="System Instructions (Define role and cloud steps)...", size_hint_y=0.45, multiline=True, font_size=sp(14), padding=[dp(15), dp(15), dp(15), dp(15)])
        self.layout.add_widget(self.prompt_input)

        self.key_input = RoundedInput(hint_text="Dedicated API Key (sk-...)", size_hint_y=None, height=dp(46), multiline=False, password=True, font_size=sp(14), padding=[dp(15), dp(12), dp(15), dp(12)])
        self.layout.add_widget(self.key_input)

        btn_box = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(10))
        cancel_btn = RoundedButton(text="Cancel", bg_color=(0.2, 0.2, 0.2, 1))
        cancel_btn.bind(on_press=lambda x: App.get_running_app().go_home())
        btn_box.add_widget(cancel_btn)

        save_btn = RoundedButton(text="Save", bg_color=(0.2, 0.7, 0.3, 1), bold=True)
        save_btn.bind(on_press=self.save_agent)
        btn_box.add_widget(save_btn)

        self.layout.add_widget(btn_box)
        self.add_widget(self.layout)

    def save_agent(self, instance):
        name = self.name_input.text.strip()
        prompt = self.prompt_input.text.strip()
        key = self.key_input.text.strip()

        if name:
            app = App.get_running_app()
            app.agents[name] = {"model": "gpt-4o-mini", "api_key": key, "system_prompt": prompt, "chips": ["Refine Instructions"]}
            app.save_data()
            self.name_input.text = ""
            self.prompt_input.text = ""
            self.key_input.text = ""
            app.go_home()


class ChatScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_stream_bubble = None
        self.layout = BoxLayout(orientation="vertical", padding=[dp(10), dp(10), dp(10), dp(10)], spacing=dp(10))

        top_bar = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
        back_btn = RoundedButton(text="❮", size_hint_x=None, width=dp(46), bg_color=(0.14, 0.15, 0.18, 1), font_size=sp(18))
        back_btn.bind(on_press=lambda x: App.get_running_app().go_home())
        top_bar.add_widget(back_btn)

        self.title_label = Label(text="Chat", bold=True, font_size=sp(16), halign="left")
        self.title_label.bind(width=lambda *x: self.title_label.setter("text_size")(self.title_label, (self.title_label.width, None)))
        top_bar.add_widget(self.title_label)

        settings_btn = RoundedButton(text="⚙", size_hint_x=None, width=dp(46), bg_color=(0.14, 0.15, 0.18, 1), font_size=sp(20))
        settings_btn.bind(on_press=lambda x: App.get_running_app().open_settings_modal())
        top_bar.add_widget(settings_btn)
        self.layout.add_widget(top_bar)

        self.chat_scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        self.chat_feed = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(12))
        self.chat_feed.bind(minimum_height=self.chat_feed.setter("height"))
        self.chat_scroll.add_widget(self.chat_feed)
        self.layout.add_widget(self.chat_scroll)

        self.chips_scroll = ScrollView(size_hint_y=None, height=dp(36), do_scroll_y=False)
        self.chips_box = BoxLayout(orientation="horizontal", size_hint_x=None, spacing=dp(6))
        self.chips_box.bind(minimum_width=self.chips_box.setter("width"))
        self.chips_scroll.add_widget(self.chips_box)
        self.layout.add_widget(self.chips_scroll)

        bottom_bar = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        self.prompt_input = RoundedInput(hint_text="Ask this persona...", padding=[dp(20), dp(15), dp(20), dp(15)])
        self.prompt_input.bind(on_text_validate=self.send_prompt)
        bottom_bar.add_widget(self.prompt_input)

        self.send_btn = RoundedButton(text="➤", size_hint_x=None, width=dp(50), radius=25, bg_color=(0.9, 0.9, 0.9, 1), color=(0.1, 0.1, 0.1, 1), font_size=sp(18), bold=True)
        self.send_btn.bind(on_press=self.send_prompt)
        bottom_bar.add_widget(self.send_btn)

        self.layout.add_widget(bottom_bar)
        self.add_widget(self.layout)

    def on_pre_enter(self):
        app = App.get_running_app()
        self.title_label.text = app.active_agent_name
        self.chat_feed.clear_widgets()

        history = app.chat_histories.get(app.active_agent_name, [])
        if history:
            for item in history:
                self.chat_feed.add_widget(ChatBubble(text=item["text"], is_user=item["is_user"], on_handoff=app.open_handoff_modal))
        else:
            self.chat_feed.add_widget(ChatBubble(text=f"Connected to {app.active_agent_name}.", is_user=False, on_handoff=app.open_handoff_modal))

        self.chips_box.clear_widgets()
        agent = app.agents.get(app.active_agent_name, {})
        for chip_text in agent.get("chips", []):
            chip = RoundedButton(text=chip_text, size_hint_x=None, width=dp(len(chip_text) * 8 + 24), bg_color=(0.18, 0.22, 0.28, 1), font_size=sp(12))
            chip.bind(on_press=lambda inst, t=chip_text: self.use_chip(t))
            self.chips_box.add_widget(chip)

    def use_chip(self, text):
        self.prompt_input.text = text
        self.send_prompt(None)

    def scroll_to_bottom(self):
        self.chat_scroll.scroll_y = 0

    def send_prompt(self, instance):
        prompt = self.prompt_input.text.strip()
        if not prompt:
            return

        app = App.get_running_app()
        role = app.app_config.get("role", "Host")
        
        # --- PHONE SATELLITE MODE ---
        if role == "Client":
            target_ip = app.app_config.get("host_ip", "").strip()
            if not target_ip:
                self.chat_feed.add_widget(ChatBubble(text="⚠️ No Tablet IP configured. Tap ⚙️ to set it.", is_user=False))
                return
            
            self.chat_feed.add_widget(ChatBubble(text=prompt, is_user=True))
            app.record_message(prompt, is_user=True)
            self.prompt_input.text = ""
            self.send_btn.disabled = True
            
            self.current_stream_bubble = ChatBubble(text="", is_user=False)
            self.chat_feed.add_widget(self.current_stream_bubble)
            Clock.schedule_once(lambda dt: self.scroll_to_bottom(), 0.05)
            
            def send_to_host():
                try:
                    payload = {"prompt": prompt, "device": "phone"}
                    ip_clean = target_ip.replace("http://", "").replace("https://", "").strip()
                    url = f"http://{ip_clean}:5000"
                    
                    res = requests.post(url, json=payload, timeout=5)
                    res.raise_for_status()
                    Clock.schedule_once(lambda dt: self.current_stream_bubble.append_chunk("✓ Handed off to Tablet Brain. Check tablet screen!"))
                except Exception as e:
                    Clock.schedule_once(lambda dt: self.current_stream_bubble.append_chunk(f"❌ Mesh Error: {str(e)}"))
                finally:
                    Clock.schedule_once(lambda dt: self.current_stream_bubble.finalize_stream())
                    Clock.schedule_once(lambda dt: setattr(self.send_btn, "disabled", False))

            threading.Thread(target=send_to_host, daemon=True).start()
            return

        # --- TABLET HOST MODE ---
        agent = app.agents.get(app.active_agent_name, {})
        api_key = agent.get("api_key", "").strip()

        if not api_key:
            self.chat_feed.add_widget(ChatBubble(text="⚠️ No API key configured. Tap ⚙️ to set your key.", is_user=False))
            return

        self.chat_feed.add_widget(ChatBubble(text=prompt, is_user=True))
        app.record_message(prompt, is_user=True)
        self.prompt_input.text = ""
        self.send_btn.disabled = True

        self.current_stream_bubble = ChatBubble(text="", is_user=False, on_handoff=app.open_handoff_modal)
        self.chat_feed.add_widget(self.current_stream_bubble)
        Clock.schedule_once(lambda dt: self.scroll_to_bottom(), 0.05)

        threading.Thread(target=app.stream_ai_response, args=(prompt, agent, self.current_stream_bubble), daemon=True).start()


# --- APP ORCHESTRATION ---

class AIShellApp(App):
    def build(self):
        Window.bind(on_keyboard=self.on_keyboard)
        Window.clearcolor = (0.07, 0.07, 0.08, 1)

        self.config_dir = Path(self.user_data_dir)
        self.agents_file = self.config_dir / "gemini_agents.json"
        self.config_file = self.config_dir / "app_config.json"

        self.load_data()
        self.chat_histories = {}
        self.active_agent_name = list(self.agents.keys())[0]

        threading.Thread(target=start_mesh_server, daemon=True).start()

        self.sm = ScreenManager(transition=SlideTransition())
        self.sm.add_widget(HomeScreen(name="home"))
        self.sm.add_widget(ChatScreen(name="chat"))
        self.sm.add_widget(CreateAgentScreen(name="create"))

        return self.sm

    def on_keyboard(self, window, key, scancode, codepoint, modifier):
        if key == 27:
            if self.sm.current != "home":
                self.go_home()
                return True
            return False
        return False

    def load_data(self):
        if self.agents_file.exists():
            try:
                with open(self.agents_file, "r") as f:
                    raw_agents = json.load(f)
                    
                    # Silently migrate broken Android Emojis to clean Unicode
                    migration_map = {
                        "🎮 Game Architect": "✦ Game Architect",
                        "🎬 Video Director": "▶ Video Director",
                        "⛏️ Minecraft Modder": "⬢ Minecraft Modder",
                        "🎨 Photo & Visuals": "★ Photo & Visuals"
                    }
                    self.agents = {}
                    for k, v in raw_agents.items():
                        new_key = migration_map.get(k, k)
                        self.agents[new_key] = v
            except Exception:
                self.agents = DEFAULT_AGENTS
        else:
            self.agents = DEFAULT_AGENTS

        if self.config_file.exists():
            try:
                with open(self.config_file, "r") as f:
                    self.app_config = json.load(f)
            except Exception:
                self.app_config = {"role": "Host", "host_ip": ""}
        else:
            self.app_config = {"role": "Host", "host_ip": ""}

    def save_data(self):
        try:
            with open(self.agents_file, "w") as f:
                json.dump(self.agents, f, indent=2)
            with open(self.config_file, "w") as f:
                json.dump(self.app_config, f, indent=2)
        except Exception:
            pass

    def go_home(self):
        self.sm.transition.direction = "right"
        self.sm.current = "home"

    def open_chat(self, agent_name):
        self.active_agent_name = agent_name
        self.sm.transition.direction = "left"
        self.sm.current = "chat"

    def open_create_screen(self):
        self.sm.transition.direction = "left"
        self.sm.current = "create"

    def record_message(self, text, is_user=False):
        if self.active_agent_name not in self.chat_histories:
            self.chat_histories[self.active_agent_name] = []
        self.chat_histories[self.active_agent_name].append({"text": text, "is_user": is_user})

    def stream_ai_response(self, prompt, agent, bubble_widget):
        headers = {"Authorization": f"Bearer {agent['api_key']}", "Content-Type": "application/json"}
        history = self.chat_histories.get(self.active_agent_name, [])[-6:]
        messages = [{"role": "system", "content": agent.get("system_prompt", "")}]
        for item in history:
            messages.append({"role": "user" if item["is_user"] else "assistant", "content": item["text"]})

        payload = {"model": agent.get("model", "gpt-4o-mini"), "messages": messages, "temperature": 0.7, "stream": True}
        accumulated = []
        chat_screen = self.sm.get_screen("chat")

        try:
            res = requests.post(API_URL, headers=headers, json=payload, timeout=60, stream=True)
            res.raise_for_status()

            for line in res.iter_lines():
                if line:
                    decoded = line.decode("utf-8").strip()
                    if decoded.startswith("data: "):
                        data_str = decoded[6:]
                        if data_str == "[DONE]":
                            break
                        try:
                            content_piece = json.loads(data_str)["choices"][0]["delta"].get("content", "")
                            if content_piece:
                                accumulated.append(content_piece)
                                Clock.schedule_once(lambda dt, p=content_piece: bubble_widget.append_chunk(p))
                                Clock.schedule_once(lambda dt: chat_screen.scroll_to_bottom())
                        except Exception:
                            continue

            self.record_message("".join(accumulated), is_user=False)
            Clock.schedule_once(lambda dt: bubble_widget.finalize_stream())
        except Exception as e:
            Clock.schedule_once(lambda dt: bubble_widget.append_chunk(f"❌ Error: {str(e)}"))
            Clock.schedule_once(lambda dt: bubble_widget.finalize_stream())
        finally:
            Clock.schedule_once(lambda dt: setattr(chat_screen.send_btn, "disabled", False))

    def open_handoff_modal(self, text_to_pass):
        box = BoxLayout(orientation="vertical", spacing=dp(8), padding=dp(12))
        box.add_widget(Label(text="Hand off output to which persona?", font_size=sp(14), bold=True, size_hint_y=None, height=dp(30)))
        popup = Popup(title="Agent Handoff", content=box, size_hint=(0.88, 0.55))

        for name in self.agents.keys():
            if name != self.active_agent_name:
                btn = RoundedButton(text=name, size_hint_y=None, height=dp(46), bg_color=(0.18, 0.22, 0.28, 1))
                def _select(inst, target_name=name):
                    popup.dismiss()
                    self.open_chat(target_name)
                    self.sm.get_screen("chat").prompt_input.text = f"Using this specification:\n\n{text_to_pass[:300]}..."
                btn.bind(on_press=_select)
                box.add_widget(btn)
        popup.open()

    def open_settings_modal(self):
        current_agent = self.agents[self.active_agent_name]
        
        box = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(12))
        box.add_widget(Label(text=f"Settings: {self.active_agent_name}", size_hint_y=None, height=dp(25), bold=True, font_size=sp(14)))

        box.add_widget(Label(text="Cloud API Key", size_hint_y=None, height=dp(20), font_size=sp(12)))
        key_input = RoundedInput(text=current_agent.get("api_key", ""), hint_text="sk-...", multiline=False, password=True, size_hint_y=None, height=dp(40), padding=[dp(10), dp(10), dp(10), dp(10)])
        box.add_widget(key_input)

        box.add_widget(Label(text="Device Role", size_hint_y=None, height=dp(20), font_size=sp(12)))
        role_box = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(10))
        
        current_role = self.app_config.get("role", "Host")
        
        host_color = (0.2, 0.7, 0.3, 1) if current_role == "Host" else (0.3, 0.3, 0.3, 1)
        client_color = (0.2, 0.7, 0.3, 1) if current_role == "Client" else (0.3, 0.3, 0.3, 1)
        
        host_btn = RoundedButton(text="Tablet (Host)", bg_color=host_color, bold=True)
        client_btn = RoundedButton(text="Phone (Client)", bg_color=client_color, bold=True)
        
        role_box.add_widget(host_btn)
        role_box.add_widget(client_btn)
        box.add_widget(role_box)

        ip_label = Label(text=f"Host IP Address (My IP: {get_local_ip()})", size_hint_y=None, height=dp(20), font_size=sp(12))
        box.add_widget(ip_label)
        
        ip_input = RoundedInput(text=self.app_config.get("host_ip", ""), hint_text="e.g. 192.168.1.5", multiline=False, size_hint_y=None, height=dp(40), padding=[dp(10), dp(10), dp(10), dp(10)])
        box.add_widget(ip_input)

        save_btn = RoundedButton(text="Save Settings", size_hint_y=None, height=dp(46), bg_color=(0.2, 0.45, 0.9, 1), bold=True)
        box.add_widget(save_btn)

        popup = Popup(title="App Configuration", content=box, size_hint=(0.9, 0.8))
        
        state = {"role": current_role}
        
        def set_host(inst):
            state["role"] = "Host"
            host_btn.bg_color = (0.2, 0.7, 0.3, 1)
            client_btn.bg_color = (0.3, 0.3, 0.3, 1)
            host_btn.canvas.before.clear()
            with host_btn.canvas.before:
                Color(*host_btn.bg_color)
                RoundedRectangle(pos=host_btn.pos, size=host_btn.size, radius=[dp(12)])
            client_btn.canvas.before.clear()
            with client_btn.canvas.before:
                Color(*client_btn.bg_color)
                RoundedRectangle(pos=client_btn.pos, size=client_btn.size, radius=[dp(12)])
            
        def set_client(inst):
            state["role"] = "Client"
            client_btn.bg_color = (0.2, 0.7, 0.3, 1)
            host_btn.bg_color = (0.3, 0.3, 0.3, 1)
            client_btn.canvas.before.clear()
            with client_btn.canvas.before:
                Color(*client_btn.bg_color)
                RoundedRectangle(pos=client_btn.pos, size=client_btn.size, radius=[dp(12)])
            host_btn.canvas.before.clear()
            with host_btn.canvas.before:
                Color(*host_btn.bg_color)
                RoundedRectangle(pos=host_btn.pos, size=host_btn.size, radius=[dp(12)])
            
        host_btn.bind(on_press=set_host)
        client_btn.bind(on_press=set_client)
        
        def _save(inst):
            self.agents[self.active_agent_name]["api_key"] = key_input.text.strip()
            self.app_config["role"] = state["role"]
            self.app_config["host_ip"] = ip_input.text.strip()
            self.save_data()
            popup.dismiss()
            
        save_btn.bind(on_press=_save)
        popup.open()


if __name__ == "__main__":
    AIShellApp().run()
