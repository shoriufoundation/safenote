"""
SafeNote About and Security Model Widget.

Presents:
- Application identity & metadata (Shoriu Foundation, v0.1.0-dev, WTFPL 2)
- Privacy charter (offline-first, no telemetry, no accounts)
- Security architecture & threat model disclosure
- License text and open source notice
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from core.application import get_app


class AboutWidget(QWidget):
    """
    About SafeNote and technical disclosures page.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(32, 28, 32, 28)
        main_layout.setSpacing(16)

        # Scroll area to comfortably show all disclosure information
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(20)

        # Header Hero Card
        hero_card = QFrame()
        hero_card.setObjectName("card")
        hero_layout = QVBoxLayout(hero_card)
        hero_layout.setContentsMargins(28, 24, 28, 24)
        hero_layout.setSpacing(10)

        title = QLabel("🛡️ SafeNote")
        title.setObjectName("title")
        title.setStyleSheet("font-size: 26px; font-weight: bold;")

        self._slogan_lbl = QLabel("Your safety. Your privacy. Your choice.")
        self._slogan_lbl.setObjectName("subtitle")
        self._slogan_lbl.setStyleSheet("font-size: 15px; font-weight: 500; color: #58a6ff;")

        self._meta_lbl = QLabel(
            "Version 0.1.0-dev • Shoriu Foundation • License: WTFPL 2\n"
            "Free and Open Source Software (FOSS)"
        )
        self._meta_lbl.setObjectName("subtitle")
        self._meta_lbl.setStyleSheet("font-size: 12px; color: #8b949e;")

        hero_layout.addWidget(title)
        hero_layout.addWidget(self._slogan_lbl)
        hero_layout.addWidget(self._meta_lbl)
        layout.addWidget(hero_card)

        # Privacy Charter Card
        privacy_card = QFrame()
        privacy_card.setObjectName("card")
        p_layout = QVBoxLayout(privacy_card)
        p_layout.setContentsMargins(24, 20, 24, 20)
        p_layout.setSpacing(10)

        p_title = QLabel("🌟 Privacy & Ethical Principles")
        p_title.setObjectName("heading")
        p_text = QLabel(
            "• Offline-First: SafeNote operates completely on your machine.\n"
            "• Zero Telemetry: No tracking, analytics, or background telemetry.\n"
            "• No Mandatory Cloud: You own your recordings and your encryption keys.\n"
            "• Transparent Operation: The microphone is never accessed silently.\n"
            "• Open Source: Fully auditable, reproducible, and verifiable."
        )
        p_text.setStyleSheet("line-height: 1.6; font-size: 13px;")

        p_layout.addWidget(p_title)
        p_layout.addWidget(p_text)
        layout.addWidget(privacy_card)

        # Security Architecture & Threat Model Card
        sec_card = QFrame()
        sec_card.setObjectName("card")
        s_layout = QVBoxLayout(sec_card)
        s_layout.setContentsMargins(24, 20, 24, 20)
        s_layout.setSpacing(10)

        s_title = QLabel("🔐 Security Model & Cryptographic Design")
        s_title.setObjectName("heading")

        s_text = QLabel(
            "• Encryption: Standard AES-256-GCM (Galois/Counter Mode) authenticated encryption.\n"
            "• Nonces: Cryptographically random 96-bit (12-byte) nonces generated per recording via secrets.token_bytes.\n"
            "• Key Storage: AES-256 master key is held in the OS Credential Manager (Windows Keyring).\n"
            "• In-Memory Playback: Audio decryption occurs directly into memory (RAM). Decrypted audio never touches persistent disk.\n"
            "• Atomic Writes: Audio recordings are encrypted to temporary files and atomically moved upon completion.\n"
            "• Honest Security Notice: No software can protect against an attacker with full administrative or kernel-level control over your operating system. If you lose your encryption key, recordings cannot be decrypted."
        )
        s_text.setWordWrap(True)
        s_text.setStyleSheet("line-height: 1.6; font-size: 13px; color: #c9d1d9;")

        s_layout.addWidget(s_title)
        s_layout.addWidget(s_text)
        layout.addWidget(sec_card)

        # License text card
        lic_card = QFrame()
        lic_card.setObjectName("card")
        l_layout = QVBoxLayout(lic_card)
        l_layout.setContentsMargins(24, 20, 24, 20)
        l_layout.setSpacing(8)

        l_title = QLabel("📜 License (WTFPL 2)")
        l_title.setObjectName("heading")

        l_text = QLabel(
            "DO WHAT THE FUCK YOU WANT TO PUBLIC LICENSE\n"
            "Version 2, December 2004\n\n"
            "Everyone is permitted to copy and distribute verbatim or modified\n"
            "copies of this license document, and changing it is allowed as long\n"
            "as the name is changed.\n\n"
            "0. You just DO WHAT THE FUCK YOU WANT TO."
        )
        l_text.setStyleSheet("font-family: monospace; font-size: 11px; color: #8b949e;")

        l_layout.addWidget(l_title)
        l_layout.addWidget(l_text)
        layout.addWidget(lic_card)

        layout.addStretch()
        scroll.setWidget(container)
        main_layout.addWidget(scroll)

        self.retranslate()
        get_app().language_changed.connect(self.retranslate)

    def retranslate(self) -> None:
        app = get_app()
        self._slogan_lbl.setText(app.tr("slogan"))
