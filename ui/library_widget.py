"""
SafeNote Recording Library Widget.

Provides full recording management:
- SQLite-backed recording list with search and sorting
- Play recording integration
- Rename recording
- Delete with confirmation dialog
- Export to unencrypted WAV with clear user warning
- File integrity checks and orphaned record cleanup
- Rescan directory for externally added files
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.application import get_app
from crypto.key_manager import get_or_create_key
from storage.recording_repository import RecordingRepository

logger = logging.getLogger(__name__)


def _format_size(size_bytes: int | None) -> str:
    if size_bytes is None:
        return "Unknown"
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes / (1024 * 1024):.1f} MB"


def _format_duration(seconds: float | None) -> str:
    if seconds is None:
        return "00:00"
    sec = int(seconds)
    mins = sec // 60
    s = sec % 60
    return f"{mins:02d}:{s:02d}"


class LibraryWidget(QWidget):
    """
    Recording library and archive management.
    """

    play_requested = Signal(str)  # filepath to play

    def __init__(self, repo: RecordingRepository, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._repo = repo
        self._recordings: list[dict] = []
        self._init_ui()
        self.refresh_library()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(32, 28, 32, 28)
        main_layout.setSpacing(16)

        # Header section
        header_layout = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setSpacing(4)
        self._page_title = QLabel()
        self._page_title.setObjectName("title")
        self._page_subtitle = QLabel()
        self._page_subtitle.setObjectName("subtitle")
        title_box.addWidget(self._page_title)
        title_box.addWidget(self._page_subtitle)
        header_layout.addLayout(title_box)
        header_layout.addStretch()

        self._scan_btn = QPushButton("🔄 Rescan Folder")
        self._scan_btn.clicked.connect(self._rescan_and_refresh)
        header_layout.addWidget(self._scan_btn)

        main_layout.addLayout(header_layout)

        # Search and filter bar
        filter_card = QFrame()
        filter_card.setObjectName("card")
        filter_layout = QHBoxLayout(filter_card)
        filter_layout.setContentsMargins(12, 10, 12, 10)
        filter_layout.setSpacing(12)

        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("🔍 Search recordings by name...")
        self._search_input.textChanged.connect(self._on_search_changed)
        filter_layout.addWidget(self._search_input, stretch=1)

        main_layout.addWidget(filter_card)

        # Table of recordings
        self._table = QTableWidget()
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels(["Name", "Created", "Duration", "Size", "Status"])
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.itemDoubleClicked.connect(self._on_double_click)
        self._table.itemSelectionChanged.connect(self._on_selection_changed)

        main_layout.addWidget(self._table, stretch=1)

        # Actions toolbar
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(12)

        self._btn_play = QPushButton("▶ Play")
        self._btn_play.setObjectName("primary")
        self._btn_play.setEnabled(False)
        self._btn_play.clicked.connect(self._play_selected)

        self._btn_rename = QPushButton("✏️ Rename")
        self._btn_rename.setEnabled(False)
        self._btn_rename.clicked.connect(self._rename_selected)

        self._btn_export = QPushButton("📤 Export to WAV...")
        self._btn_export.setEnabled(False)
        self._btn_export.clicked.connect(self._export_selected)

        self._btn_delete = QPushButton("🗑️ Delete")
        self._btn_delete.setObjectName("danger")
        self._btn_delete.setEnabled(False)
        self._btn_delete.clicked.connect(self._delete_selected)

        actions_layout.addWidget(self._btn_play)
        actions_layout.addWidget(self._btn_rename)
        actions_layout.addWidget(self._btn_export)
        actions_layout.addStretch()
        actions_layout.addWidget(self._btn_delete)

        main_layout.addLayout(actions_layout)

        self.retranslate()
        get_app().language_changed.connect(self.retranslate)

    def retranslate(self) -> None:
        app = get_app()
        self._page_title.setText(app.tr("library"))
        self._page_subtitle.setText(f"{len(self._recordings)} recordings stored")
        self._table.setHorizontalHeaderLabels([
            app.tr("name"),
            app.tr("date"),
            app.tr("duration_col") if "duration_col" in app.localizer._translations else "Duration",
            app.tr("size"),
            "Status",
        ])
        self._search_input.setPlaceholderText(f"🔍 {app.tr('search')}...")
        self._btn_play.setText(f"▶ {app.tr('play')}")
        self._btn_rename.setText(f"✏️ {app.tr('rename')}")
        self._btn_export.setText(f"📤 {app.tr('export_wav')}...")
        self._btn_delete.setText(f"🗑️ {app.tr('delete')}")

    def refresh_library(self) -> None:
        """Reload recordings from database."""
        query = self._search_input.text().strip()
        if query:
            self._recordings = self._repo.search(query)
        else:
            self._recordings = self._repo.get_all_recordings()

        self._table.setRowCount(len(self._recordings))
        for row_idx, rec in enumerate(self._recordings):
            # Name
            name_item = QTableWidgetItem(rec.get("display_name") or rec.get("filename", "Unknown"))
            self._table.setItem(row_idx, 0, name_item)

            # Date
            created = rec.get("created_at", "")[:19].replace("T", " ")
            date_item = QTableWidgetItem(created)
            self._table.setItem(row_idx, 1, date_item)

            # Duration
            dur_item = QTableWidgetItem(_format_duration(rec.get("duration_seconds")))
            dur_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._table.setItem(row_idx, 2, dur_item)

            # Size
            size_item = QTableWidgetItem(_format_size(rec.get("file_size")))
            size_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self._table.setItem(row_idx, 3, size_item)

            # Status (check if file exists)
            exists = Path(rec["filepath"]).is_file()
            status_text = "🔒 Valid" if exists else "⚠️ Missing"
            status_item = QTableWidgetItem(status_text)
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if not exists:
                status_item.setForeground(Qt.GlobalColor.red)
            self._table.setItem(row_idx, 4, status_item)

        self.retranslate()
        self._on_selection_changed()

    def _rescan_and_refresh(self) -> None:
        """Scan storage directory for new files and refresh."""
        self._repo.scan_directory()
        self._repo.cleanup_orphaned()
        self.refresh_library()

    def _on_search_changed(self, text: str) -> None:
        self.refresh_library()

    def _get_selected_recording(self) -> Optional[dict]:
        row = self._table.currentRow()
        if 0 <= row < len(self._recordings):
            return self._recordings[row]
        return None

    def _on_selection_changed(self) -> None:
        rec = self._get_selected_recording()
        has_sel = rec is not None
        file_exists = has_sel and Path(rec["filepath"]).is_file()

        self._btn_play.setEnabled(file_exists)
        self._btn_rename.setEnabled(has_sel)
        self._btn_export.setEnabled(file_exists)
        self._btn_delete.setEnabled(has_sel)

    def _on_double_click(self, item: QTableWidgetItem) -> None:
        self._play_selected()

    def _play_selected(self) -> None:
        rec = self._get_selected_recording()
        if rec and Path(rec["filepath"]).is_file():
            self.play_requested.emit(rec["filepath"])

    def _rename_selected(self) -> None:
        rec = self._get_selected_recording()
        if not rec:
            return

        app = get_app()
        curr_name = rec.get("display_name") or rec.get("filename")
        new_name, ok = QInputDialog.getText(
            self,
            app.tr("rename"),
            f"{app.tr('name')}:",
            text=curr_name
        )
        if ok and new_name.strip():
            self._repo.rename(rec["id"], new_name.strip())
            self.refresh_library()

    def _delete_selected(self) -> None:
        rec = self._get_selected_recording()
        if not rec:
            return

        app = get_app()
        name = rec.get("display_name") or rec.get("filename")
        reply = QMessageBox.question(
            self,
            app.tr("delete_confirm"),
            f"{app.tr('delete_confirm_msg')}\n\n'{name}'",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._repo.delete(rec["id"])
            self.refresh_library()

    def _export_selected(self) -> None:
        rec = self._get_selected_recording()
        if not rec:
            return

        app = get_app()
        # Security warning prompt
        warn_reply = QMessageBox.warning(
            self,
            app.tr("warning"),
            f"SECURITY NOTICE:\n{app.tr('export_warning')}\n\n"
            "The exported WAV file will NOT be encrypted.\n"
            "Do you wish to proceed?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if warn_reply != QMessageBox.StandardButton.Yes:
            return

        default_name = f"{Path(rec['filename']).stem}.wav"
        dest_path, _ = QFileDialog.getSaveFileName(
            self,
            app.tr("export_wav"),
            default_name,
            "WAV Audio (*.wav)"
        )
        if not dest_path:
            return

        try:
            key = get_or_create_key()
            if self._repo.export_wav(rec["id"], dest_path, key):
                QMessageBox.information(
                    self,
                    app.tr("info"),
                    f"Recording successfully exported to:\n{dest_path}"
                )
            else:
                QMessageBox.critical(self, app.tr("error"), "Export failed.")
        except Exception as exc:
            QMessageBox.critical(self, app.tr("error"), f"Export error: {exc}")
