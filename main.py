import os
import sys
import re
import json
import time
import threading
import socket
import webbrowser
from pathlib import Path
import requests
from http.server import BaseHTTPRequestHandler, HTTPServer

import certifi
os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp, sp
from kivy.graphics import Color, RoundedRectangle, Rectangle
from kivy.animation import Animation

API_URL = "https://api.openai.com/v1/chat/completions"

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
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

class MeshHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            phone_payload = json.loads(post_data)
            
            app = App.get_running_app()
            def inject_prompt(dt):
                app.open_chat(app.active_agent_name)
                chat_screen = app.root_layout.sm.get_screen("chat")
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
        return

def start_mesh_server():
    try:
        server = HTTPServer(("0.0.0.0", 5000), MeshHandler)
        server.serve_forever()
    except Exception:
        pass


# --- LIGHT THEME UI COMPONENTS ---

class RoundedButton(Button):
    def __init__(self, bg_color=(0.9, 0.9, 0.9, 1), radius=12, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_color = (0, 0, 0, 0)
        self.color = (0.1, 0.1, 0.1, 1) # Dark text
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
        self.foreground_color = (0.1, 0.1, 0.1, 1)
        self.cursor_color = (0.1, 0.4, 0.8, 1)
        self.write_tab = False
        with self.canvas.before:
            Color(0.92, 0.93, 0.95, 1)
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(25)])
        self.bind(pos=self._update_rect, size=self._update_rect)

    def _update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size


# --- FIXED SLIDING SIDEBAR ---

class NavigationDrawer(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (1, 1)
        self.is_open = False
        self.disabled = True
        self.opacity = 0
        
        self.panel_width = dp(280)
        
        self.overlay = Button(background_normal='', background_color=(0, 0, 0, 0), size_hint=(1, 1))
        self.overlay.bind(on_press=lambda x: self.close())
        self.add_widget(self.overlay)
        
        # Explicit coordinates instead of X/Y binds for robust Android animations
        self.panel = BoxLayout(orientation='vertical', size_hint=(None, 1), width=self.panel_width)
        self.panel.pos = (-self.panel_width, 0)
        
        with self.panel.canvas.before:
            Color(1, 1, 1, 1) # White sidebar
            self.panel_bg = RoundedRectangle(pos=self.panel.pos, size=self.panel.size)
        self.panel.bind(pos=self._update_bg, size=self._update_bg)

        self.panel.add_widget(Widget(size_hint_y=None, height=dp(20)))
        
        new_chat_btn = RoundedButton(
            text="+  New chat", size_hint=(None, None), width=self.panel_width - dp(32),
            height=dp(45), pos_hint={'center_x': 0.5}, bg_color=(0.92, 0.93, 0.95, 1), bold=True
        )
        new_chat_btn.bind(on_press=lambda x: (self.close(), App.get_running_app().go_home()))
        self.panel.add_widget(new_chat_btn)
        
        self.panel.add_widget(Widget(size_hint_y=None, height=dp(20)))
        self.panel.add_widget(Label(
            text="    Recent Chats", size_hint_y=None, height=dp(20), halign='left',
            text_size=(self.panel_width, None), color=(0.4, 0.4, 0.4, 1), font_size=sp(12), bold=True
        ))
        
        self.recent_list = BoxLayout(orientation='vertical', size_hint_y=None)
        self.recent_list.bind(minimum_height=self.recent_list.setter('height'))
        
        scroll = ScrollView(size_hint=(1, 1))
        scroll.add_widget(self.recent_list)
        self.panel.add_widget(scroll)
        
        settings_btn = Button(
            text="⚙  Settings", size_hint_y=None, height=dp(50), background_normal='',
            background_color=(0, 0, 0, 0), halign='left', text_size=(self.panel_width - dp(40), None),
            color=(0.2, 0.2, 0.2, 1)
        )
        settings_btn.bind(on_press=lambda x: App.get_running_app().open_settings_modal())
        self.panel.add_widget(settings_btn)

        self.add_widget(self.panel)
        self.bind(size=self._reposition_panel)

    def _update_bg(self, *args):
        self.panel_bg.pos = self.panel.pos
        self.panel_bg.size = self.panel.size

    def _reposition_panel(self, *args):
        if not self.is_open:
            self.panel.pos = (-self.panel_width, 0)

    def refresh_recent(self):
        self.recent_list.clear_widgets()
        app = App.get_running_app()
        sorted_sessions = sorted(app.sessions.items(), key=lambda item: item[0], reverse=True)
        
        for session_id, session_data in sorted_sessions:
            title = session_data.get("title", "New Chat")
            btn = Button(
                text=f"  💬 {title}", size_hint_y=None, height=dp(45), background_normal='',
                background_color=(0, 0, 0, 0), halign='left', text_size=(self.panel_width - dp(20), None),
                color=(0.2, 0.2, 0.2, 1)
            )
            btn.bind(on_press=lambda inst, sid=session_id: self.open_chat_and_close(sid))
            self.recent_list.add_widget(btn)

    def open_chat_and_close(self, session_id):
        App.get_running_app().load_session(session_id)
        self.close()

    def toggle(self, *args):
        if self.is_open:
            self.close()
        else:
            self.open()

    def open(self, *args):
        self.refresh_recent()
        self.disabled = False
        self.opacity = 1
        # Use raw pos coordinates for robust animation
        anim = Animation(pos=(0, 0), d=0.25, t='out_quad')
        anim_overlay = Animation(background_color=(0, 0, 0, 0.4), d=0.25)
        anim.start(self.panel)
        anim_overlay.start(self.overlay)
        self.is_open = True

    def close(self, *args):
        anim = Animation(pos=(-self.panel_width, 0), d=0.2, t='in_quad')
        anim_overlay = Animation(background_color=(0, 0, 0, 0), d=0.2)
        def _on_finish(*a):
            self.disabled = True
            self.opacity = 0
            self.is_open = False
        anim.bind(on_complete=_on_finish)
        anim.start(self.panel)
        anim_overlay.start(self.overlay)


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

        bg_color = (0.85, 0.9, 0.98, 1) if is_user else (1, 1, 1, 1)
        sender_title = "You" if is_user else "Gemini"
        sender_color = (0.4, 0.4, 0.4, 1) if is_user else (0.1, 0.4, 0.8, 1)

        with self.canvas.before:
            Color(*bg_color)
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(18)])
        self.bind(pos=self._update_rect, size=self._update_rect)

        if not is_user:
            self.title_lbl = Label(
                text=f"✦ {sender_title}", size_hint_y=None, height=dp(18),
                font_size=sp(12), bold=True, color=sender_color, halign="left"
            )
            self.title_lbl.bind(width=lambda inst, val: setattr(inst, 'text_size', (val, None)))
            self.add_widget(self.title_lbl)

        self.actions_box = BoxLayout(size_hint_y=None, height=0, spacing=dp(8))

        self.msg_label = Label(
            text=text, size_hint_y=None, font_size=sp(15),
            color=(0.1, 0.1, 0.1, 1), halign="left", valign="top"
        )
        self.msg_label.bind(width=lambda inst, val: setattr(inst, 'text_size', (val, None)))
        self.msg_label.bind(texture_size=lambda *x: self._adjust_height())
        self.add_widget(self.msg_label)

        self.add_widget(self.actions_box)
        self._refresh_actions()
        self._adjust_height()

    def append_chunk(self, chunk):
        self.raw_text += chunk
        self.msg_label.text = self.raw_text
        self._adjust_height()

    def finalize_stream(self):
        self._refresh_actions()
        self._adjust_height()

    def _refresh_actions(self):
        if not hasattr(self, 'actions_box'): return
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
                bg_color=(0.1, 0.4, 0.8, 1), color=(1, 1, 1, 1), font_size=sp(11), bold=True
            )
            cloud_btn.bind(on_press=lambda inst, u=first_url: webbrowser.open(u))
            self.actions_box.add_widget(cloud_btn)
            has_actions = True

        self.actions_box.height = dp(34) if has_actions else 0

    def _adjust_height(self):
        if hasattr(self, 'msg_label') and hasattr(self, 'actions_box'):
            self.msg_label.height = self.msg_label.texture_size[1]
            extra = dp(40) if not self.is_user else dp(16)
            self.height = self.msg_label.height + extra + self.actions_box.height

    def _update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size


# --- SCREENS (EXPLICIT WHITE BACKGROUNDS) ---

class BaseWhiteScreen(Screen):
    """Guarantees a white background on Android regardless of Window settings"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(0.96, 0.97, 0.98, 1)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)

    def _update_bg(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size

class HomeScreen(BaseWhiteScreen):
    def on_pre_enter(self):
        self.clear_widgets()
        app = App.get_running_app()
        main_layout = BoxLayout(orientation="vertical", padding=[dp(20), dp(20), dp(20), dp(10)], spacing=dp(15))

        top_bar = BoxLayout(size_hint_y=None, height=dp(40))
        hamburger = Button(
            text="≡", size_hint_x=None, width=dp(50), background_normal='',
            background_color=(0, 0, 0, 0), font_size=sp(28), color=(0.2, 0.2, 0.2, 1)
        )
        hamburger.bind(on_press=lambda x: App.get_running_app().toggle_sidebar())
        
        top_bar.add_widget(hamburger)
        top_bar.add_widget(Label(text="Gemini", font_size=sp(18), bold=True, halign="left", color=(0.2, 0.2, 0.2, 1)))
        main_layout.add_widget(top_bar)
        main_layout.add_widget(Widget(size_hint_y=None, height=dp(30)))

        main_layout.add_widget(Label(
            text="Hello, Balaji", font_size=sp(38), bold=True, halign="center",
            color=(0.1, 0.4, 0.8, 1), size_hint_y=None, height=dp(50)
        ))
        main_layout.add_widget(Label(
            text="How can I help you today?", font_size=sp(24), bold=True,
            color=(0.5, 0.5, 0.5, 1), halign="center", size_hint_y=None, height=dp(30)
        ))
        
        main_layout.add_widget(Widget(size_hint_y=None, height=dp(20)))

        chips_box = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(100), spacing=dp(15))
        for agent_name in list(app.agents.keys())[:2]:
            card = RoundedButton(
                text=f"{agent_name}\n[size=12sp]Ready to chat[/size]", markup=True,
                bg_color=(1, 1, 1, 1), color=(0.2, 0.2, 0.2, 1),
                font_size=sp(14), bold=True, size_hint_x=0.5
            )
            card.bind(on_press=lambda inst, name=agent_name: app.create_new_session(name))
            chips_box.add_widget(card)

        main_layout.add_widget(chips_box)
        main_layout.add_widget(Widget(size_hint_y=1))

        input_box = BoxLayout(size_hint_y=None, height=dp(55), spacing=dp(10))
        self.prompt_input = RoundedInput(hint_text="Ask Gemini...", padding=[dp(20), dp(18), dp(20), dp(18)], font_size=sp(15))
        self.prompt_input.bind(on_text_validate=self.send_from_home)
        
        send_btn = RoundedButton(
            text="➤", bg_color=(0.9, 0.9, 0.9, 1), color=(0.2, 0.2, 0.2, 1),
            size_hint_x=None, width=dp(55), radius=27, bold=True, font_size=sp(18)
        )
        send_btn.bind(on_press=self.send_from_home)
        
        input_box.add_widget(self.prompt_input)
        input_box.add_widget(send_btn)
        
        main_layout.add_widget(input_box)
        self.add_widget(main_layout)

    def send_from_home(self, instance):
        prompt = self.prompt_input.text.strip()
        if prompt:
            app = App.get_running_app()
            self.prompt_input.text = ""
            app.create_new_session(app.active_agent_name)
            app.open_chat_with_prompt(prompt)


class ChatScreen(BaseWhiteScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_stream_bubble = None
        self.layout = BoxLayout(orientation="vertical", padding=[dp(10), dp(10), dp(10), dp(10)], spacing=dp(10))

        top_bar = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
        hamburger = Button(
            text="≡", size_hint_x=None, width=dp(50), background_normal='',
            background_color=(0, 0, 0, 0), font_size=sp(28), color=(0.2, 0.2, 0.2, 1)
        )
        hamburger.bind(on_press=lambda x: App.get_running_app().toggle_sidebar())
        top_bar.add_widget(hamburger)

        self.title_label = Label(text="Chat", bold=True, font_size=sp(16), halign="left", color=(0.2, 0.2, 0.2, 1))
        self.title_label.bind(width=lambda *x: self.title_label.setter("text_size")(self.title_label, (self.title_label.width, None)))
        top_bar.add_widget(self.title_label)

        self.layout.add_widget(top_bar)

        self.chat_scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        self.chat_feed = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(12))
        self.chat_feed.bind(minimum_height=self.chat_feed.setter("height"))
        self.chat_scroll.add_widget(self.chat_feed)
        self.layout.add_widget(self.chat_scroll)

        bottom_bar = BoxLayout(size_hint_y=None, height=dp(55), spacing=dp(10))
        self.prompt_input = RoundedInput(hint_text="Ask Gemini...", padding=[dp(20), dp(18), dp(20), dp(18)], font_size=sp(15))
        self.prompt_input.bind(on_text_validate=self.send_prompt)
        bottom_bar.add_widget(self.prompt_input)

        self.send_btn = RoundedButton(
            text="➤", size_hint_x=None, width=dp(55), radius=27,
            bg_color=(0.9, 0.9, 0.9, 1), color=(0.2, 0.2, 0.2, 1),
            font_size=sp(18), bold=True
        )
        self.send_btn.bind(on_press=self.send_prompt)
        bottom_bar.add_widget(self.send_btn)

        self.layout.add_widget(bottom_bar)
        self.add_widget(self.layout)

    def on_pre_enter(self):
        app = App.get_running_app()
        self.title_label.text = app.active_agent_name
        self.chat_feed.clear_widgets()

        if app.current_session_id and app.current_session_id in app.sessions:
            history = app.sessions[app.current_session_id].get("messages", [])
            for item in history:
                self.chat_feed.add_widget(ChatBubble(text=item["text"], is_user=item["is_user"]))
        else:
            self.chat_feed.add_widget(ChatBubble(text=f"Connected to {app.active_agent_name}.", is_user=False))

    def scroll_to_bottom(self):
        self.chat_scroll.scroll_y = 0

    def send_prompt(self, instance):
        prompt = self.prompt_input.text.strip()
        if not prompt: 
            return

        app = App.get_running_app()
        if not app.current_session_id:
            app.create_new_session(app.active_agent_name, prompt)

        role = app.app_config.get("role", "Host")
        
        if role == "Client":
            target_ip = app.app_config.get("host_ip", "").strip()
            if not target_ip:
                self.chat_feed.add_widget(ChatBubble(text="⚠️ No Tablet IP configured in Settings.", is_user=False))
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
                    ip_clean = target_ip.replace("http://", "").replace("https://", "").strip()
                    res = requests.post(f"http://{ip_clean}:5000", json={"prompt": prompt, "device": "phone"}, timeout=5)
                    res.raise_for_status()
                    Clock.schedule_once(lambda dt: self.current_stream_bubble.append_chunk("✓ Handed off to Tablet Brain."))
                except Exception as e:
                    Clock.schedule_once(lambda dt: self.current_stream_bubble.append_chunk(f"❌ Mesh Error: {str(e)}"))
                finally:
                    Clock.schedule_once(lambda dt: self.current_stream_bubble.finalize_stream())
                    Clock.schedule_once(lambda dt: setattr(self.send_btn, "disabled", False))

            threading.Thread(target=send_to_host, daemon=True).start()
            return

        agent = app.agents.get(app.active_agent_name, {})
        if not agent.get("api_key", "").strip():
            self.chat_feed.add_widget(ChatBubble(text="⚠️ No API key configured in Settings.", is_user=False))
            return

        self.chat_feed.add_widget(ChatBubble(text=prompt, is_user=True))
        app.record_message(prompt, is_user=True)
        self.prompt_input.text = ""
        self.send_btn.disabled = True

        self.current_stream_bubble = ChatBubble(text="", is_user=False)
        self.chat_feed.add_widget(self.current_stream_bubble)
        Clock.schedule_once(lambda dt: self.scroll_to_bottom(), 0.05)
        threading.Thread(target=app.stream_ai_response, args=(prompt, agent, self.current_stream_bubble), daemon=True).start()


class CreateAgentScreen(BaseWhiteScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation="vertical", padding=dp(20), spacing=dp(15))

        title = Label(text="Create Persona", size_hint_y=None, height=dp(36), font_size=sp(20), bold=True, halign="left", color=(0.1,0.1,0.1,1))
        title.bind(width=lambda *x: title.setter("text_size")(title, (title.width, None)))
        self.layout.add_widget(title)

        self.name_input = RoundedInput(hint_text="Agent Name...", size_hint_y=None, height=dp(46), multiline=False, font_size=sp(14), padding=[dp(15), dp(12), dp(15), dp(12)])
        self.layout.add_widget(self.name_input)

        self.prompt_input = RoundedInput(hint_text="System Instructions...", size_hint_y=0.45, multiline=True, font_size=sp(14), padding=[dp(15), dp(15), dp(15), dp(15)])
        self.layout.add_widget(self.prompt_input)

        self.key_input = RoundedInput(hint_text="Dedicated API Key (sk-...)", size_hint_y=None, height=dp(46), multiline=False, password=True, font_size=sp(14), padding=[dp(15), dp(12), dp(15), dp(12)])
        self.layout.add_widget(self.key_input)

        btn_box = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(10))
        cancel_btn = RoundedButton(text="Cancel", bg_color=(0.9, 0.9, 0.9, 1))
        cancel_btn.bind(on_press=lambda x: App.get_running_app().go_home())
        btn_box.add_widget(cancel_btn)

        save_btn = RoundedButton(text="Save", bg_color=(0.1, 0.8, 0.4, 1), color=(1,1,1,1), bold=True)
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


# --- ROOT ORCHESTRATION ---

class RootLayout(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.sm = ScreenManager(transition=SlideTransition())
        self.sm.add_widget(HomeScreen(name="home"))
        self.sm.add_widget(ChatScreen(name="chat"))
        self.sm.add_widget(CreateAgentScreen(name="create"))
        
        self.sidebar = NavigationDrawer()
        
        self.add_widget(self.sm)
        self.add_widget(self.sidebar)

class AIShellApp(App):
    def build(self):
        # Prevent Android keyboard from hiding the input bar
        Window.softinput_mode = 'below_target'

        self.config_dir = Path(self.user_data_dir)
        self.agents_file = self.config_dir / "gemini_agents.json"
        self.config_file = self.config_dir / "app_config.json"
        self.sessions_file = self.config_dir / "chat_sessions.json"

        self.load_data()
        self.current_session_id = None
        self.active_agent_name = list(self.agents.keys())[0]

        threading.Thread(target=start_mesh_server, daemon=True).start()

        self.root_layout = RootLayout()
        return self.root_layout

    def toggle_sidebar(self):
        if hasattr(self, 'root_layout') and self.root_layout and hasattr(self.root_layout, 'sidebar'):
            self.root_layout.sidebar.toggle()

    def on_keyboard(self, window, key, scancode, codepoint, modifier):
        if key == 27:
            if hasattr(self, 'root_layout') and self.root_layout.sidebar.is_open:
                self.root_layout.sidebar.close()
                return True
            if hasattr(self, 'root_layout') and self.root_layout.sm.current != "home":
                self.go_home()
                return True
            return False
        return False

    def load_data(self):
        if self.agents_file.exists():
            try:
                with open(self.agents_file, "r") as f: self.agents = json.load(f)
            except: self.agents = DEFAULT_AGENTS
        else: self.agents = DEFAULT_AGENTS

        if self.config_file.exists():
            try:
                with open(self.config_file, "r") as f: self.app_config = json.load(f)
            except: self.app_config = {"role": "Host", "host_ip": ""}
        else: self.app_config = {"role": "Host", "host_ip": ""}
        
        if self.sessions_file.exists():
            try:
                with open(self.sessions_file, "r") as f: self.sessions = json.load(f)
            except: self.sessions = {}
        else: self.sessions = {}

    def save_data(self):
        try:
            with open(self.agents_file, "w") as f: json.dump(self.agents, f, indent=2)
            with open(self.config_file, "w") as f: json.dump(self.app_config, f, indent=2)
            with open(self.sessions_file, "w") as f: json.dump(self.sessions, f, indent=2)
        except Exception:
            pass

    def go_home(self):
        self.current_session_id = None
        self.root_layout.sm.transition.direction = "right"
        self.root_layout.sm.current = "home"

    def create_new_session(self, agent_name, initial_prompt="New Chat"):
        self.active_agent_name = agent_name
        self.current_session_id = str(int(time.time()))
        title = initial_prompt[:25] + "..." if len(initial_prompt) > 25 else initial_prompt
        self.sessions[self.current_session_id] = {
            "title": title,
            "agent": agent_name,
            "messages": []
        }
        self.save_data()
        self.open_chat(agent_name)

    def load_session(self, session_id):
        if session_id in self.sessions:
            self.current_session_id = session_id
            self.active_agent_name = self.sessions[session_id].get("agent", list(self.agents.keys())[0])
            self.open_chat(self.active_agent_name)

    def open_chat(self, agent_name):
        self.active_agent_name = agent_name
        self.root_layout.sm.transition.direction = "left"
        self.root_layout.sm.current = "chat"

    def open_chat_with_prompt(self, prompt):
        self.open_chat(self.active_agent_name)
        def _trigger(dt):
            chat_screen = self.root_layout.sm.get_screen("chat")
            chat_screen.prompt_input.text = prompt
            chat_screen.send_prompt(None)
        Clock.schedule_once(_trigger, 0.05)

    def record_message(self, text, is_user=False):
        if self.current_session_id and self.current_session_id in self.sessions:
            self.sessions[self.current_session_id]["messages"].append({"text": text, "is_user": is_user})
            self.save_data()

    def stream_ai_response(self, prompt, agent, bubble_widget):
        headers = {"Authorization": f"Bearer {agent['api_key']}", "Content-Type": "application/json"}
        
        messages = [{"role": "system", "content": agent.get("system_prompt", "")}]
        if self.current_session_id and self.current_session_id in self.sessions:
            history = self.sessions[self.current_session_id]["messages"][-6:]
            for item in history: 
                messages.append({"role": "user" if item["is_user"] else "assistant", "content": item["text"]})

        payload = {"model": agent.get("model", "gpt-4o-mini"), "messages": messages, "temperature": 0.7, "stream": True}
        accumulated = []
        chat_screen = self.root_layout.sm.get_screen("chat")

        try:
            res = requests.post(API_URL, headers=headers, json=payload, timeout=60, stream=True)
            res.raise_for_status()

            for line in res.iter_lines():
                if line:
                    decoded = line.decode("utf-8").strip()
                    if decoded.startswith("data: "):
                        data_str = decoded[6:]
                        if data_str == "[DONE]": break
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

    def open_settings_modal(self):
        if hasattr(self, 'root_layout') and self.root_layout.sidebar.is_open:
            self.root_layout.sidebar.close()
            
        current_agent = self.agents.get(self.active_agent_name, {})
        box = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(12))
        
        box.add_widget(Label(text="Cloud API Key", size_hint_y=None, height=dp(20), font_size=sp(12), color=(0.1, 0.1, 0.1, 1)))
        key_input = RoundedInput(
            text=current_agent.get("api_key", ""), hint_text="sk-...", multiline=False,
            password=True, size_hint_y=None, height=dp(40), padding=[dp(10), dp(10), dp(10), dp(10)]
        )
        box.add_widget(key_input)

        box.add_widget(Label(text="Device Role", size_hint_y=None, height=dp(20), font_size=sp(12), color=(0.1, 0.1, 0.1, 1)))
        role_box = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(10))
        current_role = self.app_config.get("role", "Host")
        
        host_btn = RoundedButton(
            text="Tablet (Host)",
            bg_color=(0.1, 0.4, 0.8, 1) if current_role == "Host" else (0.9, 0.9, 0.9, 1),
            color=(1,1,1,1) if current_role == "Host" else (0.1,0.1,0.1,1),
            bold=True
        )
        client_btn = RoundedButton(
            text="Phone (Client)",
            bg_color=(0.1, 0.4, 0.8, 1) if current_role == "Client" else (0.9, 0.9, 0.9, 1),
            color=(1,1,1,1) if current_role == "Client" else (0.1,0.1,0.1,1),
            bold=True
        )
        
        role_box.add_widget(host_btn)
        role_box.add_widget(client_btn)
        box.add_widget(role_box)

        box.add_widget(Label(text=f"Host IP Address (My IP: {get_local_ip()})", size_hint_y=None, height=dp(20), font_size=sp(12), color=(0.1, 0.1, 0.1, 1)))
        ip_input = RoundedInput(
            text=self.app_config.get("host_ip", ""), hint_text="e.g. 192.168.1.5",
            multiline=False, size_hint_y=None, height=dp(40), padding=[dp(10), dp(10), dp(10), dp(10)]
        )
        box.add_widget(ip_input)

        save_btn = RoundedButton(text="Save Settings", size_hint_y=None, height=dp(46), bg_color=(0.1, 0.8, 0.4, 1), color=(1,1,1,1), bold=True)
        box.add_widget(save_btn)

        popup = Popup(title="Settings", content=box, size_hint=(0.9, 0.8), background_color=(1,1,1,1), title_color=(0.1,0.1,0.1,1))
        state = {"role": current_role}
        
        def set_host(inst):
            state["role"] = "Host"
            host_btn.bg_color = (0.1, 0.4, 0.8, 1); host_btn.color = (1,1,1,1)
            client_btn.bg_color = (0.9, 0.9, 0.9, 1); client_btn.color = (0.1,0.1,0.1,1)
            host_btn._update_rect(); client_btn._update_rect()
            
        def set_client(inst):
            state["role"] = "Client"
            client_btn.bg_color = (0.1, 0.4, 0.8, 1); client_btn.color = (1,1,1,1)
            host_btn.bg_color = (0.9, 0.9, 0.9, 1); host_btn.color = (0.1,0.1,0.1,1)
            client_btn._update_rect(); host_btn._update_rect()
            
        host_btn.bind(on_press=set_host)
        client_btn.bind(on_press=set_client)
        
        def _save(inst):
            if self.active_agent_name in self.agents:
                self.agents[self.active_agent_name]["api_key"] = key_input.text.strip()
            self.app_config["role"] = state["role"]
            self.app_config["host_ip"] = ip_input.text.strip()
            self.save_data()
            popup.dismiss()
            
        save_btn.bind(on_press=_save)
        popup.open()

if __name__ == "__main__":
    AIShellApp().run()
