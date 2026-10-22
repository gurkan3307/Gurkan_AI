# -*- coding: utf-8 -*-
"""GURKAN AI v3.0 — PySide6 masaustu arayuzu (ilk entegrasyon surumu).

Bu dosya mevcut v2.9.6 motorunu degistirmez, yaninda calisir.
Gorunen marka adidir; ticari kullanimdan once marka sicil kontrolu gerekir.
Vazgecilmezler: yazili modda varsayilan sessizlik; /gor-5 ASLA seslendirilmez;
RAG yerel motorla cevaplanir; Obsidian taslaklari onay gerektirir.
"""
from __future__ import annotations

import html
import importlib.util
import math
import re
import sys
import threading
from pathlib import Path
from datetime import datetime

from PySide6.QtCore import Qt, QThread, QTimer, Signal, QRectF, QPointF, QEasingCurve
from PySide6.QtGui import (
    QColor, QFont, QPainter, QPen, QBrush, QConicalGradient,
    QRadialGradient, QKeySequence, QShortcut,
)
from PySide6.QtWidgets import (
    QApplication, QWidget, QMainWindow, QLabel, QFrame, QPushButton, QLineEdit,
    QComboBox, QScrollArea, QVBoxLayout, QHBoxLayout, QGridLayout, QSplitter,
    QSizePolicy, QMessageBox, QProgressBar, QTextEdit,
)

BASE = Path(__file__).resolve().parent
BACKEND = BASE / "jarvis_v2_9_6_kaynakli_rag.py"

COLORS = {
    "background": "#07111F", "panel": "#0D1C2C", "panel2": "#10263B",
    "border": "#1B4059", "cyan": "#41D9FF", "blue": "#2A8BFF",
    "text": "#E9F5FF", "muted": "#90AABF", "mint": "#3DD9A6",
    "amber": "#FFC979", "red": "#FF7C8D",
}

_BACKEND_MODULE = None
_BACKEND_LOCK = threading.Lock()


def get_backend():
    """Motoru lazim oldugunda yukle; main() calismaz."""
    global _BACKEND_MODULE
    with _BACKEND_LOCK:
        if _BACKEND_MODULE is not None:
            return _BACKEND_MODULE
        if not BACKEND.is_file():
            raise FileNotFoundError(
                "Python çekirdeği bulunamadı. Bu dosyayi "
                "jarvis_v2_9_6_kaynakli_rag.py yanina koy."
            )
        spec = importlib.util.spec_from_file_location("jarvis_core_v296_for_gui", BACKEND)
        if spec is None or spec.loader is None:
            raise RuntimeError("Python çekirdeği açılamıyor.")
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        module.init_db()
        _BACKEND_MODULE = module
        return module


class TaskWorker(QThread):
    result = Signal(str, str)  # operation, output
    failure = Signal(str, str)

    def __init__(self, operation: str, argument: str = "", provider: str = "yerel", speak: bool = False):
        super().__init__()
        self.operation = operation
        self.argument = argument
        self.provider = provider
        self.want_speech = speak

    def run(self):
        try:
            backend = get_backend()
            op = self.operation
            if op == "status":
                text = backend.bilgi_durumu()
            elif op == "chat":
                history = backend.load_history()
                text = backend.get_reply_with_tools(self.provider, history, self.argument)
                backend.save_exchange(self.argument, text, self.provider)
            elif op == "rag":
                text = backend.rag_answer(self.argument)
                backend.save_exchange("/sor " + self.argument, text, "yerel-rag")
            elif op == "find":
                text = backend.rag_find_report(self.argument)
            elif op == "notes":
                notes = backend.list_notes()
                text = f"Toplam {len(notes)} not:\n\n" + "\n".join(x for x, _ in notes[:80])
                if len(notes) > 80:
                    text += f"\n... ve {len(notes)-80} not daha."
            elif op == "index":
                changed, removed, chunks = backend.index_notes()
                text = f"Indeksleme tamamlandi: {changed} yeni/degisen not, {removed} kaldirilan, {chunks} RAG parcasi."
            elif op == "screen":
                text = backend.analyze_other_window()
                backend.save_exchange("/gor-5", text, "yerel")
            elif op == "approve":
                text = backend.approve_obsidian_note()
            elif op == "reject":
                backend.PENDING_NOTE = None
                text = "Bekleyen Obsidian taslagi iptal edildi."
            elif op == "voice":
                # Ilk asama: tek tur dinle/yanitla. Kesintisiz dinleme sonraki surumde.
                backend.CURRENT_STT_LANG = "tr-TR"
                heard = backend.listen("tr-TR")
                if not heard:
                    text = "Ses anlasilamadi; lutfen tekrar dene."
                else:
                    history = backend.load_history()
                    answer = backend.get_reply_with_tools(self.provider, history, heard)
                    backend.save_exchange(heard, answer, self.provider)
                    text = "Sen (sesli): " + heard + "\n\nJARVIS: " + answer
                    previous_voice = backend.VOICE_CHAT_ACTIVE
                    backend.VOICE_CHAT_ACTIVE = True
                    try:
                        backend.speak(answer)
                    finally:
                        backend.VOICE_CHAT_ACTIVE = previous_voice
            else:
                raise ValueError("Bilinmeyen gorev: " + op)

            # Soru cevaplari istege bagli konusur, /gor-5 ve sistem gorevleri ASLA konusmaz.
            if self.want_speech and op in ("chat", "rag"):
                previous = backend.TEXT_SPEECH_ENABLED
                backend.TEXT_SPEECH_ENABLED = True
                try:
                    backend.speak(text)
                finally:
                    backend.TEXT_SPEECH_ENABLED = previous
            self.result.emit(op, str(text))
        except Exception as exc:
            self.failure.emit(self.operation, f"{type(exc).__name__}: {exc}")


class JARVISCore(QWidget):
    """Gercek QPainter animasyonu; resim veya video degil."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.angle = 0.0
        self.busy = False
        self.setMinimumSize(320, 335)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(33)

    def tick(self):
        self.angle = (self.angle + (1.45 if self.busy else 0.55)) % 360
        self.update()

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2 - 6
        r = min(w * 0.37, h * 0.39)

        background = QRadialGradient(QPointF(cx, cy), r * 1.65)
        background.setColorAt(0, QColor(20, 72, 116, 115))
        background.setColorAt(0.50, QColor(15, 40, 70, 60))
        background.setColorAt(1, QColor(7, 17, 31, 0))
        p.setPen(Qt.NoPen)
        p.setBrush(background)
        p.drawEllipse(QPointF(cx, cy), r * 1.65, r * 1.65)

        for scale, alpha, width in ((1.22, 47, 1), (1.05, 110, 2), (0.88, 135, 2)):
            pen = QPen(QColor(65, 217, 255, alpha), width)
            p.setPen(pen)
            p.setBrush(Qt.NoBrush)
            p.drawEllipse(QPointF(cx, cy), r * scale, r * scale)

        # Hareketli bolunmus halkalar.
        for i, (scale, thick, arcs) in enumerate(((1.16, 5, 9), (0.96, 3, 13), (0.77, 2, 16))):
            p.setPen(QPen(QColor(45, 159 + i * 12, 255, 210 - i * 37), thick, Qt.SolidLine, Qt.RoundCap))
            rr = QRectF(cx-r*scale, cy-r*scale, 2*r*scale, 2*r*scale)
            for j in range(arcs):
                a = ((self.angle * (-1 if i == 1 else 1) * (0.7 + 0.16*i)) + j*360/arcs)
                p.drawArc(rr, int(a * 16), int((360 / arcs * 0.42) * 16))

        ring = QRadialGradient(QPointF(cx-r*0.18, cy-r*0.16), r*0.80)
        ring.setColorAt(0, QColor(18, 104, 158, 235))
        ring.setColorAt(0.60, QColor(7, 44, 93, 230))
        ring.setColorAt(0.90, QColor(4, 18, 45, 240))
        ring.setColorAt(1, QColor(42, 174, 255, 230))
        p.setPen(QPen(QColor("#55D9FF"), 3))
        p.setBrush(ring)
        p.drawEllipse(QPointF(cx, cy), r*.65, r*.65)

        p.setPen(QColor("#F3FBFF"))
        f = QFont("Segoe UI", max(19, int(r*.24)), QFont.Bold)
        f.setLetterSpacing(QFont.AbsoluteSpacing, 2)
        p.setFont(f)
        p.drawText(QRectF(cx-r*.66, cy-29, r*1.32, 47), Qt.AlignCenter, "GURKAN AI")
        p.setPen(QColor("#45D8FF"))
        p.setFont(QFont("Segoe UI", 12, QFont.DemiBold))
        p.drawText(QRectF(cx-r*.5, cy+22, r, 30), Qt.AlignCenter, "v3.0")

        p.setPen(QColor("#83BFD6"))
        p.setFont(QFont("Segoe UI", 10))
        p.drawText(QRectF(0, h-23, w, 21), Qt.AlignCenter,
                   "İŞLENİYOR" if self.busy else "SİSTEM HAZIR")
        p.end()


class StatCard(QFrame):
    def __init__(self, label, value="—", subtitle="", parent=None):
        super().__init__(parent)
        self.setObjectName("statCard")
        v = QVBoxLayout(self)
        v.setContentsMargins(15, 12, 15, 12)
        v.setSpacing(5)
        self.heading = QLabel(label)
        self.heading.setObjectName("dimText")
        self.value = QLabel(value)
        self.value.setObjectName("statValue")
        self.subtitle = QLabel(subtitle)
        self.subtitle.setObjectName("dimText")
        self.subtitle.setWordWrap(True)
        v.addWidget(self.heading)
        v.addWidget(self.value)
        v.addWidget(self.subtitle)


class MessageBubble(QFrame):
    def __init__(self, name: str, message: str, mine=False):
        super().__init__()
        self.setObjectName("bubbleMine" if mine else "bubbleAssistant")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 10, 12, 12)
        lay.setSpacing(5)
        who = QLabel(("SEN" if mine else "GURKAN AI") + "  " + datetime.now().strftime("%H:%M"))
        who.setObjectName("bubbleAuthor")
        body = QLabel(message)
        body.setTextFormat(Qt.PlainText)  # Enjeksiyon/HTML yorumlama yok.
        body.setWordWrap(True)
        body.setTextInteractionFlags(Qt.TextSelectableByMouse)
        body.setObjectName("bodyText")
        lay.addWidget(who)
        lay.addWidget(body)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GURKAN AI v3.0 — Geliştirme Sürümü")
        self.setMinimumSize(1130, 745)
        self.resize(1510, 890)
        self.worker = None
        self.speech_enabled = False
        self.last_command = ""
        self.setup_ui()
        self.add_message("GURKAN AI", "Arayüz hazır. Yerel model için LM Studio sunucusunu aç. "
                         "Yazılı sohbet sessizdir; F8 ile seslendirmeyi açabilirsin.")
        QTimer.singleShot(200, lambda: self.launch("status"))

    def setup_ui(self):
        root = QWidget()
        root.setObjectName("root")
        self.setCentralWidget(root)
        outer = QHBoxLayout(root)
        outer.setContentsMargins(10, 10, 10, 10)
        outer.setSpacing(12)

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(205)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(14, 21, 14, 15)
        side.setSpacing(10)
        brand = QLabel("◉  GURKAN AI  v3.0")
        brand.setObjectName("brand")
        side.addWidget(brand)
        tagline = QLabel("KİŞİSEL YAPAY ZEKÂ")
        tagline.setObjectName("dimText")
        side.addWidget(tagline)
        side.addSpacing(26)
        for label, mode in (
            ("⌑   Sohbet", "chat"), ("◉   Sesli Mod", "voice"),
            ("▤   Bilgi Bankası", "notes"), ("▣   Ekran Analizi", "screen"),
            ("◇   Modeller", "models"), ("⚙   Ayarlar", "settings"),
        ):
            b = QPushButton(label)
            b.setObjectName("menuBtn")
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(lambda _=False, mode=mode: self.sidebar_action(mode))
            side.addWidget(b)
        side.addStretch()
        self.speech_badge = QLabel("◌  SES ÇIKIŞI KAPALI")
        self.speech_badge.setObjectName("dimText")
        side.addWidget(self.speech_badge)
        self.local_badge = QLabel("●  Yerel model: bekleniyor")
        self.local_badge.setObjectName("dimText")
        self.local_badge.setWordWrap(True)
        side.addWidget(self.local_badge)
        outer.addWidget(sidebar)

        content = QFrame()
        content.setObjectName("content")
        frame = QVBoxLayout(content)
        frame.setContentsMargins(0, 0, 0, 0)
        frame.setSpacing(12)
        header = QHBoxLayout()
        self.title = QLabel("GURKAN AI  <font color='#41D9FF'>v3.0</font>")
        self.title.setObjectName("title")
        header.addWidget(self.title)
        header.addStretch()
        self.state = QLabel("●  Hazır")
        self.state.setObjectName("readyLabel")
        header.addWidget(self.state)
        header.addSpacing(18)
        header.addWidget(QLabel("Model:"))
        self.provider = QComboBox()
        self.provider.addItem("Yerel • Qwen3-8B", "yerel")
        self.provider.addItem("Google • Gemini API", "google")
        self.provider.setFixedWidth(183)
        self.provider.currentIndexChanged.connect(self.provider_changed)
        header.addWidget(self.provider)
        frame.addLayout(header)

        split = QSplitter(Qt.Horizontal)
        split.setChildrenCollapsible(False)
        split.setHandleWidth(6)

        center = QFrame()
        center.setObjectName("centralPanel")
        cen = QVBoxLayout(center)
        cen.setContentsMargins(18, 16, 18, 16)
        cen.setSpacing(12)
        cen.addWidget(self.section_title("GURKAN AI ÇEKİRDEK SİSTEMİ", "Gerçek zamanlı animasyon"))
        self.core = JARVISCore()
        cen.addWidget(self.core, stretch=3)
        cards = QGridLayout()
        cards.setSpacing(10)
        self.card_cpu = StatCard("CPU", "—", "Sistem yükü")
        self.card_ram = StatCard("RAM", "—", "Kullanım oranı")
        self.card_vault = StatCard("OBSIDIAN", "—", "Bilgi bankası")
        self.card_audio = StatCard("SES", "Kapalı", "F8 ile değiştir")
        cards.addWidget(self.card_cpu, 0, 0)
        cards.addWidget(self.card_ram, 0, 1)
        cards.addWidget(self.card_vault, 1, 0)
        cards.addWidget(self.card_audio, 1, 1)
        cen.addLayout(cards)
        cen.addWidget(self.section_title("HIZLI KOMUTLAR", "Mevcut Python çekirdeğine bağlı"))
        commands = QGridLayout()
        commands.setSpacing(9)
        for i, (title, command) in enumerate((
            ("⌕ Ekranı Oku", "/gor-5"),
            ("▤ Notları Listele", "/notlar"),
            ("≡ Bilgi Durumu", "/bilgi-durum"),
            ("↻ İndeksle", "/indeksle"),
            ("◈ Ses Aç/Kapat", "/ses"),
            ("⌕ Kaynak Ara", "/ara "),
        )):
            b = QPushButton(title)
            b.setObjectName("quickBtn")
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(lambda _=False, command=command: self.send_command(command))
            commands.addWidget(b, i // 3, i % 3)
        cen.addLayout(commands)
        cen.addStretch(1)

        chat = QFrame()
        chat.setObjectName("chatPanel")
        chatlay = QVBoxLayout(chat)
        chatlay.setContentsMargins(15, 15, 15, 15)
        chatlay.setSpacing(10)
        chatlay.addWidget(self.section_title("SOHBET", "Yazılı yanıt • kaynaklı RAG"))
        self.scroll = QScrollArea()
        self.scroll.setObjectName("chatScroll")
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.message_host = QWidget()
        self.messages = QVBoxLayout(self.message_host)
        self.messages.setContentsMargins(4, 8, 4, 8)
        self.messages.setSpacing(12)
        self.messages.addStretch()
        self.scroll.setWidget(self.message_host)
        chatlay.addWidget(self.scroll, 1)

        bottom = QHBoxLayout()
        bottom.setSpacing(8)
        self.entry = QLineEdit()
        self.entry.setPlaceholderText("Mesaj yaz veya /sor konu ...")
        self.entry.returnPressed.connect(self.send_current)
        bottom.addWidget(self.entry, 1)
        self.btn_voice = QPushButton("🎙")
        self.btn_voice.setObjectName("smallBtn")
        self.btn_voice.setToolTip("Tek turluk Türkçe sesli sohbet")
        self.btn_voice.clicked.connect(lambda: self.launch("voice"))
        bottom.addWidget(self.btn_voice)
        self.btn_send = QPushButton("Gönder")
        self.btn_send.setObjectName("primaryBtn")
        self.btn_send.clicked.connect(self.send_current)
        bottom.addWidget(self.btn_send)
        chatlay.addLayout(bottom)
        notice = QLabel("/gor-5 sessizdir. Obsidian taslakları /onayla olmadan yazılmaz.")
        notice.setObjectName("dimText")
        notice.setWordWrap(True)
        chatlay.addWidget(notice)

        split.addWidget(center)
        split.addWidget(chat)
        split.setStretchFactor(0, 6)
        split.setStretchFactor(1, 5)
        split.setSizes([670, 460])
        frame.addWidget(split, 1)
        outer.addWidget(content, 1)

        self.key_f8 = QShortcut(QKeySequence("F8"), self)
        self.key_f8.setContext(Qt.ApplicationShortcut)
        self.key_f8.activated.connect(self.toggle_speech)

        self.monitor_timer = QTimer(self)
        self.monitor_timer.timeout.connect(self.update_system_stats)
        self.monitor_timer.start(2400)
        self.update_system_stats()

        self.setStyleSheet(STYLESHEET)

    def section_title(self, title, hint):
        label = QLabel(f"{html.escape(title)}  <span style='color:#6A93AA;font-size:11px'>" +
                       html.escape(hint) + "</span>")
        label.setObjectName("sectionHeading")
        return label

    def update_system_stats(self):
        try:
            import psutil
            self.card_cpu.value.setText(f"{psutil.cpu_percent(interval=None):.0f}%")
            self.card_ram.value.setText(f"{psutil.virtual_memory().percent:.0f}%")
        except Exception:
            self.card_cpu.value.setText("N/D")
            self.card_ram.value.setText("N/D")

    def add_message(self, person, text, mine=False):
        bubble = MessageBubble(person, text, mine)
        self.messages.insertWidget(self.messages.count()-1, bubble)
        QTimer.singleShot(10, self.scroll_to_bottom)

    def scroll_to_bottom(self):
        bar = self.scroll.verticalScrollBar()
        bar.setValue(bar.maximum())

    def toggle_speech(self):
        self.speech_enabled = not self.speech_enabled
        state = "Açık" if self.speech_enabled else "Kapalı"
        self.card_audio.value.setText(state)
        self.speech_badge.setText("●  SES ÇIKIŞI " + state.upper())
        self.state.setText("●  Yazılı mod sesi " + state.lower())
        # Bu F8 yalnızca GUI uygulaması odaktayken çalışır.

    def provider_changed(self):
        if self.provider.currentData() == "google":
            QMessageBox.information(
                self, "Bulut sağlayıcısı", "Google seçildi. Normal sohbet mesajları Google "
                "API'ye gönderilebilir ve API ücretlendirmesi geçerli olabilir. "
                "Obsidian /sor cevapları yerel Qwen modeliyle işlenir."
            )

    def sidebar_action(self, action):
        if action == "voice":
            self.launch("voice")
        elif action == "notes":
            self.send_command("/bilgi-durum")
        elif action == "screen":
            self.send_command("/gor-5")
        elif action == "models":
            self.provider.setFocus()
            self.add_message("GURKAN AI", "Model seçimi sağ üstte. Varsayılan yerel Qwen3-8B.")
        elif action == "settings":
            self.add_message("GURKAN AI", "Ayarlar: F8 ses aç/kapat. Yerel model için LM Studio "
                             "http://127.0.0.1:1234/v1 çalışmalı.")
        else:
            self.entry.setFocus()

    def send_current(self):
        msg = self.entry.text().strip()
        if not msg:
            return
        self.entry.clear()
        self.send_command(msg)

    def send_command(self, command):
        if self.worker is not None and self.worker.isRunning():
            self.add_message("GURKAN AI", "Önce mevcut işlemin tamamlanmasını bekle.")
            return
        text = command.strip()
        if not text:
            return
        if text == "/ses":
            self.toggle_speech()
            return
        if text in ("/ara", "/sor"):
            self.entry.setText(text + " ")
            self.entry.setFocus()
            return
        if text == "/gor":
            text = "/gor-5"  # Varsayilan guvenli yerel OCR yolu.

        self.add_message("Sen", text, True)
        if text == "/gor-5":
            self.add_message("GURKAN AI", "5 saniye içinde okumak istediğin pencereye geç. "
                             "Analiz tamamlanınca bu pencere geri açılacak.")
            self.showMinimized()
            QTimer.singleShot(400, lambda: self.launch("screen"))
            return
        if text.startswith("/sor "):
            self.launch("rag", text[5:].strip())
        elif text.startswith("/ara "):
            self.launch("find", text[5:].strip())
        elif text == "/bilgi-durum":
            self.launch("status")
        elif text == "/notlar":
            self.launch("notes")
        elif text == "/indeksle":
            self.launch("index")
        elif text == "/onayla":
            self.launch("approve")
        elif text == "/reddet":
            self.launch("reject")
        elif text == "/aktar":
            self.add_message("GURKAN AI", "Devir notu oluşturma bu ilk arayüz sürümünde "
                             "henüz bağlanmadı; v2.9.6 terminalinden /aktar kullanılabilir.")
        else:
            self.launch("chat", text)

    def launch(self, operation, arg=""):
        if self.worker is not None and self.worker.isRunning():
            return
        self.state.setText("◉  İşleniyor...")
        self.core.busy = True
        self.btn_send.setEnabled(False)
        self.btn_voice.setEnabled(False)
        self.worker = TaskWorker(
            operation, arg, self.provider.currentData() or "yerel",
            speak=self.speech_enabled and operation in ("chat", "rag")
        )
        self.worker.result.connect(self.handle_result)
        self.worker.failure.connect(self.handle_failure)
        self.worker.finished.connect(self.handle_finished)
        self.worker.start()

    def handle_result(self, op, output):
        if op == "screen":
            self.showNormal()
            self.raise_()
            self.activateWindow()
        if op == "status":
            m = re.search(r"Toplam:\s*(\d+)\s*not", output)
            if m:
                self.card_vault.value.setText(m.group(1) + " not")
            self.add_message("GURKAN AI", output)
        elif op == "chat":
            self.local_badge.setText("●  Model: " + ("Google API" if self.provider.currentData() == "google" else "LM Studio"))
            self.add_message("GURKAN AI", output)
        else:
            self.add_message("GURKAN AI", output)
        if op == "index":
            self.card_vault.subtitle.setText("RAG indeksi yenilendi")

    def handle_failure(self, op, error):
        if op == "screen":
            self.showNormal()
            self.raise_()
            self.activateWindow()
        self.add_message("GURKAN AI", "İşlem tamamlanamadı: " + error +
                         "\nLM Studio açıksa model adını ve sunucu bağlantısını kontrol et.")

    def handle_finished(self):
        self.state.setText("●  Hazır")
        self.core.busy = False
        self.btn_send.setEnabled(True)
        self.btn_voice.setEnabled(True)
        self.entry.setFocus()

    def closeEvent(self, event):
        if self.worker is not None and self.worker.isRunning():
            QMessageBox.information(self, "GURKAN AI", "Arka plandaki işlem sürüyor. "
                                    "İşlem bitince uygulamayı kapatabilirsin.")
            event.ignore()
            return
        event.accept()


STYLESHEET = """
QWidget { background: #07111F; color: #E9F5FF; font-family: 'Segoe UI'; font-size: 12px; }
QMainWindow, QWidget#root { background: #07111F; }
QFrame#sidebar, QFrame#centralPanel, QFrame#chatPanel { background: #0B1A2A; border: 1px solid #1B4059; border-radius: 15px; }
QFrame#centralPanel, QFrame#chatPanel { background: #091929; }
QFrame#statCard { background: #10263B; border: 1px solid #214A62; border-radius: 10px; }
QLabel { background: transparent; }
QLabel#brand { font-size: 20px; font-weight: 800; color: #E9F8FF; }
QLabel#title { font-size: 28px; font-weight: 800; }
QLabel#dimText { font-size: 11px; color: #90AABF; }
QLabel#readyLabel { color: #3DD9A6; font-weight: 700; }
QLabel#sectionHeading { color: #BCEAFF; font-weight: 750; font-size: 15px; }
QLabel#statValue { color: #44D9FF; font-size: 25px; font-weight: 700; }
QLabel#bubbleAuthor { color: #4AD8FF; font-size: 10px; font-weight: 750; }
QLabel#bodyText { color: #E9F5FF; font-size: 12px; }
QFrame#bubbleMine { background: #153954; border-radius: 12px; border: 1px solid #285B7B; }
QFrame#bubbleAssistant { background: #10293C; border-radius: 12px; border: 1px solid #1B4059; }
QScrollArea#chatScroll { background: transparent; border: 0; }
QScrollArea#chatScroll > QWidget > QWidget { background: transparent; }
QPushButton { background: #12334B; color: #D9F3FF; padding: 10px 12px; border: 1px solid #2A5875; border-radius: 9px; font-weight: 650; }
QPushButton:hover { background: #194F70; border-color: #36C7F3; }
QPushButton:pressed { background: #126CA3; }
QPushButton:disabled { background: #243443; color: #7193A6; }
QPushButton#menuBtn { text-align: left; background: transparent; border: none; padding: 13px 9px; font-size: 13px; }
QPushButton#menuBtn:hover { background: #123851; }
QPushButton#quickBtn { padding: 12px 5px; }
QPushButton#primaryBtn { background: #0789D4; border-color: #20C7FE; }
QPushButton#primaryBtn:hover { background: #069BEA; }
QPushButton#smallBtn { font-size: 17px; min-width: 34px; }
QLineEdit, QComboBox { color: #E9F5FF; background: #10283F; border: 1px solid #2B607C; border-radius: 9px; padding: 11px; }
QLineEdit:focus { border: 1px solid #4EC8FC; }
QComboBox QAbstractItemView { background: #122B42; color: white; selection-background-color: #1C618A; }
QSplitter::handle { background: #0A1C2B; }
QScrollBar:vertical { background: #0C1D2A; width: 9px; }
QScrollBar::handle:vertical { background: #285E78; min-height: 30px; border-radius: 4px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
"""


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("GURKAN AI v3.0")
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
