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

CONFIG_DIR  = os.path.expanduser("~/.config/netrdp")
CONFIG_FILE = os.path.join(CONFIG_DIR, "connections.json")

# ── Çeviriler ──────────────────────────────────────────────────────────────────
TRANSLATIONS = {
    "en": {
        "tab_general":        "General",
        "tab_saved":          "Saved",
        "label_computer":     "Computer:",
        "label_user":         "User name:",
        "label_password":     "Password:",
        "label_domain":       "Domain:",
        "label_colordepth":   "Color depth:",
        "hint":               "You will be prompted for credentials when you connect.",
        "save_check":         "Save this connection",
        "alias_placeholder":  "Enter a name (leave blank to show IP)",
        "alias_label":        "Alias:",
        "host_placeholder":   "Example: 192.168.1.100:3389",
        "user_placeholder":   "Username (optional)",
        "pass_placeholder":   "Password (optional)",
        "options_show":       "Show Options",
        "options_hide":       "Hide Options",
        "section_options":    "CONNECTION OPTIONS",
        "section_language":   "LANGUAGE",
        "chk_clipboard":      "Clipboard sharing",
        "chk_audio":          "Audio redirection",
        "chk_drives":         "Drive redirection",
        "chk_nla":            "NLA authentication",
        "chk_cert":           "Ignore TLS certificate warning",
        "btn_connect":        "Connect",
        "btn_help":           "Help",
        "btn_clear":          "Clear all saved",
        "btn_load":           "Connect",
        "status_ready":       "Ready",
        "status_connecting":  "Connecting: {label} ...",
        "status_closed":      "Connection closed.",
        "status_timeout":     "Timeout: Could not reach {host}:{port} within 3s.",
        "status_error":       "Error ({rc}): {err}",
        "status_notfound":    "xfreerdp not found! sudo apt install freerdp2-x11",
        "status_host_empty":  "Error: Host address is empty!",
        "help_title":         "netRDP - xfreerdp Based RDP Client",
        "help_body":          (
            "Usage:\n"
            "1. Enter the IP or hostname in the Computer field.\n"
            "2. Use format 192.168.1.10:3389 for a custom port.\n"
            "3. Click Connect.\n\n"
            "Dependency: freerdp2-x11 or freerdp3-x11\n"
            "Saved connections are stored in ~/.config/netrdp/connections.json"
        ),
        "confirm_clear":      "Delete all saved connections?",
        "user_missing":       "No user specified",
        "banner_title":       "Remote Desktop",
        "banner_subtitle":    "Connection",
        "count_label":        "{n} saved",
    },
    "tr": {
        "tab_general":        "Genel",
        "tab_saved":          "Kayıtlı",
        "label_computer":     "Bilgisayar:",
        "label_user":         "Kullanıcı adı:",
        "label_password":     "Şifre:",
        "label_domain":       "Etki Alanı:",
        "label_colordepth":   "Renk derinliği:",
        "hint":               "Bağlandığınızda kimlik bilgileriniz istenecek.",
        "save_check":         "Bu bağlantıyı kaydet",
        "alias_placeholder":  "İsim girin (boş bırakılırsa IP gösterilir)",
        "alias_label":        "Alias:",
        "host_placeholder":   "Örnek: 192.168.1.100:3389",
        "user_placeholder":   "Kullanıcı adı (boş bırakılabilir)",
        "pass_placeholder":   "Şifre (boş bırakılabilir)",
        "options_show":       "Seçenekleri Göster",
        "options_hide":       "Seçenekleri Gizle",
        "section_options":    "BAĞLANTI SEÇENEKLERİ",
        "section_language":   "DİL",
        "chk_clipboard":      "Pano paylaşımı",
        "chk_audio":          "Ses yönlendirme",
        "chk_drives":         "Sürücü yönlendirme",
        "chk_nla":            "NLA kimlik doğrulaması",
        "chk_cert":           "TLS sertifika uyarısını yok say",
        "btn_connect":        "Bağlan",
        "btn_help":           "Yardım",
        "btn_clear":          "Tüm kayıtları temizle",
        "btn_load":           "Bağlan",
        "status_ready":       "Hazır",
        "status_connecting":  "Bağlanıyor: {label} ...",
        "status_closed":      "Bağlantı kapatıldı.",
        "status_timeout":     "Zaman aşımı: {host}:{port} adresine 3sn içinde ulaşılamadı.",
        "status_error":       "Hata ({rc}): {err}",
        "status_notfound":    "xfreerdp bulunamadı! sudo apt install freerdp2-x11",
        "status_host_empty":  "Hata: Host adresi boş!",
        "help_title":         "netRDP - xfreerdp Tabanlı RDP İstemcisi",
        "help_body":          (
            "Kullanım:\n"
            "1. Computer alanına IP veya hostname girin.\n"
            "2. Port için 192.168.1.10:3389 formatı kullanın.\n"
            "3. Bağlan butonuna tıklayın.\n\n"
            "Bağımlılık: freerdp2-x11 veya freerdp3-x11\n"
            "Kayıtlı bağlantılar ~/.config/netrdp/connections.json dosyasına kaydedilir."
        ),
        "confirm_clear":      "Tüm kayıtlı bağlantılar silinsin mi?",
        "user_missing":       "Kullanıcı belirtilmemiş",
        "banner_title":       "Remote Desktop",
        "banner_subtitle":    "Bağlantı",
        "count_label":        "{n} kayıt",
    },
    "de": {
        "tab_general":        "Allgemein",
        "tab_saved":          "Gespeichert",
        "label_computer":     "Computer:",
        "label_user":         "Benutzername:",
        "label_password":     "Passwort:",
        "label_domain":       "Domäne:",
        "label_colordepth":   "Farbtiefe:",
        "hint":               "Sie werden beim Verbinden nach Anmeldedaten gefragt.",
        "save_check":         "Diese Verbindung speichern",
        "alias_placeholder":  "Name eingeben (leer lassen für IP-Anzeige)",
        "alias_label":        "Alias:",
        "host_placeholder":   "Beispiel: 192.168.1.100:3389",
        "user_placeholder":   "Benutzername (optional)",
        "pass_placeholder":   "Passwort (optional)",
        "options_show":       "Optionen anzeigen",
        "options_hide":       "Optionen verbergen",
        "section_options":    "VERBINDUNGSOPTIONEN",
        "section_language":   "SPRACHE",
        "chk_clipboard":      "Zwischenablage teilen",
        "chk_audio":          "Audio-Weiterleitung",
        "chk_drives":         "Laufwerks-Weiterleitung",
        "chk_nla":            "NLA-Authentifizierung",
        "chk_cert":           "TLS-Zertifikatswarnung ignorieren",
        "btn_connect":        "Verbinden",
        "btn_help":           "Hilfe",
        "btn_clear":          "Alle gespeicherten löschen",
        "btn_load":           "Verbinden",
        "status_ready":       "Bereit",
        "status_connecting":  "Verbinde: {label} ...",
        "status_closed":      "Verbindung getrennt.",
        "status_timeout":     "Timeout: {host}:{port} in 3s nicht erreichbar.",
        "status_error":       "Fehler ({rc}): {err}",
        "status_notfound":    "xfreerdp nicht gefunden! sudo apt install freerdp2-x11",
        "status_host_empty":  "Fehler: Host-Adresse ist leer!",
        "help_title":         "netRDP - xfreerdp-basierter RDP-Client",
        "help_body":          (
            "Verwendung:\n"
            "1. IP oder Hostname im Feld 'Computer' eingeben.\n"
            "2. Format 192.168.1.10:3389 für benutzerdefinierten Port verwenden.\n"
            "3. Auf 'Verbinden' klicken.\n\n"
            "Abhängigkeit: freerdp2-x11 oder freerdp3-x11\n"
            "Gespeicherte Verbindungen werden in ~/.config/netrdp/connections.json gespeichert."
        ),
        "confirm_clear":      "Alle gespeicherten Verbindungen löschen?",
        "user_missing":       "Kein Benutzer angegeben",
        "banner_title":       "Remote Desktop",
        "banner_subtitle":    "Verbindung",
        "count_label":        "{n} gespeichert",
    },
}

DARK_CSS = """
* {
    font-family: "Segoe UI", "Ubuntu", Sans;
}

window {
    background-color: #1f1f1f;
}

/* Baslik bandi */
.banner {
    background-color: #2b2b2b;
    padding: 18px 20px 16px 20px;
    border-width: 0 0 1px 0;
    border-style: solid;
    border-color: #3a3a3a;
}

.banner-title {
    color: #8ab4d4;
    font-size: 15px;
    font-weight: normal;
}

.banner-subtitle {
    color: #5d9ec8;
    font-size: 20px;
    font-weight: bold;
}

/* Form alani */
.form-area {
    background-color: #1f1f1f;
    padding: 22px 28px 18px 28px;
}

.field-label {
    color: #b0b0b0;
    font-size: 13px;
}

.hint-label {
    color: #606060;
    font-size: 12px;
}

entry {
    background-color: #2d2d2d;
    color: #e8e8e8;
    border-width: 1px;
    border-style: solid;
    border-color: #4a4a4a;
    border-radius: 3px;
    padding: 6px 10px;
    font-size: 13px;
}

entry:focus {
    border-color: #0078d4;
    background-color: #303040;
}

/* Gelismis panel */
.options-area {
    background-color: #181818;
    padding: 16px 28px 18px 28px;
    border-width: 1px 0 0 0;
    border-style: solid;
    border-color: #2a2a2a;
}

.section-label {
    color: #707070;
    font-size: 11px;
    font-weight: bold;
}

checkbutton {
    color: #b0b0b0;
    background-color: transparent;
    font-size: 12px;
}

checkbutton check {
    background-color: #2d2d2d;
    border-width: 1px;
    border-style: solid;
    border-color: #4a4a4a;
    border-radius: 2px;
    min-width: 14px;
    min-height: 14px;
}

checkbutton:checked check {
    background-color: #0078d4;
    border-color: #0078d4;
}

checkbutton label {
    color: #b0b0b0;
}

checkbutton:hover label {
    color: #e0e0e0;
}

/* Alt buton cubugu */
.button-bar {
    background-color: #252525;
    padding: 12px 20px;
    border-width: 1px 0 0 0;
    border-style: solid;
    border-color: #333333;
}

/* Baglan butonu - mavi */
.btn-connect {
    background-color: #0078d4;
    color: #ffffff;
    border-width: 1px;
    border-style: solid;
    border-color: #006cc0;
    border-radius: 3px;
    padding: 7px 22px;
    font-size: 13px;
    min-width: 90px;
}

.btn-connect:hover {
    background-color: #1a8ee0;
    border-color: #0078d4;
}

.btn-connect:active {
    background-color: #005fa3;
}

.btn-connect:disabled {
    background-color: #1a3a50;
    color: #405060;
    border-color: #1a3a50;
}

/* Iptal butonu */
.btn-cancel {
    background-color: #2d2d2d;
    color: #c8c8c8;
    border-width: 1px;
    border-style: solid;
    border-color: #4a4a4a;
    border-radius: 3px;
    padding: 7px 22px;
    font-size: 13px;
    min-width: 90px;
}

.btn-cancel:hover {
    background-color: #363636;
    color: #ffffff;
    border-color: #606060;
}

.btn-cancel:active {
    background-color: #222222;
}

/* Secenekler toggle */
.btn-options {
    background-color: transparent;
    color: #707070;
    border-width: 0;
    border-radius: 2px;
    padding: 5px 8px;
    font-size: 12px;
}

.btn-options:hover {
    background-color: #2a2a2a;
    color: #a0a0a0;
}

.btn-options:checked {
    color: #8ab4d4;
}

/* Kayitli baglanti listesi */
.saved-row {
    background-color: #252525;
    padding: 10px 16px;
    border-width: 0 0 1px 0;
    border-style: solid;
    border-color: #2e2e2e;
}

row:hover .saved-row {
    background-color: #2e3a48;
}

row:selected {
    background-color: #1a3a55;
}

.saved-host {
    color: #d0d0d0;
    font-size: 13px;
    font-weight: bold;
}

.saved-user {
    color: #606060;
    font-size: 11px;
}

.btn-load {
    background-color: transparent;
    color: #5090b8;
    border-width: 1px;
    border-style: solid;
    border-color: #304860;
    border-radius: 3px;
    padding: 4px 12px;
    font-size: 11px;
}

.btn-load:hover {
    background-color: #1a3a55;
    color: #8ab4d4;
    border-color: #4a7090;
}

.btn-del {
    background-color: transparent;
    color: #503030;
    border-width: 0;
    border-radius: 3px;
    padding: 4px 8px;
    font-size: 13px;
}

.btn-del:hover {
    background-color: #3a1515;
    color: #cc4444;
}

.btn-order {
    background-color: transparent;
    color: #404040;
    border-width: 0;
    border-radius: 2px;
    padding: 1px 5px;
    font-size: 9px;
    min-width: 18px;
    min-height: 14px;
}

.btn-order:hover {
    background-color: #2a3a4a;
    color: #8ab4d4;
}

.btn-order:disabled {
    color: #2a2a2a;
}

/* Durum cubugu */
.statusbar {
    background-color: #161616;
    padding: 5px 20px;
    border-width: 1px 0 0 0;
    border-style: solid;
    border-color: #2a2a2a;
}

.status-text {
    color: #505050;
    font-size: 11px;
}

.status-ok {
    color: #0078d4;
    font-size: 11px;
}

.status-error {
    color: #c0392b;
    font-size: 11px;
}

.status-connecting {
    color: #e67e22;
    font-size: 11px;
}

.count-label {
    color: #404040;
    font-size: 11px;
}

/* Notebook sekmeleri */
notebook {
    background-color: #1f1f1f;
}

notebook header {
    background-color: #1f1f1f;
    border-width: 0 0 1px 0;
    border-style: solid;
    border-color: #333333;
    padding: 0 8px;
}

notebook tab {
    background-color: #1f1f1f;
    color: #707070;
    padding: 9px 18px;
    border-width: 0;
    font-size: 12px;
}

notebook tab:checked {
    background-color: #1f1f1f;
    color: #8ab4d4;
    border-width: 0 0 2px 0;
    border-style: solid;
    border-color: #0078d4;
}

notebook tab:hover {
    background-color: #282828;
    color: #a0a0a0;
}

scrolledwindow {
    background-color: #1f1f1f;
    border-width: 0;
}

combobox button {
    background-color: #2d2d2d;
    color: #e8e8e8;
    border-width: 1px;
    border-style: solid;
    border-color: #4a4a4a;
    border-radius: 3px;
    padding: 6px 10px;
    font-size: 12px;
}

combobox button:hover {
    border-color: #0078d4;
    background-color: #303040;
}
"""


def load_config():
    if not os.path.exists(CONFIG_FILE):
        return []
    try:
        with open(CONFIG_FILE) as f:
            return json.load(f)
    except Exception:
        return []


def save_config(connections):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(connections, f, indent=2)


class netRDPWindow(Gtk.Window):

    def __init__(self):
        super().__init__(title="netRDP Client")
        self.set_default_size(460, -1)
        self.set_resizable(False)
        self.set_border_width(0)
        self.set_position(Gtk.WindowPosition.CENTER)

        css = Gtk.CssProvider()
        css.load_from_data(DARK_CSS.encode())
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            css,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        self.lang = "en"
        self.connections = load_config()
        self._build_ui()
        self._refresh_saved()

    def _(self, key, **kwargs):
        text = TRANSLATIONS[self.lang].get(key, TRANSLATIONS["en"].get(key, key))
        return text.format(**kwargs) if kwargs else text

    def _build_ui(self):
        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(root)

        self._banner_box = self._banner()
        root.pack_start(self._banner_box, False, False, 0)

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

        icon = Gtk.Label(label="")
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

        form = Gtk.Grid()
        form.get_style_context().add_class("form-area")
        form.set_row_spacing(8)
        form.set_column_spacing(12)

        self._lbl_computer = Gtk.Label(label=self._("label_computer"))
        self._lbl_computer.get_style_context().add_class("field-label")
        self._lbl_computer.set_xalign(1)

        self.host_entry = Gtk.Entry()
        self.host_entry.set_placeholder_text(self._("host_placeholder"))
        self.host_entry.set_hexpand(True)
        self.host_entry.connect("changed", self._on_host_changed)
        self.host_entry.connect("activate", self._on_enter_key)

        form.attach(self._lbl_computer,  0, 0, 1, 1)
        form.attach(self.host_entry,     1, 0, 1, 1)

        self._lbl_user = Gtk.Label(label=self._("label_user"))
        self._lbl_user.get_style_context().add_class("field-label")
        self._lbl_user.set_xalign(1)

        self.user_entry = Gtk.Entry()
        self.user_entry.set_placeholder_text(self._("user_placeholder"))
        self.user_entry.set_hexpand(True)

        form.attach(self._lbl_user,      0, 1, 1, 1)
        form.attach(self.user_entry,     1, 1, 1, 1)

        self._lbl_pass = Gtk.Label(label=self._("label_password"))
        self._lbl_pass.get_style_context().add_class("field-label")
        self._lbl_pass.set_xalign(1)

        self.pass_entry = Gtk.Entry()
        self.pass_entry.set_visibility(False)
        self.pass_entry.set_placeholder_text(self._("pass_placeholder"))
        self.pass_entry.set_input_purpose(Gtk.InputPurpose.PASSWORD)
        self.pass_entry.set_hexpand(True)
        self.pass_entry.connect("activate", self._on_enter_key)

        form.attach(self._lbl_pass,      0, 2, 1, 1)
        form.attach(self.pass_entry,     1, 2, 1, 1)

        self._hint_lbl = Gtk.Label(label=self._("hint"))
        self._hint_lbl.get_style_context().add_class("hint-label")
        self._hint_lbl.set_xalign(0)
        self._hint_lbl.set_margin_top(4)
        form.attach(self._hint_lbl,      0, 3, 2, 1)

        self.save_check = Gtk.CheckButton(label=self._("save_check"))
        self.save_check.set_margin_top(6)
        self.save_check.connect("toggled", self._on_save_check_toggled)
        form.attach(self.save_check,     0, 4, 2, 1)

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
        self.chk_nla = Gtk.CheckButton(label=self._("chk_nla"))
        self.chk_nla.set_active(True)
        self.chk_cert = Gtk.CheckButton(label=self._("chk_cert"))

        for c in [self.chk_clipboard, self.chk_audio,
                  self.chk_drives, self.chk_nla, self.chk_cert]:
            adv.pack_start(c, False, False, 0)

        dom_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self._lbl_domain = Gtk.Label(label=self._("label_domain"))
        self._lbl_domain.get_style_context().add_class("field-label")
        self._lbl_domain.set_xalign(1)
        self._lbl_domain.set_width_chars(13)

        self.domain_entry = Gtk.Entry()
        self.domain_entry.set_placeholder_text("WORKGROUP")
        self.domain_entry.set_hexpand(True)

        dom_row.pack_start(self._lbl_domain,   False, False, 0)
        dom_row.pack_start(self.domain_entry,  True,  True,  0)
        adv.pack_start(dom_row, False, False, 0)

        bpp_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self._lbl_bpp = Gtk.Label(label=self._("label_colordepth"))
        self._lbl_bpp.get_style_context().add_class("field-label")
        self._lbl_bpp.set_xalign(1)
        self._lbl_bpp.set_width_chars(13)

        self.bpp_combo = Gtk.ComboBoxText()
        for lbl_txt, val in [("32-bit", "32"), ("24-bit", "24"), ("16-bit", "16")]:
            self.bpp_combo.append(val, lbl_txt)
        self.bpp_combo.set_active(0)
        self.bpp_combo.set_hexpand(True)

        bpp_row.pack_start(self._lbl_bpp,    False, False, 0)
        bpp_row.pack_start(self.bpp_combo,   True,  True,  0)
        adv.pack_start(bpp_row, False, False, 0)

        sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        sep.set_margin_top(4)
        sep.set_margin_bottom(2)
        adv.pack_start(sep, False, False, 0)

        self._sec_lang_lbl = Gtk.Label(label=self._("section_language"))
        self._sec_lang_lbl.get_style_context().add_class("section-label")
        self._sec_lang_lbl.set_xalign(0)
        adv.pack_start(self._sec_lang_lbl, False, False, 0)

        lang_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        lang_icon = Gtk.Label(label="🌐")
        lang_icon.set_margin_end(2)

        self.lang_combo = Gtk.ComboBoxText()
        self.lang_combo.append("en", "English")
        self.lang_combo.append("tr", "Türkçe")
        self.lang_combo.append("de", "Deutsch")
        self.lang_combo.set_active_id(self.lang)
        self.lang_combo.set_size_request(150, -1)
        self.lang_combo.connect("changed", self._on_lang_changed)

        lang_row.pack_start(lang_icon,       False, False, 0)
        lang_row.pack_start(self.lang_combo, False, False, 0)
        adv.pack_start(lang_row, False, False, 0)

        self.adv_revealer.add(adv)
        page.pack_start(self.adv_revealer, False, False, 0)

        bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        bar.get_style_context().add_class("button-bar")

        self.options_btn = Gtk.ToggleButton()
        self.options_btn.get_style_context().add_class("btn-options")
        self.options_btn.connect("toggled", self._on_options_toggle)

        opt_inner = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        self.arrow_lbl = Gtk.Label(label="v")
        self._opt_text_lbl = Gtk.Label(label=self._("options_show"))
        opt_inner.pack_start(self.arrow_lbl,       False, False, 0)
        opt_inner.pack_start(self._opt_text_lbl,   False, False, 0)
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

        bar.pack_start(self.options_btn,  False, False, 0)
        bar.pack_start(spacer,            True,  True,  0)
        bar.pack_start(self.help_btn,     False, False, 0)
        bar.pack_start(self.connect_btn,  False, False, 0)

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

    def _on_lang_changed(self, combo):
        new_lang = combo.get_active_id()
        if new_lang and new_lang != self.lang:
            self.lang = new_lang
            self._apply_translations()

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

    def _on_host_changed(self, entry):
        self.connect_btn.set_sensitive(bool(entry.get_text().strip()))

    def _on_save_check_toggled(self, chk):
        self.alias_revealer.set_reveal_child(chk.get_active())

    def _on_enter_key(self, widget):
        if self.connect_btn.get_sensitive():
            self._on_connect(None)

    def _on_options_toggle(self, btn):
        active = btn.get_active()
        self.adv_revealer.set_reveal_child(active)
        self.arrow_lbl.set_text("^" if active else "v")
        self._opt_text_lbl.set_label(
            self._("options_hide") if active else self._("options_show")
        )

    def _on_help(self, btn):
        dlg = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text=self._("help_title")
        )
        dlg.format_secondary_text(self._("help_body"))
        dlg.run()
        dlg.destroy()

    def _on_connect(self, btn):
        raw  = self.host_entry.get_text().strip()
        user = self.user_entry.get_text().strip()
        pwd  = self.pass_entry.get_text()
        dom  = self.domain_entry.get_text().strip()

        if not raw:
            self._set_status(self._("status_host_empty"), "error")
            return

        if ":" in raw:
            parts = raw.rsplit(":", 1)
            host, port = parts[0], parts[1]
        else:
            host, port = raw, "3389"

        cmd = self._build_cmd(host, port, user, pwd, dom)

        if self.save_check.get_active():
            alias = self.alias_entry.get_text().strip()
            self._save(host, port, user, pwd, dom, alias)

        label = f"{host}:{port}"
        self._set_status(self._("status_connecting", label=label), "connecting")
        self.connect_btn.set_sensitive(False)
        threading.Thread(target=self._run, args=(cmd, self._on_done), daemon=True).start()

    def _build_cmd(self, host, port, user, pwd, dom):
        bpp = self.bpp_combo.get_active_id() or "32"

        cmd = [
            "xfreerdp",
            f"/v:{host}:{port}",
            f"/bpp:{bpp}",
            "/dynamic-resolution",
        ]

        if user:
            cmd.append(f"/u:{user}")
        if pwd:
            cmd.append(f"/p:{pwd}")
        if dom:
            cmd.append(f"/d:{dom}")

        if self.chk_clipboard.get_active():
            cmd.append("+clipboard")
        if self.chk_audio.get_active():
            cmd.append("/sound:sys:alsa")
        if self.chk_drives.get_active():
            home = os.path.expanduser("~")
            cmd.append(f"/drive:Home,{home}")
        if not self.chk_nla.get_active():
            cmd.append("-nla")
        if self.chk_cert.get_active():
            cmd.append("/cert:ignore")

        return cmd

    def _run(self, cmd, done_cb=None):
        import socket

        target = next((a for a in cmd if a.startswith("/v:")), None)
        if target:
            v = target[3:]
            if ":" in v:
                chk_host, chk_port = v.rsplit(":", 1)
                try:
                    chk_port = int(chk_port)
                except ValueError:
                    chk_port = 3389
            else:
                chk_host, chk_port = v, 3389

            try:
                sock = socket.create_connection((chk_host, chk_port), timeout=3)
                sock.close()
            except (socket.timeout, ConnectionRefusedError, OSError):
                GLib.idle_add(
                    self._set_status,
                    self._("status_timeout", host=chk_host, port=chk_port),
                    "error"
                )
                if done_cb:
                    GLib.idle_add(done_cb)
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
                    "error"
                )
        except FileNotFoundError:
            GLib.idle_add(self._set_status, self._("status_notfound"), "error")
        except Exception as e:
            GLib.idle_add(self._set_status, f"Error: {e}", "error")

        if done_cb:
            GLib.idle_add(done_cb)

    def _on_done(self):
        self.connect_btn.set_sensitive(bool(self.host_entry.get_text().strip()))

    def _save(self, host, port, user, pwd, dom, alias=""):
        for c in self.connections:
            if c["host"] == host and c["port"] == port:
                c["user"] = user
                c["password"] = pwd
                c["domain"] = dom
                c["alias"] = alias
                save_config(self.connections)
                self._refresh_saved()
                return
        self.connections.append({
            "host": host, "port": port,
            "user": user, "password": pwd,
            "domain": dom, "alias": alias
        })
        save_config(self.connections)
        self._refresh_saved()

    def _refresh_saved(self):
        for c in self.saved_lb.get_children():
            self.saved_lb.remove(c)

        total = len(self.connections)
        for idx, conn in enumerate(self.connections):
            row_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
            row_box.get_style_context().add_class("saved-row")

            order_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
            up_btn = Gtk.Button(label="^")
            up_btn.get_style_context().add_class("btn-order")
            up_btn.set_sensitive(idx > 0)
            up_btn.connect("clicked", self._on_move, idx, -1)

            dn_btn = Gtk.Button(label="v")
            dn_btn.get_style_context().add_class("btn-order")
            dn_btn.set_sensitive(idx < total - 1)
            dn_btn.connect("clicked", self._on_move, idx, +1)

            order_box.pack_start(up_btn, False, False, 0)
            order_box.pack_start(dn_btn, False, False, 0)

            info = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)

            alias = conn.get("alias", "").strip()
            display_name = alias if alias else f"{conn['host']}:{conn.get('port', 3389)}"
            h = Gtk.Label(label=display_name)
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

            sp = Gtk.Box()
            sp.set_hexpand(True)

            conn_btn = Gtk.Button(label=self._("btn_load"))
            conn_btn.get_style_context().add_class("btn-load")
            conn_btn.connect("clicked", self._on_connect_saved, conn)

            db = Gtk.Button(label="x")
            db.get_style_context().add_class("btn-del")
            db.connect("clicked", self._on_del, idx)

            row_box.pack_start(order_box, False, False, 0)
            row_box.pack_start(info,      True,  True,  0)
            row_box.pack_start(sp,        False, False, 0)
            row_box.pack_start(conn_btn,  False, False, 0)
            row_box.pack_start(db,        False, False, 0)

            row = Gtk.ListBoxRow()
            row.add(row_box)
            self.saved_lb.add(row)

        self.saved_lb.show_all()
        cnt = len(self.connections)
        self.count_lbl.set_text(self._("count_label", n=cnt) if cnt else "")

    def _on_move(self, btn, idx, direction):
        new_idx = idx + direction
        if 0 <= new_idx < len(self.connections):
            self.connections[idx], self.connections[new_idx] = \
                self.connections[new_idx], self.connections[idx]
            save_config(self.connections)
            self._refresh_saved()

    def _on_connect_saved(self, btn, conn):
        host  = conn.get("host", "")
        port  = conn.get("port", "3389")
        user  = conn.get("user", "")
        pwd   = conn.get("password", "")
        dom   = conn.get("domain", "")
        alias = conn.get("alias", "").strip()
        label = alias if alias else f"{host}:{port}"

        if not host:
            self._set_status(self._("status_host_empty"), "error")
            return

        btn.set_sensitive(False)
        cmd = self._build_cmd(host, port, user, pwd, dom)
        self._set_status(self._("status_connecting", label=label), "connecting")

        def done():
            btn.set_sensitive(True)

        threading.Thread(target=self._run, args=(cmd, done), daemon=True).start()

    def _on_del(self, btn, idx):
        if 0 <= idx < len(self.connections):
            del self.connections[idx]
            save_config(self.connections)
            self._refresh_saved()

    def _on_clear_all(self, btn):
        dlg = Gtk.MessageDialog(
            transient_for=self, flags=0,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text=self._("confirm_clear")
        )
        r = dlg.run()
        dlg.destroy()
        if r == Gtk.ResponseType.YES:
            self.connections.clear()
            save_config(self.connections)
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