#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
netRDP - Windows Remote Desktop Connection tarzı, karanlık temalı gelişmiş RDP istemcisi
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib
import subprocess
import os
import json
import threading

# ── Paths ──────────────────────────────────────────────────────────────────────
APP_DIR       = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR    = os.path.expanduser("~/.config/netrdp")
CONFIG_FILE   = os.path.join(CONFIG_DIR, "connections.json")
SETTINGS_FILE = os.path.join(CONFIG_DIR, "settings.json")
CSS_FILE      = os.path.join(APP_DIR, "netrdp_style.css")
I18N_FILE     = os.path.join(APP_DIR, "translations.json")


# ── JSON I/O ───────────────────────────────────────────────────────────────────
def load_json(path, fallback):
    if not os.path.exists(path):
        return fallback
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return fallback


def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ── Translations ───────────────────────────────────────────────────────────────
TRANSLATIONS = load_json(I18N_FILE, {})

# Minimal built-in English fallback — used only if translations.json is missing
_FALLBACK = {
    "tab_general": "General", "tab_saved": "Saved",
    "label_computer": "Computer:", "label_user": "User name:",
    "label_password": "Password:", "label_domain": "Domain:",
    "label_colordepth": "Color depth:", "hint": "Credentials will be requested.",
    "save_check": "Save this connection", "alias_placeholder": "Alias (optional)",
    "alias_label": "Alias:", "host_placeholder": "192.168.1.100:3389",
    "user_placeholder": "Username (optional)", "pass_placeholder": "Password (optional)",
    "options_show": "Show Options", "options_hide": "Hide Options",
    "section_options": "CONNECTION OPTIONS", "section_language": "LANGUAGE",
    "chk_clipboard": "Clipboard", "chk_audio": "Audio", "chk_drives": "Drives",
    "chk_nla": "NLA auth", "chk_cert": "Ignore TLS cert",
    "btn_connect": "Connect", "btn_help": "Help",
    "btn_clear": "Clear all", "btn_load": "Connect",
    "status_ready": "Ready", "status_connecting": "Connecting: {label} ...",
    "status_closed": "Connection closed.",
    "status_timeout": "Timeout: {host}:{port} unreachable.",
    "status_error": "Error ({rc}): {err}",
    "status_notfound": "xfreerdp not found!",
    "status_host_empty": "Error: host is empty!",
    "help_title": "netRDP", "help_body": "Enter host and click Connect.",
    "confirm_clear": "Delete all saved connections?",
    "user_missing": "No user", "banner_title": "Remote Desktop",
    "banner_subtitle": "Connection", "count_label": "{n} saved",
}


class netRDPWindow(Gtk.Window):

    def __init__(self):
        super().__init__(title="netRDP Client")
        self.set_default_size(460, -1)
        self.set_resizable(False)
        self.set_border_width(0)
        self.set_position(Gtk.WindowPosition.CENTER)

        self._load_css()

        self.lang        = "en"
        self.connections = load_json(CONFIG_FILE, [])
        self.settings    = load_json(SETTINGS_FILE, {})

        self._build_ui()
        self._load_settings_to_ui()
        self._refresh_saved()

    # ── CSS ────────────────────────────────────────────────────────────────────
    def _load_css(self):
        css = Gtk.CssProvider()
        if os.path.exists(CSS_FILE):
            css.load_from_path(CSS_FILE)
        else:
            print(f"Warning: stylesheet not found: {CSS_FILE}")
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), css,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

    # ── i18n ───────────────────────────────────────────────────────────────────
    def _(self, key, **kwargs):
        lang_dict = TRANSLATIONS.get(self.lang, {})
        text = (
            lang_dict.get(key)
            or TRANSLATIONS.get("en", {}).get(key)
            or _FALLBACK.get(key, key)
        )
        return text.format(**kwargs) if kwargs else text

    # ── UI build ───────────────────────────────────────────────────────────────
    def _build_ui(self):
        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(root)

        root.pack_start(self._banner(), False, False, 0)

        self.nb = Gtk.Notebook()
        self.nb.set_show_border(False)
        root.pack_start(self.nb, True, True, 0)

        self._tab_lbl1 = Gtk.Label(label=self._("tab_general"))
        self.nb.append_page(self._connect_page(), self._tab_lbl1)

        self._tab_lbl2 = Gtk.Label(label=self._("tab_saved"))
        self.nb.append_page(self._saved_page(), self._tab_lbl2)

        root.pack_end(self._statusbar(), False, False, 0)

    def _banner(self):
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        box.get_style_context().add_class("banner")

        icon = Gtk.Label()
        icon.set_markup('<span font="24">&#x1F5A5;</span>')

        text = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
        self._banner_t1 = Gtk.Label(label=self._("banner_title"))
        self._banner_t1.get_style_context().add_class("banner-title")
        self._banner_t1.set_xalign(0)
        self._banner_t2 = Gtk.Label(label=self._("banner_subtitle"))
        self._banner_t2.get_style_context().add_class("banner-subtitle")
        self._banner_t2.set_xalign(0)
        text.pack_start(self._banner_t1, False, False, 0)
        text.pack_start(self._banner_t2, False, False, 0)

        box.pack_start(icon, False, False, 0)
        box.pack_start(text, False, False, 0)
        return box

    def _connect_page(self):
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        # ── Form grid ──
        form = Gtk.Grid()
        form.get_style_context().add_class("form-area")
        form.set_row_spacing(8)
        form.set_column_spacing(12)

        def field_label(key):
            lbl = Gtk.Label(label=self._(key))
            lbl.get_style_context().add_class("field-label")
            lbl.set_xalign(1)
            return lbl

        self._lbl_computer = field_label("label_computer")
        self.host_entry = Gtk.Entry()
        self.host_entry.set_placeholder_text(self._("host_placeholder"))
        self.host_entry.set_hexpand(True)
        self.host_entry.connect("changed",  self._on_host_changed)
        self.host_entry.connect("activate", self._on_enter_key)
        form.attach(self._lbl_computer, 0, 0, 1, 1)
        form.attach(self.host_entry,    1, 0, 1, 1)

        self._lbl_user = field_label("label_user")
        self.user_entry = Gtk.Entry()
        self.user_entry.set_placeholder_text(self._("user_placeholder"))
        self.user_entry.set_hexpand(True)
        form.attach(self._lbl_user,  0, 1, 1, 1)
        form.attach(self.user_entry, 1, 1, 1, 1)

        self._lbl_pass = field_label("label_password")
        self.pass_entry = Gtk.Entry()
        self.pass_entry.set_visibility(False)
        self.pass_entry.set_placeholder_text(self._("pass_placeholder"))
        self.pass_entry.set_input_purpose(Gtk.InputPurpose.PASSWORD)
        self.pass_entry.set_hexpand(True)
        self.pass_entry.connect("activate", self._on_enter_key)
        form.attach(self._lbl_pass,  0, 2, 1, 1)
        form.attach(self.pass_entry, 1, 2, 1, 1)

        self._hint_lbl = Gtk.Label(label=self._("hint"))
        self._hint_lbl.get_style_context().add_class("hint-label")
        self._hint_lbl.set_xalign(0)
        self._hint_lbl.set_margin_top(4)
        form.attach(self._hint_lbl, 0, 3, 2, 1)

        self.save_check = Gtk.CheckButton(label=self._("save_check"))
        self.save_check.set_margin_top(6)
        self.save_check.connect("toggled", self._on_save_check_toggled)
        form.attach(self.save_check, 0, 4, 2, 1)

        # Alias revealer
        self.alias_revealer = Gtk.Revealer()
        self.alias_revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_DOWN)
        self.alias_revealer.set_transition_duration(150)
        self.alias_revealer.set_reveal_child(False)
        alias_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        alias_box.set_margin_top(4)
        self._alias_lbl = Gtk.Label(label=self._("alias_label"))
        self._alias_lbl.get_style_context().add_class("field-label")
        self._alias_lbl.set_xalign(1)
        self._alias_lbl.set_width_chars(9)
        self.alias_entry = Gtk.Entry()
        self.alias_entry.set_placeholder_text(self._("alias_placeholder"))
        self.alias_entry.set_hexpand(True)
        alias_box.pack_start(self._alias_lbl,  False, False, 0)
        alias_box.pack_start(self.alias_entry, True,  True,  0)
        self.alias_revealer.add(alias_box)
        form.attach(self.alias_revealer, 0, 5, 2, 1)

        page.pack_start(form, False, False, 0)

        # ── Advanced options revealer ──
        self.adv_revealer = Gtk.Revealer()
        self.adv_revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_DOWN)
        self.adv_revealer.set_transition_duration(180)
        self.adv_revealer.set_reveal_child(False)

        adv = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        adv.get_style_context().add_class("options-area")

        self._sec_options_lbl = Gtk.Label(label=self._("section_options"))
        self._sec_options_lbl.get_style_context().add_class("section-label")
        self._sec_options_lbl.set_xalign(0)
        adv.pack_start(self._sec_options_lbl, False, False, 0)

        self.chk_clipboard = Gtk.CheckButton(label=self._("chk_clipboard"))
        self.chk_clipboard.set_active(True)
        self.chk_audio = Gtk.CheckButton(label=self._("chk_audio"))
        self.chk_audio.set_active(True)
        self.chk_drives = Gtk.CheckButton(label=self._("chk_drives"))
        self.chk_nla    = Gtk.CheckButton(label=self._("chk_nla"))
        self.chk_nla.set_active(True)
        self.chk_cert   = Gtk.CheckButton(label=self._("chk_cert"))

        for chk in [self.chk_clipboard, self.chk_audio,
                    self.chk_drives, self.chk_nla, self.chk_cert]:
            adv.pack_start(chk, False, False, 0)
            chk.connect("toggled", self._on_option_changed)

        # Domain row
        dom_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self._lbl_domain = Gtk.Label(label=self._("label_domain"))
        self._lbl_domain.get_style_context().add_class("field-label")
        self._lbl_domain.set_xalign(1)
        self._lbl_domain.set_width_chars(13)
        self.domain_entry = Gtk.Entry()
        self.domain_entry.set_placeholder_text("WORKGROUP")
        self.domain_entry.set_hexpand(True)
        self.domain_entry.connect("changed", self._on_option_changed)
        dom_row.pack_start(self._lbl_domain,  False, False, 0)
        dom_row.pack_start(self.domain_entry, True,  True,  0)
        adv.pack_start(dom_row, False, False, 0)

        # Color depth row
        bpp_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self._lbl_bpp = Gtk.Label(label=self._("label_colordepth"))
        self._lbl_bpp.get_style_context().add_class("field-label")
        self._lbl_bpp.set_xalign(1)
        self._lbl_bpp.set_width_chars(13)
        self.bpp_combo = Gtk.ComboBoxText()
        for label, val in [("32-bit", "32"), ("24-bit", "24"), ("16-bit", "16")]:
            self.bpp_combo.append(val, label)
        self.bpp_combo.set_active(0)
        self.bpp_combo.set_hexpand(True)
        self.bpp_combo.connect("changed", self._on_option_changed)
        bpp_row.pack_start(self._lbl_bpp,  False, False, 0)
        bpp_row.pack_start(self.bpp_combo, True,  True,  0)
        adv.pack_start(bpp_row, False, False, 0)

        sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        sep.set_margin_top(4)
        sep.set_margin_bottom(2)
        adv.pack_start(sep, False, False, 0)

        # Language row
        self._sec_lang_lbl = Gtk.Label(label=self._("section_language"))
        self._sec_lang_lbl.get_style_context().add_class("section-label")
        self._sec_lang_lbl.set_xalign(0)
        adv.pack_start(self._sec_lang_lbl, False, False, 0)

        lang_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        lang_icon = Gtk.Label(label="🌐")
        lang_icon.set_margin_end(2)
        self.lang_combo = Gtk.ComboBoxText()
        for lang_id, lang_dict in TRANSLATIONS.items():
            lang_name = lang_dict.get("_name", lang_id)
            self.lang_combo.append(lang_id, lang_name)
        self.lang_combo.set_active_id(self.lang)
        self.lang_combo.set_size_request(150, -1)
        self.lang_combo.connect("changed", self._on_lang_changed)
        lang_row.pack_start(lang_icon,       False, False, 0)
        lang_row.pack_start(self.lang_combo, False, False, 0)
        adv.pack_start(lang_row, False, False, 0)

        self.adv_revealer.add(adv)
        page.pack_start(self.adv_revealer, False, False, 0)

        # ── Button bar ──
        bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        bar.get_style_context().add_class("button-bar")

        self.options_btn = Gtk.ToggleButton()
        self.options_btn.get_style_context().add_class("btn-options")
        self.options_btn.connect("toggled", self._on_options_toggle)
        opt_inner = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        self.arrow_lbl     = Gtk.Label(label="v")
        self._opt_text_lbl = Gtk.Label(label=self._("options_show"))
        opt_inner.pack_start(self.arrow_lbl,     False, False, 0)
        opt_inner.pack_start(self._opt_text_lbl, False, False, 0)
        self.options_btn.add(opt_inner)

        spacer = Gtk.Box()
        spacer.set_hexpand(True)

        self.help_btn = Gtk.Button(label=self._("btn_help"))
        self.help_btn.get_style_context().add_class("btn-cancel")
        self.help_btn.connect("clicked", self._on_help)

        self.connect_btn = Gtk.Button(label=self._("btn_connect"))
        self.connect_btn.get_style_context().add_class("btn-connect")
        self.connect_btn.set_sensitive(False)
        self.connect_btn.connect("clicked", self._on_connect)

        bar.pack_start(self.options_btn, False, False, 0)
        bar.pack_start(spacer,           True,  True,  0)
        bar.pack_start(self.help_btn,    False, False, 0)
        bar.pack_start(self.connect_btn, False, False, 0)

        page.pack_start(bar, False, False, 0)
        return page

    def _saved_page(self):
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_min_content_height(200)
        self.saved_lb = Gtk.ListBox()
        self.saved_lb.get_style_context().add_class("saved-list")
        self.saved_lb.set_selection_mode(Gtk.SelectionMode.NONE)
        scroll.add(self.saved_lb)
        page.pack_start(scroll, True, True, 0)

        footer = Gtk.Box()
        footer.get_style_context().add_class("button-bar")
        self.clr_btn = Gtk.Button(label=self._("btn_clear"))
        self.clr_btn.get_style_context().add_class("btn-cancel")
        self.clr_btn.connect("clicked", self._on_clear_all)
        footer.pack_end(self.clr_btn, False, False, 0)
        page.pack_end(footer, False, False, 0)
        return page

    def _statusbar(self):
        bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        bar.get_style_context().add_class("statusbar")
        self.status_lbl = Gtk.Label(label=self._("status_ready"))
        self.status_lbl.get_style_context().add_class("status-text")
        self.status_lbl.set_xalign(0)
        self.count_lbl = Gtk.Label()
        self.count_lbl.get_style_context().add_class("count-label")
        bar.pack_start(self.status_lbl, False, False, 0)
        bar.pack_end(self.count_lbl,   False, False, 0)
        return bar

    # ── Settings ───────────────────────────────────────────────────────────────
    def _load_settings_to_ui(self):
        s = self.settings
        # Only restore saved language if settings.json explicitly contains it
        saved_lang = s.get("lang") if s else None
        if saved_lang and saved_lang in TRANSLATIONS:
            self.lang = saved_lang
            self.lang_combo.set_active_id(self.lang)
            self._apply_translations()
        self.chk_clipboard.set_active(s.get("clipboard", True))
        self.chk_audio.set_active(s.get("audio",         True))
        self.chk_drives.set_active(s.get("drives",       False))
        self.chk_nla.set_active(s.get("nla",             True))
        self.chk_cert.set_active(s.get("cert",           False))
        self.domain_entry.set_text(s.get("domain",       ""))
        self.bpp_combo.set_active_id(s.get("bpp",        "32"))

    def _collect_settings(self):
        return {
            "lang":      self.lang,
            "clipboard": self.chk_clipboard.get_active(),
            "audio":     self.chk_audio.get_active(),
            "drives":    self.chk_drives.get_active(),
            "nla":       self.chk_nla.get_active(),
            "cert":      self.chk_cert.get_active(),
            "domain":    self.domain_entry.get_text().strip(),
            "bpp":       self.bpp_combo.get_active_id() or "32",
        }

    def _on_option_changed(self, _widget):
        self.settings = self._collect_settings()
        save_json(SETTINGS_FILE, self.settings)

    # ── Language ───────────────────────────────────────────────────────────────
    def _on_lang_changed(self, combo):
        new_lang = combo.get_active_id()
        if new_lang and new_lang != self.lang:
            self.lang = new_lang
            self._apply_translations()
            self.settings = self._collect_settings()
            save_json(SETTINGS_FILE, self.settings)

    def _apply_translations(self):
        self._banner_t1.set_label(self._("banner_title"))
        self._banner_t2.set_label(self._("banner_subtitle"))
        self._tab_lbl1.set_label(self._("tab_general"))
        self._tab_lbl2.set_label(self._("tab_saved"))
        self._lbl_computer.set_label(self._("label_computer"))
        self._lbl_user.set_label(self._("label_user"))
        self._lbl_pass.set_label(self._("label_password"))
        self._hint_lbl.set_label(self._("hint"))
        self.save_check.set_label(self._("save_check"))
        self._alias_lbl.set_label(self._("alias_label"))
        self.host_entry.set_placeholder_text(self._("host_placeholder"))
        self.user_entry.set_placeholder_text(self._("user_placeholder"))
        self.pass_entry.set_placeholder_text(self._("pass_placeholder"))
        self.alias_entry.set_placeholder_text(self._("alias_placeholder"))
        self._sec_options_lbl.set_label(self._("section_options"))
        self._sec_lang_lbl.set_label(self._("section_language"))
        self.chk_clipboard.set_label(self._("chk_clipboard"))
        self.chk_audio.set_label(self._("chk_audio"))
        self.chk_drives.set_label(self._("chk_drives"))
        self.chk_nla.set_label(self._("chk_nla"))
        self.chk_cert.set_label(self._("chk_cert"))
        self._lbl_domain.set_label(self._("label_domain"))
        self._lbl_bpp.set_label(self._("label_colordepth"))
        is_open = self.options_btn.get_active()
        self._opt_text_lbl.set_label(
            self._("options_hide") if is_open else self._("options_show")
        )
        self.help_btn.set_label(self._("btn_help"))
        self.connect_btn.set_label(self._("btn_connect"))
        self.clr_btn.set_label(self._("btn_clear"))
        self._set_status(self._("status_ready"), "text")
        self._refresh_saved()

    # ── Event handlers ─────────────────────────────────────────────────────────
    def _on_host_changed(self, entry):
        self.connect_btn.set_sensitive(bool(entry.get_text().strip()))

    def _on_save_check_toggled(self, chk):
        self.alias_revealer.set_reveal_child(chk.get_active())

    def _on_enter_key(self, _widget):
        if self.connect_btn.get_sensitive():
            self._on_connect(None)

    def _on_options_toggle(self, btn):
        active = btn.get_active()
        self.adv_revealer.set_reveal_child(active)
        self.arrow_lbl.set_text("^" if active else "v")
        self._opt_text_lbl.set_label(
            self._("options_hide") if active else self._("options_show")
        )

    def _on_help(self, _btn):
        dlg = Gtk.MessageDialog(
            transient_for=self, flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text=self._("help_title"),
        )
        dlg.format_secondary_text(self._("help_body"))
        dlg.run()
        dlg.destroy()

    def _on_connect(self, _btn):
        raw  = self.host_entry.get_text().strip()
        user = self.user_entry.get_text().strip()
        pwd  = self.pass_entry.get_text()
        dom  = self.domain_entry.get_text().strip()

        if not raw:
            self._set_status(self._("status_host_empty"), "error")
            return

        host, port = (raw.rsplit(":", 1) if ":" in raw else (raw, "3389"))
        cmd = self._build_cmd(host, port, user, pwd, dom)

        if self.save_check.get_active():
            self._save(host, port, user, pwd, dom,
                       self.alias_entry.get_text().strip())

        self._set_status(self._("status_connecting", label=f"{host}:{port}"), "connecting")
        self.connect_btn.set_sensitive(False)
        threading.Thread(target=self._run, args=(cmd, self._on_done), daemon=True).start()

    def _build_cmd(self, host, port, user, pwd, dom):
        bpp = self.bpp_combo.get_active_id() or "32"
        cmd = ["xfreerdp", f"/v:{host}:{port}", f"/bpp:{bpp}", "/dynamic-resolution"]
        if user: cmd.append(f"/u:{user}")
        if pwd:  cmd.append(f"/p:{pwd}")
        if dom:  cmd.append(f"/d:{dom}")
        if self.chk_clipboard.get_active(): cmd.append("+clipboard")
        if self.chk_audio.get_active():     cmd.append("/sound:sys:alsa")
        if self.chk_drives.get_active():    cmd.append(f"/drive:Home,{os.path.expanduser('~')}")
        if not self.chk_nla.get_active():   cmd.append("-nla")
        if self.chk_cert.get_active():      cmd.append("/cert:ignore")
        return cmd

    def _run(self, cmd, done_cb=None):
        import socket

        target = next((a for a in cmd if a.startswith("/v:")), None)
        if target:
            v = target[3:]
            chk_host, chk_port = (v.rsplit(":", 1) if ":" in v else (v, "3389"))
            try:
                chk_port = int(chk_port)
            except ValueError:
                chk_port = 3389
            try:
                s = socket.create_connection((chk_host, chk_port), timeout=3)
                s.close()
            except (socket.timeout, ConnectionRefusedError, OSError):
                GLib.idle_add(
                    self._set_status,
                    self._("status_timeout", host=chk_host, port=chk_port),
                    "error",
                )
                if done_cb: GLib.idle_add(done_cb)
                return

        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            _, stderr = proc.communicate()
            rc = proc.returncode
            if rc == 0:
                GLib.idle_add(self._set_status, self._("status_closed"), "ok")
            else:
                err = stderr.decode(errors="replace")[:100].strip()
                GLib.idle_add(
                    self._set_status,
                    self._("status_error", rc=rc, err=err or "unknown"),
                    "error",
                )
        except FileNotFoundError:
            GLib.idle_add(self._set_status, self._("status_notfound"), "error")
        except Exception as e:
            GLib.idle_add(self._set_status, f"Error: {e}", "error")

        if done_cb: GLib.idle_add(done_cb)

    def _on_done(self):
        self.connect_btn.set_sensitive(bool(self.host_entry.get_text().strip()))

    # ── Saved connections ──────────────────────────────────────────────────────
    def _save(self, host, port, user, pwd, dom, alias=""):
        for c in self.connections:
            if c["host"] == host and c["port"] == port:
                c.update(user=user, password=pwd, domain=dom, alias=alias)
                save_json(CONFIG_FILE, self.connections)
                self._refresh_saved()
                return
        self.connections.append(
            dict(host=host, port=port, user=user, password=pwd, domain=dom, alias=alias)
        )
        save_json(CONFIG_FILE, self.connections)
        self._refresh_saved()

    def _refresh_saved(self):
        for row in self.saved_lb.get_children():
            self.saved_lb.remove(row)

        total = len(self.connections)
        for idx, conn in enumerate(self.connections):
            row_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
            row_box.get_style_context().add_class("saved-row")

            order_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
            for symbol, direction, sensitive in [("^", -1, idx > 0),
                                                  ("v", +1, idx < total - 1)]:
                btn = Gtk.Button(label=symbol)
                btn.get_style_context().add_class("btn-order")
                btn.set_sensitive(sensitive)
                btn.connect("clicked", self._on_move, idx, direction)
                order_box.pack_start(btn, False, False, 0)

            info = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            alias = conn.get("alias", "").strip()
            display = alias if alias else f"{conn['host']}:{conn.get('port', 3389)}"
            h = Gtk.Label(label=display)
            h.get_style_context().add_class("saved-host")
            h.set_xalign(0)

            if alias:
                sub = f"{conn['host']}:{conn.get('port', 3389)}"
            else:
                sub = conn.get("user") or self._("user_missing")
                if conn.get("domain"):
                    sub = f"{conn['domain']}\\{sub}"
            if conn.get("password"):
                sub += "  ***"
            ul = Gtk.Label(label=sub)
            ul.get_style_context().add_class("saved-user")
            ul.set_xalign(0)
            info.pack_start(h,  False, False, 0)
            info.pack_start(ul, False, False, 0)

            spacer = Gtk.Box()
            spacer.set_hexpand(True)

            conn_btn = Gtk.Button(label=self._("btn_load"))
            conn_btn.get_style_context().add_class("btn-load")
            conn_btn.connect("clicked", self._on_connect_saved, conn)

            del_btn = Gtk.Button(label="x")
            del_btn.get_style_context().add_class("btn-del")
            del_btn.connect("clicked", self._on_del, idx)

            row_box.pack_start(order_box, False, False, 0)
            row_box.pack_start(info,      True,  True,  0)
            row_box.pack_start(spacer,    False, False, 0)
            row_box.pack_start(conn_btn,  False, False, 0)
            row_box.pack_start(del_btn,   False, False, 0)

            row = Gtk.ListBoxRow()
            row.add(row_box)
            self.saved_lb.add(row)

        self.saved_lb.show_all()
        cnt = len(self.connections)
        self.count_lbl.set_text(self._("count_label", n=cnt) if cnt else "")

    def _on_move(self, _btn, idx, direction):
        new_idx = idx + direction
        if 0 <= new_idx < len(self.connections):
            self.connections[idx], self.connections[new_idx] = \
                self.connections[new_idx], self.connections[idx]
            save_json(CONFIG_FILE, self.connections)
            self._refresh_saved()

    def _on_connect_saved(self, btn, conn):
        host  = conn.get("host", "")
        port  = conn.get("port", "3389")
        alias = conn.get("alias", "").strip()
        if not host:
            self._set_status(self._("status_host_empty"), "error")
            return
        label = alias if alias else f"{host}:{port}"
        btn.set_sensitive(False)
        cmd = self._build_cmd(host, port, conn.get("user", ""),
                              conn.get("password", ""), conn.get("domain", ""))
        self._set_status(self._("status_connecting", label=label), "connecting")
        threading.Thread(
            target=self._run, args=(cmd, lambda: btn.set_sensitive(True)), daemon=True
        ).start()

    def _on_del(self, _btn, idx):
        if 0 <= idx < len(self.connections):
            del self.connections[idx]
            save_json(CONFIG_FILE, self.connections)
            self._refresh_saved()

    def _on_clear_all(self, _btn):
        dlg = Gtk.MessageDialog(
            transient_for=self, flags=0,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text=self._("confirm_clear"),
        )
        r = dlg.run()
        dlg.destroy()
        if r == Gtk.ResponseType.YES:
            self.connections.clear()
            save_json(CONFIG_FILE, self.connections)
            self._refresh_saved()

    def _set_status(self, msg, state="ok"):
        self.status_lbl.set_text(msg)
        ctx = self.status_lbl.get_style_context()
        for cls in ["status-text", "status-ok", "status-error", "status-connecting"]:
            ctx.remove_class(cls)
        ctx.add_class(f"status-{state}")


def main():
    win = netRDPWindow()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()


if __name__ == "__main__":
    main()