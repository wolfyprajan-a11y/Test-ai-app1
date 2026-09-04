import os
import sys
import re
import json
import threading
import webbrowser
from pathlib import Path
import requests

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

# Default Specialized AI Personas
DEFAULT_AGENTS = {
    "🎮 Game Architect": {
        "model": "gpt-4o-mini",
        "api_key": "",
        "system_prompt": (
            "You are an elite game architect and systems engineer. "
            "You design modular game mechanics, level balance, procedural algorithms, "
            "and cloud-executable game specifications. When generating code, format it "
            "cleanly so it can run directly in a cloud VM or sandbox. "
            "If sharing cloud builds or playable links, make URLs clear."
        ),
        "chips": [
            "Balance Tower Defense Waves",
            "Procedural 3D Map Logic",
            "Godot State Machine Code",
            "Cloud Game Specs"
        ]
    },
    "🎨 Photo & Visuals": {
        "model": "gpt-4o-mini",
        "api_key": "",
        "system_prompt": (
            "You are a master visual prompt engineer and art director. "
            "Transform game concepts and raw ideas into photorealistic, highly-detailed "
            "image generation prompts. Specify cinematic lighting, camera lenses, materials, "
            "color palettes, and render engine parameters."
        ),
        "chips": [
            "Photorealistic Game Asset",
            "Cinematic Boss Concept",
            "Isometric Map Texture",
            "Cyberpunk Character Portrait"
        ]
    },
    "🎬 Video Director": {
        "model": "gpt-4o-mini",
        "api_key": "",
        "system_prompt": (
            "You are an expert video director and sequence editor. "
            "Provide production-ready shot lists, cut timing, camera pacing, "
            "and audio cues. Maintain steady camera perspectives without sudden zooms. "
            "Deliver clean storyboards and transition notes."
        ),
        "chips": [
            "Steady Camera Shot List",
            "Smooth Gameplay Trailer Cut",
            "Cinematic Intro Script",
            "Sound Design & Audio Cues"
        ]
    }
}


class ChatBubble(BoxLayout):
    """Dynamic chat bubble supporting real-time streaming, handoffs, and cloud link detection."""
    def __init__(self, text="", is_user=False, on_handoff=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.size_hint_y = None
        self.padding = [dp(14), dp(10), dp(14), dp(10)]
        self.spacing = dp(6)
        self.is_user = is_user
        self.on_handoff = on_handoff
        self.raw_text = text

        bg_color = (0.16, 0.23, 0.35, 1) if is_user else (0.13, 0.14, 0.16, 1)
        sender_title = "You" if is_user else "AI"
        sender_color = (0.6, 0.8, 1, 1) if is_user else (0.8, 0.6, 1, 1)

        with self.canvas.before:
            Color(*bg_color)
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(16)])
        self.bind(pos=self._update_rect, size=self._update_rect)

        # Header tag
        self.add_widget(Label(
            text=f"✦ {sender_title}",
            size_hint_y=None,
            height=dp(18),
            font_size=sp(12),
            bold=True,
            color=sender_color,
            halign="left",
            text_size=(Window.width - dp(60), None)
        ))

        # Main response body
        self.msg_label = Label(
            text=text,
            size_hint_y=None,
            font_size=sp(14),
            color=(0.93, 0.93, 0.94, 1),
            halign="left",
            valign="top"
        )
        self.msg_label.bind(width=lambda *x: self.msg_label.setter("text_size")(self.msg_label, (self.msg_label.width, None)))
        self.msg_label.bind(texture_size=lambda *x: self._adjust_height())
        self.add_widget(self.msg_label)

        # Action bar container (for cloud links & handoffs)
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

        # Check for URLs (cloud games, GitHub, Replit, zip files)
        urls = re.findall(r"https?://[^\s<>\"']+", self.raw_text)
        if urls:
            first_url = urls[0]
            cloud_btn = Button(
                text="🌐 Open Cloud Link / Play",
                size_hint_x=None,
                width=dp(180),
                background_color=(0.2, 0.6, 0.4, 1),
                font_size=sp(11),
                bold=True
            )
            cloud_btn.bind(on_press=lambda inst, u=first_url: webbrowser.open(u))
            self.actions_box.add_widget(cloud_btn)
            has_actions = True

        # Handoff button to pass output to another agent
        if self.on_handoff:
            handoff_btn = Button(
                text="✦ Pass to Agent...",
                size_hint_x=None,
                width=dp(140),
                background_color=(0.3, 0.35, 0.5, 1),
                font_size=sp(11)
            )
            handoff_btn.bind(on_press=lambda inst: self.on_handoff(self.raw_text))
            self.actions_box.add_widget(handoff_btn)
            has_actions = True

        self.actions_box.height = dp(34) if has_actions else 0

    def _adjust_height(self):
        self.msg_label.height = self.msg_label.texture_size[1]
        self.height = self.msg_label.height + dp(38) + self.actions_box.height

    def _update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size


class HomeScreen(Screen):
    """Dashboard displaying all configured AI Personas."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(12))
        self.add_widget(self.layout)

    def on_pre_enter(self):
        self.layout.clear_widgets()
        app = App.get_running_app()

        # Header Title
        title_box = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(55))
        title = Label(text="Gemini Agent Hub", font_size=sp(24), bold=True, color=(1, 1, 1, 1), halign="left")
        title.bind(width=lambda *x: title.setter("text_size")(title, (title.width, None)))
        subtitle = Label(text="Select or create a specialized AI persona", font_size=sp(13), color=(0.7, 0.7, 0.7, 1), halign="left")
        subtitle.bind(width=lambda *x: subtitle.setter("text_size")(subtitle, (subtitle.width, None)))
        title_box.add_widget(title)
        title_box.add_widget(subtitle)
        self.layout.add_widget(title_box)

        # Agent Cards List
        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        grid = GridLayout(cols=1, spacing=dp(10), size_hint_y=None)
        grid.bind(minimum_height=grid.setter("height"))

        for agent_name, agent_data in app.agents.items():
            has_key = bool(agent_data.get("api_key", "").strip())
            status_text = "[color=33ff88]● Ready[/color]" if has_key else "[color=ffaa33]● Needs API Key[/color]"

            card = Button(
                text=f"{agent_name}\n[size=12sp]{agent_data.get('model', 'gpt-4o-mini')}  |  {status_text}[/size]",
                markup=True,
                size_hint_y=None,
                height=dp(80),
                background_color=(0.14, 0.16, 0.20, 1),
                color=(0.9, 0.93, 1, 1),
                font_size=sp(15),
                bold=True
            )
            card.bind(on_press=lambda inst, name=agent_name: app.open_chat(name))
            grid.add_widget(card)

        scroll.add_widget(grid)
        self.layout.add_widget(scroll)

        # Bottom "+ Create New Agent" Button
        create_btn = Button(
            text="+ Create New AI Persona",
            size_hint_y=None,
            height=dp(52),
            background_color=(0.25, 0.45, 0.9, 1),
            font_size=sp(15),
            bold=True
        )
        create_btn.bind(on_press=lambda x: app.open_create_screen())
        self.layout.add_widget(create_btn)


class CreateAgentScreen(Screen):
    """Form to create, name, and configure a custom persona."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(12))

        title = Label(text="Create Custom Persona", size_hint_y=None, height=dp(36), font_size=sp(20), bold=True, halign="left")
        title.bind(width=lambda *x: title.setter("text_size")(title, (title.width, None)))
        self.layout.add_widget(title)

        self.name_input = TextInput(
            hint_text="Agent Name (e.g. 🛠️ Godot Scripter)",
            size_hint_y=None, height=dp(46), multiline=False, font_size=sp(14),
            background_color=(0.13, 0.14, 0.16, 1), foreground_color=(1, 1, 1, 1)
        )
        self.layout.add_widget(self.name_input)

        self.prompt_input = TextInput(
            hint_text="System Instructions (Define agent role, behavior, and cloud deployment steps)...",
            size_hint_y=0.45, multiline=True, font_size=sp(13),
            background_color=(0.13, 0.14, 0.16, 1), foreground_color=(1, 1, 1, 1)
        )
        self.layout.add_widget(self.prompt_input)

        self.key_input = TextInput(
            hint_text="Dedicated API Key (sk-...)",
            size_hint_y=None, height=dp(46), multiline=False, password=True, font_size=sp(14),
            background_color=(0.13, 0.14, 0.16, 1), foreground_color=(1, 1, 1, 1)
        )
        self.layout.add_widget(self.key_input)

        btn_box = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(10))
        cancel_btn = Button(text="Cancel", background_color=(0.3, 0.3, 0.3, 1), font_size=sp(14))
        cancel_btn.bind(on_press=lambda x: App.get_running_app().go_home())
        btn_box.add_widget(cancel_btn)

        save_btn = Button(text="Save Persona", background_color=(0.2, 0.7, 0.3, 1), font_size=sp(14), bold=True)
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
            app.agents[name] = {
                "model": "gpt-4o-mini",
                "api_key": key,
                "system_prompt": prompt,
                "chips": ["Refine Instructions", "Generate Spec", "Provide Example"]
            }
            app.save_agents()
            self.name_input.text = ""
            self.prompt_input.text = ""
            self.key_input.text = ""
            app.go_home()


class ChatScreen(Screen):
    """Primary chat interface featuring live streaming, handoffs, and contextual chips."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_stream_bubble = None

        self.layout = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(8))

        # Top Bar
        top_bar = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
        back_btn = Button(text="❮", size_hint_x=None, width=dp(46), background_color=(0.18, 0.19, 0.22, 1), font_size=sp(18))
        back_btn.bind(on_press=lambda x: App.get_running_app().go_home())
        top_bar.add_widget(back_btn)

        self.title_label = Label(text="Chat", bold=True, font_size=sp(16), halign="left")
        self.title_label.bind(width=lambda *x: self.title_label.setter("text_size")(self.title_label, (self.title_label.width, None)))
        top_bar.add_widget(self.title_label)

        settings_btn = Button(text="⚙️", size_hint_x=None, width=dp(46), background_color=(0.18, 0.19, 0.22, 1), font_size=sp(16))
        settings_btn.bind(on_press=self.open_settings)
        top_bar.add_widget(settings_btn)
        self.layout.add_widget(top_bar)

        # Chat Stream
        self.chat_scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        self.chat_feed = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(10))
        self.chat_feed.bind(minimum_height=self.chat_feed.setter("height"))
        self.chat_scroll.add_widget(self.chat_feed)
        self.layout.add_widget(self.chat_scroll)

        # Contextual Chips Row
        self.chips_scroll = ScrollView(size_hint_y=None, height=dp(36), do_scroll_y=False)
        self.chips_box = BoxLayout(orientation="horizontal", size_hint_x=None, spacing=dp(6))
        self.chips_box.bind(minimum_width=self.chips_box.setter("width"))
        self.chips_scroll.add_widget(self.chips_box)
        self.layout.add_widget(self.chips_scroll)

        # Bottom Input Pill Bar
        bottom_bar = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(8))
        self.prompt_input = TextInput(
            hint_text="Ask this persona...",
            multiline=False,
            font_size=sp(14),
            background_color=(0.13, 0.14, 0.16, 1),
            foreground_color=(1, 1, 1, 1),
            padding=[dp(12), dp(12), dp(12), dp(12)]
        )
        self.prompt_input.bind(on_text_validate=self.send_prompt)
        bottom_bar.add_widget(self.prompt_input)

        self.send_btn = Button(
            text="➤",
            size_hint_x=None,
            width=dp(50),
            background_color=(0.25, 0.45, 0.9, 1),
            font_size=sp(18),
            bold=True
        )
        self.send_btn.bind(on_press=self.send_prompt)
        bottom_bar.add_widget(self.send_btn)

        self.layout.add_widget(bottom_bar)
        self.add_widget(self.layout)

    def on_pre_enter(self):
        app = App.get_running_app()
        self.title_label.text = app.active_agent_name
        self.chat_feed.clear_widgets()

        # Load message history
        history = app.chat_histories.get(app.active_agent_name, [])
        if history:
            for item in history:
                bubble = ChatBubble(
                    text=item["text"],
                    is_user=item["is_user"],
                    on_handoff=app.open_handoff_modal
                )
                self.chat_feed.add_widget(bubble)
        else:
            bubble = ChatBubble(
                text=f"Connected to {app.active_agent_name}. What shall we build or plan today?",
                is_user=False,
                on_handoff=app.open_handoff_modal
            )
            self.chat_feed.add_widget(bubble)

        # Populate contextual chips
        self.chips_box.clear_widgets()
        agent = app.agents.get(app.active_agent_name, {})
        for chip_text in agent.get("chips", []):
            chip = Button(
                text=chip_text,
                size_hint_x=None,
                width=dp(len(chip_text) * 8 + 24),
                background_color=(0.18, 0.22, 0.28, 1),
                color=(0.8, 0.9, 1, 1),
                font_size=sp(12)
            )
            chip.bind(on_press=lambda inst, t=chip_text: self.use_chip(t))
            self.chips_box.add_widget(chip)

    def use_chip(self, text):
        self.prompt_input.text = text
        self.send_prompt(None)

    def scroll_to_bottom(self):
        self.chat_scroll.scroll_y = 0

    def open_settings(self, instance):
        App.get_running_app().open_settings_modal()

    def send_prompt(self, instance):
        prompt = self.prompt_input.text.strip()
        if not prompt:
            return

        app = App.get_running_app()
        agent = app.agents.get(app.active_agent_name, {})
        api_key = agent.get("api_key", "").strip()

        if not api_key:
            err_bubble = ChatBubble(text="⚠️ No API key configured. Tap ⚙️ at top-right to set your key.", is_user=False)
            self.chat_feed.add_widget(err_bubble)
            return

        # Add user bubble
        user_bubble = ChatBubble(text=prompt, is_user=True)
        self.chat_feed.add_widget(user_bubble)
        app.record_message(prompt, is_user=True)

        self.prompt_input.text = ""
        self.send_btn.disabled = True

        # Add placeholder bubble for streaming response
        self.current_stream_bubble = ChatBubble(
            text="",
            is_user=False,
            on_handoff=app.open_handoff_modal
        )
        self.chat_feed.add_widget(self.current_stream_bubble)
        Clock.schedule_once(lambda dt: self.scroll_to_bottom(), 0.05)

        # Start background stream
        threading.Thread(
            target=app.stream_ai_response,
            args=(prompt, agent, self.current_stream_bubble),
            daemon=True
        ).start()


class AIShellApp(App):
    def build(self):
        Window.bind(on_keyboard=self.on_keyboard)
        Window.clearcolor = (0.07, 0.07, 0.08, 1)

        self.app_dir = Path.home() / ".aishell"
        self.app_dir.mkdir(parents=True, exist_ok=True)
        self.config_file = self.app_dir / "gemini_agents.json"

        self.agents = self.load_agents()
        self.chat_histories = {}
        self.active_agent_name = list(self.agents.keys())[0]

        self.sm = ScreenManager(transition=SlideTransition())
        self.sm.add_widget(HomeScreen(name="home"))
        self.sm.add_widget(ChatScreen(name="chat"))
        self.sm.add_widget(CreateAgentScreen(name="create"))

        return self.sm

    def on_keyboard(self, window, key, scancode, codepoint, modifier):
        if key == 27:  # Android back button
            if self.sm.current != "home":
                self.go_home()
                return True
            return False
        return False

    def load_agents(self):
        if self.config_file.exists():
            try:
                with open(self.config_file, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return DEFAULT_AGENTS

    def save_agents(self):
        try:
            with open(self.config_file, "w") as f:
                json.dump(self.agents, f, indent=2)
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
        """Streams tokens from OpenAI completions endpoint with fallback error handling."""
        headers = {
            "Authorization": f"Bearer {agent['api_key']}",
            "Content-Type": "application/json"
        }

        # Build rolling conversation context (last 6 messages)
        history = self.chat_histories.get(self.active_agent_name, [])[-6:]
        messages = [{"role": "system", "content": agent.get("system_prompt", "")}]
        for item in history:
            role = "user" if item["is_user"] else "assistant"
            messages.append({"role": role, "content": item["text"]})

        payload = {
            "model": agent.get("model", "gpt-4o-mini"),
            "messages": messages,
            "temperature": 0.7,
            "stream": True
        }

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
                            chunk_json = json.loads(data_str)
                            delta = chunk_json["choices"][0]["delta"]
                            content_piece = delta.get("content", "")
                            if content_piece:
                                accumulated.append(content_piece)
                                Clock.schedule_once(lambda dt, p=content_piece: bubble_widget.append_chunk(p))
                                Clock.schedule_once(lambda dt: chat_screen.scroll_to_bottom())
                        except Exception:
                            continue

            full_text = "".join(accumulated)
            self.record_message(full_text, is_user=False)
            Clock.schedule_once(lambda dt: bubble_widget.finalize_stream())

        except Exception as e:
            err_msg = f"❌ Request Error: {str(e)}"
            Clock.schedule_once(lambda dt: bubble_widget.append_chunk(err_msg))
            Clock.schedule_once(lambda dt: bubble_widget.finalize_stream())

        finally:
            Clock.schedule_once(lambda dt: setattr(chat_screen.send_btn, "disabled", False))

    def open_handoff_modal(self, text_to_pass):
        """Allows piping response content into another agent."""
        box = BoxLayout(orientation="vertical", spacing=dp(8), padding=dp(12))
        box.add_widget(Label(text="Hand off output to which persona?", font_size=sp(14), bold=True, size_hint_y=None, height=dp(30)))

        popup = Popup(title="Agent Handoff", content=box, size_hint=(0.88, 0.55))

        for name in self.agents.keys():
            if name != self.active_agent_name:
                btn = Button(text=name, size_hint_y=None, height=dp(42), background_color=(0.18, 0.22, 0.28, 1))

                def _select(inst, target_name=name):
                    popup.dismiss()
                    self.open_chat(target_name)
                    chat_screen = self.sm.get_screen("chat")
                    chat_screen.prompt_input.text = f"Using this specification:\n\n{text_to_pass[:300]}..."

                btn.bind(on_press=_select)
                box.add_widget(btn)

        popup.open()

    def open_settings_modal(self):
        """Edits active agent's credentials and parameters."""
        current_agent = self.agents[self.active_agent_name]

        box = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(12))
        box.add_widget(Label(text=f"Settings: {self.active_agent_name}", size_hint_y=None, height=dp(32), bold=True, font_size=sp(14)))

        key_input = TextInput(
            text=current_agent.get("api_key", ""),
            hint_text="API Key (sk-...)",
            multiline=False, password=True, size_hint_y=None, height=dp(44), font_size=sp(13)
        )
        box.add_widget(key_input)

        save_btn = Button(text="Save Configuration", size_hint_y=None, height=dp(44), background_color=(0.2, 0.7, 0.3, 1), bold=True)
        box.add_widget(save_btn)

        popup = Popup(title="Agent Credentials", content=box, size_hint=(0.88, 0.45))

        def _save(inst):
            self.agents[self.active_agent_name]["api_key"] = key_input.text.strip()
            self.save_agents()
            popup.dismiss()

        save_btn.bind(on_press=_save)
        popup.open()


if __name__ == "__main__":
    AIShellApp().run()
