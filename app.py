import os
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox, QComboBox, QFileDialog, QGroupBox, QHBoxLayout,
    QLabel, QLineEdit, QMainWindow, QPlainTextEdit, QProgressBar, QPushButton,
    QTextEdit, QVBoxLayout, QWidget, QFormLayout,
)

from converter import ConvertOptions
from session import is_logged_in, clear_session, DND_URL
from workers import ConvertWorker, LoginWorker

DARK_STYLE = """
QMainWindow, QWidget {
    background-color: #1e1e2e;
    color: #cdd6f4;
}
QGroupBox {
    border: 1px solid #45475a;
    border-radius: 6px;
    margin-top: 12px;
    padding-top: 8px;
    font-weight: bold;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 4px;
    color: #89b4fa;
}
QLineEdit, QComboBox {
    background-color: #313244;
    border: 1px solid #45475a;
    border-radius: 4px;
    padding: 6px 8px;
    color: #cdd6f4;
}
QLineEdit:focus, QComboBox:focus { border-color: #89b4fa; }
QComboBox::drop-down { border: none; padding-right: 8px; }
QComboBox QAbstractItemView {
    background-color: #313244;
    border: 1px solid #45475a;
    selection-background-color: #45475a;
}
QPushButton {
    background-color: #89b4fa;
    color: #1e1e2e;
    border: none;
    border-radius: 6px;
    padding: 8px 18px;
    font-weight: bold;
}
QPushButton:hover { background-color: #b4befe; }
QPushButton:disabled { background-color: #45475a; color: #6c7086; }
QPushButton#secondaryBtn {
    background-color: #45475a;
    color: #cdd6f4;
    padding: 6px 12px;
}
QPushButton#secondaryBtn:hover { background-color: #585b70; }
QPushButton#dangerBtn {
    background-color: #f38ba8;
    color: #1e1e2e;
    padding: 6px 12px;
}
QPushButton#dangerBtn:hover { background-color: #eba0ac; }
QPushButton#openBtn { background-color: #a6e3a1; }
QPushButton#openBtn:hover { background-color: #94e2d5; }
QPushButton#doneBtn { background-color: #a6e3a1; color: #1e1e2e; padding: 6px 12px; }
QPushButton#doneBtn:hover { background-color: #94e2d5; }
QCheckBox { spacing: 6px; }
QCheckBox::indicator {
    width: 16px; height: 16px;
    border: 1px solid #45475a;
    border-radius: 3px;
    background-color: #313244;
}
QCheckBox::indicator:checked { background-color: #89b4fa; border-color: #89b4fa; }
QPlainTextEdit {
    background-color: #313244;
    border: 1px solid #45475a;
    border-radius: 4px;
    padding: 6px 8px;
    color: #cdd6f4;
}
QPlainTextEdit:focus { border-color: #89b4fa; }
QTextEdit {
    background-color: #181825;
    border: 1px solid #45475a;
    border-radius: 4px;
    color: #a6e3a1;
    font-family: monospace;
    font-size: 12px;
    padding: 4px;
}
QProgressBar {
    background-color: #313244;
    border: none;
    border-radius: 4px;
    height: 8px;
}
QProgressBar::chunk { background-color: #89b4fa; border-radius: 4px; }
QLabel#statusLabel[status="ok"] { color: #a6e3a1; }
QLabel#statusLabel[status="error"] { color: #f38ba8; }
QLabel#loginStatus[status="ok"] { color: #a6e3a1; font-weight: bold; }
QLabel#loginStatus[status="off"] { color: #6c7086; }
QLabel#loginStatus[status="busy"] { color: #f9e2af; }
"""


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._convert_worker = None
        self._login_worker = None
        self._last_output = None
        self._build_ui()

    def _build_ui(self):
        self.setWindowTitle("Web to PDF")
        self.setMinimumSize(660, 720)

        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        # --- URLs ---
        url_group = QGroupBox("Web Page URLs (one per line — each becomes a chapter)")
        url_layout = QVBoxLayout(url_group)
        self.url_input = QPlainTextEdit()
        self.url_input.setPlaceholderText("https://example.com/chapter-1\nhttps://example.com/chapter-2\nhttps://example.com/chapter-3")
        self.url_input.setFixedHeight(90)
        url_layout.addWidget(self.url_input)
        layout.addWidget(url_group)

        # --- Output ---
        out_group = QGroupBox("Output File")
        out_layout = QHBoxLayout(out_group)
        self.out_input = QLineEdit(str(Path.home() / "Downloads" / "output.pdf"))
        browse_btn = QPushButton("Browse...")
        browse_btn.setObjectName("secondaryBtn")
        browse_btn.clicked.connect(self._browse_output)
        out_layout.addWidget(self.out_input)
        out_layout.addWidget(browse_btn)
        layout.addWidget(out_group)

        # --- D&D Beyond Login ---
        dnd_group = QGroupBox("D&D Beyond")
        dnd_layout = QVBoxLayout(dnd_group)

        status_row = QHBoxLayout()
        self.login_status = QLabel()
        self.login_status.setObjectName("loginStatus")
        self._refresh_login_status()
        status_row.addWidget(self.login_status)
        status_row.addStretch()

        self.login_btn = QPushButton("Login...")
        self.login_btn.setObjectName("secondaryBtn")
        self.login_btn.clicked.connect(self._start_login)

        self.done_btn = QPushButton("Done — Save Session")
        self.done_btn.setObjectName("doneBtn")
        self.done_btn.setVisible(False)
        self.done_btn.clicked.connect(self._finish_login)

        self.logout_btn = QPushButton("Logout")
        self.logout_btn.setObjectName("dangerBtn")
        self.logout_btn.clicked.connect(self._logout)
        self.logout_btn.setVisible(is_logged_in())

        status_row.addWidget(self.login_btn)
        status_row.addWidget(self.done_btn)
        status_row.addWidget(self.logout_btn)
        dnd_layout.addLayout(status_row)

        hint = QLabel("Log in once to convert D&D Beyond character sheets and campaign pages.")
        hint.setStyleSheet("color: #6c7086; font-size: 11px;")
        hint.setWordWrap(True)
        dnd_layout.addWidget(hint)
        layout.addWidget(dnd_group)

        # --- Options ---
        opts_group = QGroupBox("Options")
        opts_form = QFormLayout(opts_group)
        opts_form.setSpacing(10)

        self.format_combo = QComboBox()
        self.format_combo.addItems(["A4", "A3", "A5", "Letter", "Legal", "Tabloid"])
        opts_form.addRow("Page format:", self.format_combo)

        self.landscape_check = QCheckBox("Landscape orientation")
        opts_form.addRow("", self.landscape_check)

        self.bg_check = QCheckBox("Include background colors & images")
        self.bg_check.setChecked(True)
        opts_form.addRow("", self.bg_check)

        margin_w = QWidget()
        margin_l = QHBoxLayout(margin_w)
        margin_l.setContentsMargins(0, 0, 0, 0)
        self.margin_combo = QComboBox()
        self.margin_combo.addItems(["None (0)", "Small (0.5cm)", "Normal (1cm)", "Large (2cm)"])
        self.margin_combo.setCurrentIndex(2)
        margin_l.addWidget(self.margin_combo)
        margin_l.addStretch()
        opts_form.addRow("Margins:", margin_w)

        wait_w = QWidget()
        wait_l = QHBoxLayout(wait_w)
        wait_l.setContentsMargins(0, 0, 0, 0)
        self.wait_combo = QComboBox()
        self.wait_combo.addItems(["networkidle (recommended)", "load", "domcontentloaded"])
        wait_l.addWidget(self.wait_combo)
        wait_l.addStretch()
        opts_form.addRow("Wait until:", wait_w)

        layout.addWidget(opts_group)

        # --- Convert ---
        self.convert_btn = QPushButton("Convert to PDF")
        self.convert_btn.setMinimumHeight(44)
        f = self.convert_btn.font()
        f.setPointSize(11)
        self.convert_btn.setFont(f)
        self.convert_btn.clicked.connect(self._start_convert)
        layout.addWidget(self.convert_btn)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        status_row2 = QHBoxLayout()
        self.status_label = QLabel("")
        self.status_label.setObjectName("statusLabel")
        self.open_btn = QPushButton("Open PDF")
        self.open_btn.setObjectName("openBtn")
        self.open_btn.setVisible(False)
        self.open_btn.clicked.connect(self._open_pdf)
        status_row2.addWidget(self.status_label)
        status_row2.addStretch()
        status_row2.addWidget(self.open_btn)
        layout.addLayout(status_row2)

        log_group = QGroupBox("Log")
        log_layout = QVBoxLayout(log_group)
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setMaximumHeight(110)
        log_layout.addWidget(self.log_view)
        layout.addWidget(log_group)

    # --- D&D Beyond login ---

    def _refresh_login_status(self):
        if is_logged_in():
            self.login_status.setText("Logged in to D&D Beyond")
            self.login_status.setProperty("status", "ok")
        else:
            self.login_status.setText("Not logged in to D&D Beyond")
            self.login_status.setProperty("status", "off")
        self.login_status.style().unpolish(self.login_status)
        self.login_status.style().polish(self.login_status)

    def _start_login(self):
        self.login_btn.setEnabled(False)
        self.done_btn.setVisible(True)
        self.logout_btn.setVisible(False)
        self.login_status.setText("Browser open — log in, then click Done")
        self.login_status.setProperty("status", "busy")
        self.login_status.style().unpolish(self.login_status)
        self.login_status.style().polish(self.login_status)
        self.log_view.append("Opening D&D Beyond login in Opera GX...")

        self._login_worker = LoginWorker()
        self._login_worker.finished.connect(self._on_login_done)
        self._login_worker.start()

    def _finish_login(self):
        self.done_btn.setVisible(False)
        self.log_view.append("Saving session...")
        if self._login_worker:
            self._login_worker.save_and_close()

    def _on_login_done(self, success: bool, message: str):
        self.login_btn.setEnabled(True)
        self.done_btn.setVisible(False)
        self.logout_btn.setVisible(is_logged_in())
        self._refresh_login_status()
        self.log_view.append(message)

    def _logout(self):
        clear_session()
        self.logout_btn.setVisible(False)
        self._refresh_login_status()
        self.log_view.append("D&D Beyond session cleared.")

    # --- PDF conversion ---

    def _browse_output(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save PDF as", self.out_input.text(), "PDF Files (*.pdf)"
        )
        if path:
            self.out_input.setText(path if path.endswith(".pdf") else path + ".pdf")

    def _margin_value(self) -> str:
        return {"None (0)": "0", "Small (0.5cm)": "0.5cm",
                "Normal (1cm)": "1cm", "Large (2cm)": "2cm"}[self.margin_combo.currentText()]

    def _start_convert(self):
        raw_urls = self.url_input.toPlainText().strip().splitlines()
        urls = []
        for u in raw_urls:
            u = u.strip()
            if not u:
                continue
            if not u.startswith(("http://", "https://")):
                u = "https://" + u
            urls.append(u)

        output = self.out_input.text().strip()

        if not urls:
            self._set_status("Please enter at least one URL.", "error")
            return
        if not output:
            self._set_status("Please choose an output file.", "error")
            return

        if any(DND_URL in u for u in urls) and not is_logged_in():
            self.log_view.append("Tip: Log in to D&D Beyond to access protected pages.")

        margin = self._margin_value()
        options = ConvertOptions(
            urls=urls, output_path=output,
            format=self.format_combo.currentText(),
            landscape=self.landscape_check.isChecked(),
            margin_top=margin, margin_right=margin,
            margin_bottom=margin, margin_left=margin,
            print_background=self.bg_check.isChecked(),
            wait_until=self.wait_combo.currentText().split(" ")[0],
        )

        self.convert_btn.setEnabled(False)
        self.open_btn.setVisible(False)
        self.progress_bar.setVisible(True)
        self.log_view.clear()
        self._set_status("Converting...", "")

        self._convert_worker = ConvertWorker(options)
        self._convert_worker.progress.connect(self.log_view.append)
        self._convert_worker.finished.connect(self._on_convert_done)
        self._convert_worker.error.connect(self._on_convert_error)
        self._convert_worker.start()

    def _on_convert_done(self, path: str):
        self._last_output = path
        self._set_status(f"Done! Saved to {path}", "ok")
        self.progress_bar.setVisible(False)
        self.convert_btn.setEnabled(True)
        self.open_btn.setVisible(True)

    def _on_convert_error(self, msg: str):
        self._set_status(f"Error: {msg}", "error")
        self.log_view.append(f"ERROR: {msg}")
        self.progress_bar.setVisible(False)
        self.convert_btn.setEnabled(True)

    def _set_status(self, msg: str, status: str):
        self.status_label.setText(msg)
        self.status_label.setProperty("status", status)
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)

    def _open_pdf(self):
        if self._last_output and os.path.exists(self._last_output):
            os.system(f'xdg-open "{self._last_output}"')
