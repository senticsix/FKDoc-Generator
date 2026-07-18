"""Modernes App-Theme: folgt automatisch dem System (hell/dunkel).

Die Farbwerte werden per Token (@name) in das QSS-Template eingesetzt.
"""

from PyQt6.QtCore import Qt

LIGHT = {
    "bg": "#f4f5f7",
    "surface": "#ffffff",
    "surface2": "#eceef2",
    "border": "#d8dbe2",
    "text": "#1e2228",
    "muted": "#6b7280",
    "accent": "#2f6fed",
    "accent_hover": "#4a83f0",
    "accent_pressed": "#2a63d4",
    "accent_soft": "rgba(47, 111, 237, 40)",
    "on_accent": "#ffffff",
}

DARK = {
    "bg": "#1b1d22",
    "surface": "#25272e",
    "surface2": "#2e313a",
    "border": "#3b3f4a",
    "text": "#e8eaed",
    "muted": "#9aa0a6",
    "accent": "#4c8dff",
    "accent_hover": "#5e99ff",
    "accent_pressed": "#3d7ce6",
    "accent_soft": "rgba(76, 141, 255, 55)",
    "on_accent": "#ffffff",
}

QSS_TEMPLATE = """
QWidget {
    background-color: @bg;
    color: @text;
    font-size: 13px;
}

QLabel {
    background: transparent;
}

QLabel#footerLabel {
    color: @muted;
    font-size: 11px;
    padding-top: 4px;
}

QLabel#hintLabel {
    color: @muted;
    font-size: 12px;
    padding: 4px;
}

/* --- Eingabefelder --- */
QLineEdit, QDateEdit, QComboBox {
    background-color: @surface;
    border: 1px solid @border;
    border-radius: 8px;
    padding: 7px 10px;
    selection-background-color: @accent;
    selection-color: @on_accent;
}

QLineEdit:focus, QDateEdit:focus, QComboBox:focus {
    border: 1px solid @accent;
}

QLineEdit:read-only {
    background-color: @surface2;
    color: @muted;
}

QLineEdit#rangeDisplay {
    background-color: @surface;
    color: @text;
    font-weight: 600;
}

/* --- Buttons --- */
QPushButton {
    background-color: @surface;
    border: 1px solid @border;
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: 600;
}

QPushButton:hover {
    background-color: @surface2;
    border-color: @accent;
}

QPushButton:pressed {
    background-color: @border;
}

QPushButton#primaryButton {
    background-color: @accent;
    border: 1px solid @accent;
    color: @on_accent;
}

QPushButton#primaryButton:hover {
    background-color: @accent_hover;
}

QPushButton#primaryButton:pressed {
    background-color: @accent_pressed;
}

/* --- Radio & Checkbox --- */
QRadioButton, QCheckBox {
    spacing: 8px;
    padding: 4px 0;
    background: transparent;
}

QRadioButton::indicator {
    width: 18px;
    height: 18px;
    border-radius: 11px;
    border: 2px solid @border;
    background-color: @surface;
}

QRadioButton::indicator:hover {
    border-color: @accent;
}

QRadioButton::indicator:checked {
    width: 12px;
    height: 12px;
    border: 5px solid @accent;
    border-radius: 11px;
    background-color: @on_accent;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 5px;
    border: 2px solid @border;
    background-color: @surface;
}

QCheckBox::indicator:hover {
    border-color: @accent;
}

QCheckBox::indicator:checked {
    background-color: @accent;
    border-color: @accent;
    image: none;
}

/* --- ComboBox/DateEdit-Dropdown --- */
QComboBox::drop-down, QDateEdit::drop-down {
    border: none;
    background: transparent;
    width: 24px;
}

QComboBox QAbstractItemView {
    background-color: @surface;
    border: 1px solid @border;
    border-radius: 8px;
    selection-background-color: @accent;
    selection-color: @on_accent;
    outline: none;
}

/* --- Kalender --- */
QCalendarWidget QWidget {
    alternate-background-color: @surface;
}

QCalendarWidget QWidget#qt_calendar_navigationbar {
    background-color: @surface2;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
}

QCalendarWidget QToolButton {
    background: transparent;
    border: none;
    border-radius: 6px;
    color: @text;
    padding: 4px 8px;
    font-weight: 600;
}

QCalendarWidget QToolButton:hover {
    background-color: @accent_soft;
}

QCalendarWidget QToolButton::menu-indicator {
    image: none;
    width: 0;
}

QCalendarWidget QAbstractItemView {
    background-color: @surface;
    selection-background-color: @accent;
    selection-color: @on_accent;
    outline: none;
}

QFrame#calendarPopup {
    background-color: @surface;
    border: 1px solid @border;
    border-radius: 10px;
}

/* --- Dialoge & Meldungen --- */
QMessageBox, QInputDialog, QDialog {
    background-color: @bg;
}

QDialogButtonBox QPushButton {
    min-width: 84px;
}

/* --- Scrollbars --- */
QScrollBar:vertical {
    background: transparent;
    width: 10px;
    margin: 2px;
}

QScrollBar::handle:vertical {
    background: @border;
    border-radius: 4px;
    min-height: 24px;
}

QScrollBar::handle:vertical:hover {
    background: @muted;
}

QScrollBar::add-line, QScrollBar::sub-line {
    height: 0;
}
"""


def build_stylesheet(palette):
    qss = QSS_TEMPLATE

    # Längste Tokens zuerst ersetzen, damit z. B. @surface nicht
    # den Anfang von @surface2 wegfrisst.
    for key in sorted(palette, key=len, reverse=True):
        qss = qss.replace(f"@{key}", palette[key])

    return qss


def is_dark_mode(app):
    try:
        return app.styleHints().colorScheme() == Qt.ColorScheme.Dark
    except AttributeError:
        # Ältere Qt-Version: aus der Systempalette ableiten
        return app.palette().window().color().lightness() < 128


def apply_theme(app):
    palette = DARK if is_dark_mode(app) else LIGHT
    app.setStyleSheet(build_stylesheet(palette))


def install_auto_theme(app):
    """Apply the theme and follow live system light/dark switches."""
    apply_theme(app)

    try:
        app.styleHints().colorSchemeChanged.connect(lambda _: apply_theme(app))
    except AttributeError:
        pass
