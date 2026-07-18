from pathlib import Path

from PyQt6.QtCore import (
    QDate,
    QEasingCurve,
    QPoint,
    QPropertyAnimation,
    Qt,
    QThread,
    QUrl,
    pyqtSignal,
)
from PyQt6.QtGui import QColor, QDesktopServices
from PyQt6.QtWidgets import (
    QWidget,
    QRadioButton,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QDateEdit,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QButtonGroup,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QCalendarWidget,
    QLabel,
    QFrame,
    QCheckBox,
    QComboBox,
    QInputDialog,
    QGraphicsOpacityEffect,
)

from ConfigManager import (
    load_config,
    save_config,
    config_exists,
    is_config_complete,
)
from mailer import available_mail_programs, send_pdf_via_mail
from updater import check_for_update
from version import APP_VERSION

DATE_FORMAT = "dd.MM.yyyy"

ANIM_FAST = 160
ANIM_MEDIUM = 220


def fade_in_widget(widget, duration=ANIM_FAST):
    """Softly fade a widget in when it appears. Returns the animation."""
    effect = QGraphicsOpacityEffect(widget)
    widget.setGraphicsEffect(effect)

    animation = QPropertyAnimation(effect, b"opacity", widget)
    animation.setDuration(duration)
    animation.setStartValue(0.0)
    animation.setEndValue(1.0)
    animation.setEasingCurve(QEasingCurve.Type.OutCubic)
    # Effekt nach der Animation entfernen (vermeidet Render-Nebenwirkungen)
    animation.finished.connect(lambda: widget.setGraphicsEffect(None))
    animation.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
    return animation


def fade_in_window(window, duration=ANIM_MEDIUM):
    """Fade in a top-level window/dialog. Returns the animation."""
    animation = QPropertyAnimation(window, b"windowOpacity", window)
    animation.setDuration(duration)
    animation.setStartValue(0.0)
    animation.setEndValue(1.0)
    animation.setEasingCurve(QEasingCurve.Type.OutCubic)
    animation.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
    return animation


class UpdateCheckWorker(QThread):
    """Fragt die GitHub-Releases im Hintergrund ab, ohne die UI zu blockieren."""

    finished_check = pyqtSignal(object, object)  # (ergebnis, fehler)

    def run(self):
        try:
            self.finished_check.emit(check_for_update(), None)
        except Exception as error:
            self.finished_check.emit(None, error)


def show_update_dialog(parent, info):
    """Zeigt gefundene Updates an und öffnet auf Wunsch die Download-Seite."""
    notes = info.get("notes", "")
    if len(notes) > 600:
        notes = notes[:600] + "…"

    text = (
        f"Version {info['version']} ist verfügbar (installiert: {APP_VERSION})."
    )
    if notes:
        text += f"\n\nÄnderungen:\n{notes}"
    text += "\n\nDownload-Seite jetzt öffnen?"

    answer = QMessageBox.question(
        parent,
        "Update verfügbar",
        text,
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.Yes,
    )

    if answer == QMessageBox.StandardButton.Yes:
        QDesktopServices.openUrl(QUrl(info["url"]))


def make_date_edit(initial_text=""):
    """Create a QDateEdit with calendar popup, optionally preset from a dd.MM.yyyy string."""
    date_edit = QDateEdit()
    date_edit.setCalendarPopup(True)
    date_edit.setDisplayFormat(DATE_FORMAT)

    date = QDate.fromString(initial_text, DATE_FORMAT)
    date_edit.setDate(date if date.isValid() else QDate.currentDate())

    return date_edit


class RangeCalendar(QCalendarWidget):
    """Calendar that highlights a selected date range."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.range_start = None
        self.range_end = None

        self.setGridVisible(False)
        self.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)

    def paintCell(self, painter, rect, date):
        super().paintCell(painter, rect, date)

        start = self.range_start
        end = self.range_end if self.range_end is not None else self.range_start

        if start is not None and start <= date <= end:
            painter.save()
            painter.fillRect(rect, QColor(66, 133, 244, 70))
            painter.restore()


class DateRangeEdit(QWidget):
    """One field for a trip: pick departure and return in a single calendar popup.

    First click selects the departure date, second click the return date.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.start_date = QDate.currentDate()
        self.end_date = QDate.currentDate()

        self.display = QLineEdit()
        self.display.setReadOnly(True)
        self.display.setMinimumWidth(240)
        self.display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.display.setObjectName("rangeDisplay")

        self.open_button = QPushButton("Auswählen...")
        self.open_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.open_button.clicked.connect(self.open_popup)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.display)
        layout.addWidget(self.open_button)
        self.setLayout(layout)

        # Popup with the range calendar
        self.popup = QFrame(self, Qt.WindowType.Popup)
        self.popup.setObjectName("calendarPopup")
        self.popup.setFrameShape(QFrame.Shape.StyledPanel)
        self._popup_animation = None

        self.calendar = RangeCalendar()
        self.calendar.clicked.connect(self._on_date_clicked)

        self.hint_label = QLabel("Abreise anklicken, danach Rückreise.")
        self.hint_label.setObjectName("hintLabel")
        self.hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        popup_layout = QVBoxLayout()
        popup_layout.setContentsMargins(4, 4, 4, 4)
        popup_layout.addWidget(self.hint_label)
        popup_layout.addWidget(self.calendar)
        self.popup.setLayout(popup_layout)

        self._update_display()

    def open_popup(self):
        # Show the current selection; the next click starts a new one.
        self.calendar.range_start = self.start_date
        self.calendar.range_end = self.end_date
        self.calendar.setSelectedDate(self.start_date)
        self.calendar.updateCells()

        self.hint_label.setText("Abreise anklicken, danach Rückreise.")

        position = self.display.mapToGlobal(self.display.rect().bottomLeft())
        position += QPoint(0, 6)

        # Dezent einblenden: kurzer Fade + leichtes Hochgleiten
        self.popup.move(position + QPoint(0, 8))
        self.popup.setWindowOpacity(0.0)
        self.popup.show()

        slide = QPropertyAnimation(self.popup, b"pos", self.popup)
        slide.setDuration(ANIM_FAST)
        slide.setStartValue(position + QPoint(0, 8))
        slide.setEndValue(position)
        slide.setEasingCurve(QEasingCurve.Type.OutCubic)

        fade = QPropertyAnimation(self.popup, b"windowOpacity", self.popup)
        fade.setDuration(ANIM_FAST)
        fade.setStartValue(0.0)
        fade.setEndValue(1.0)

        self._popup_animation = (slide, fade)
        slide.start()
        fade.start()

    def _on_date_clicked(self, date):
        calendar = self.calendar

        selection_finished = (
            calendar.range_start is not None and calendar.range_end is not None
        )

        if calendar.range_start is None or selection_finished:
            # Start a new selection
            calendar.range_start = date
            calendar.range_end = None
            self.hint_label.setText("Jetzt die Rückreise anklicken.")
        else:
            # Complete the selection (swap if clicked backwards)
            if date < calendar.range_start:
                calendar.range_start, calendar.range_end = date, calendar.range_start
            else:
                calendar.range_end = date

            self.start_date = calendar.range_start
            self.end_date = calendar.range_end
            self._update_display()
            self.popup.hide()

        calendar.updateCells()

    def _update_display(self):
        self.display.setText(
            f"{self.start_date.toString(DATE_FORMAT)}  –  {self.end_date.toString(DATE_FORMAT)}"
        )


class OptionsDialog(QDialog):
    def __init__(self, config, parent=None):
        super().__init__(parent)

        self.config = dict(config)

        self.setWindowTitle("Optionen")
        self.resize(520, 380)
        self._appear_animation = None

        self.name_input = QLineEdit()
        self.name_input.setText(self.config.get("name", ""))

        self.initial_date_input = make_date_edit(self.config.get("date-init", ""))
        self.training_start_input = make_date_edit(self.config.get("date-ausb-anf", ""))
        self.training_end_input = make_date_edit(self.config.get("date-ausb-ende", ""))

        self.kilometers_input = QLineEdit()
        self.kilometers_input.setText(self.config.get("kilometers", ""))

        self.mail_to_input = QLineEdit()
        self.mail_to_input.setPlaceholderText("Empfänger für den Mail-Versand")
        self.mail_to_input.setText(self.config.get("mail-to", ""))

        self.mail_program_combo = QComboBox()
        self.mail_program_combo.addItem("– beim ersten Versand fragen –", "")
        for program in available_mail_programs():
            self.mail_program_combo.addItem(program, program)

        saved_program = self.config.get("mail-program", "")
        index = self.mail_program_combo.findData(saved_program)
        self.mail_program_combo.setCurrentIndex(index if index >= 0 else 0)

        self.pdf_root_input = QLineEdit()
        self.pdf_root_input.setReadOnly(True)
        self.pdf_root_input.setPlaceholderText("optional – Ablage nach Jahr/Monat")
        self.pdf_root_input.setText(self.config.get("pdf-root", ""))

        self.pdf_root_button = QPushButton("Durchsuchen...")
        self.pdf_root_button.clicked.connect(self.browse_pdf_root)

        pdf_root_layout = QHBoxLayout()
        pdf_root_layout.addWidget(self.pdf_root_input)
        pdf_root_layout.addWidget(self.pdf_root_button)

        self.output_path_input = QLineEdit()
        self.output_path_input.setReadOnly(True)
        self.output_path_input.setText(self.config.get("output_path", ""))

        self.output_path_button = QPushButton("Durchsuchen...")
        self.output_path_button.clicked.connect(self.browse_output_path)

        output_path_layout = QHBoxLayout()
        output_path_layout.addWidget(self.output_path_input)
        output_path_layout.addWidget(self.output_path_button)

        form_layout = QFormLayout()
        form_layout.addRow("Name:", self.name_input)
        form_layout.addRow("Erstanreise:", self.initial_date_input)
        form_layout.addRow("Ausbildungsbeginn:", self.training_start_input)
        form_layout.addRow("Ausbildungsende:", self.training_end_input)
        form_layout.addRow("Kilometer:", self.kilometers_input)
        form_layout.addRow("E-Mail-Empfänger:", self.mail_to_input)
        form_layout.addRow("Mail-Programm:", self.mail_program_combo)
        form_layout.addRow("PDF-Ordner:", pdf_root_layout)
        form_layout.addRow("Speicherpfad:", output_path_layout)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )

        self.update_button = QPushButton("Nach Updates suchen")
        self.update_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.update_button.clicked.connect(self.check_updates_clicked)

        version_label = QLabel(f"Version {APP_VERSION}")
        version_label.setObjectName("footerLabel")

        update_layout = QHBoxLayout()
        update_layout.addWidget(version_label)
        update_layout.addStretch()
        update_layout.addWidget(self.update_button)

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 16)
        layout.setSpacing(12)
        layout.addLayout(form_layout)
        layout.addLayout(update_layout)
        layout.addWidget(self.button_box)

        self.setLayout(layout)

        self.button_box.accepted.connect(self.validate_and_accept)
        self.button_box.rejected.connect(self.reject)

    def showEvent(self, event):
        super().showEvent(event)

        if self._appear_animation is None:
            self._appear_animation = fade_in_window(self)

    def browse_output_path(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Speicherort auswählen",
            self.output_path_input.text() or "Fahrtkostenerstattung_Familienheimfahrt.docx",
            "Word-Dokument (*.docx)"
        )

        if file_path:
            if not file_path.lower().endswith(".docx"):
                file_path += ".docx"

            self.output_path_input.setText(file_path)

    def browse_pdf_root(self):
        folder = QFileDialog.getExistingDirectory(
            self,
            "PDF-Ordner auswählen",
            self.pdf_root_input.text() or str(Path.home()),
        )

        if folder:
            self.pdf_root_input.setText(folder)

    def check_updates_clicked(self):
        self.update_button.setEnabled(False)
        self.update_button.setText("Suche…")

        try:
            info = check_for_update()
        except Exception as error:
            QMessageBox.warning(
                self,
                "Update-Prüfung fehlgeschlagen",
                f"GitHub konnte nicht erreicht werden:\n{error}",
            )
            return
        finally:
            self.update_button.setEnabled(True)
            self.update_button.setText("Nach Updates suchen")

        if info is None:
            QMessageBox.information(
                self,
                "Kein Update",
                f"Du verwendest bereits die aktuelle Version ({APP_VERSION}).",
            )
        else:
            show_update_dialog(self, info)

    def validate_and_accept(self):
        config = self.get_config()

        if not is_config_complete(config):
            QMessageBox.warning(
                self,
                "Unvollständige Optionen",
                "Bitte fülle alle Felder aus, bevor du speicherst."
            )
            return

        if self.training_end_input.date() < self.training_start_input.date():
            QMessageBox.warning(
                self,
                "Ungültige Daten",
                "Das Ausbildungsende liegt vor dem Ausbildungsbeginn."
            )
            return

        self.accept()

    def get_config(self):
        self.config["name"] = self.name_input.text().strip()
        self.config["date-init"] = self.initial_date_input.date().toString(DATE_FORMAT)
        self.config["date-ausb-anf"] = self.training_start_input.date().toString(DATE_FORMAT)
        self.config["date-ausb-ende"] = self.training_end_input.date().toString(DATE_FORMAT)
        self.config["kilometers"] = self.kilometers_input.text().strip()
        self.config["mail-to"] = self.mail_to_input.text().strip()
        self.config["mail-program"] = self.mail_program_combo.currentData() or ""
        self.config["pdf-root"] = self.pdf_root_input.text().strip()
        self.config["output_path"] = self.output_path_input.text().strip()

        return self.config


class FahrtkostenWindow(QWidget):
    def __init__(self, generate_document_callback):
        super().__init__()

        self.generate_document_callback = generate_document_callback
        self.is_first_launch = not config_exists()
        self.config = load_config()

        self.setWindowTitle("Fahrtkostenerstattung")
        self.resize(480, 220)

        self.one_trip_radio = QRadioButton("1 Fahrt")
        self.two_trips_radio = QRadioButton("2 Fahrten")
        self.one_trip_radio.setChecked(True)

        self.trip_group = QButtonGroup(self)
        self.trip_group.addButton(self.one_trip_radio)
        self.trip_group.addButton(self.two_trips_radio)

        radio_layout = QHBoxLayout()
        radio_layout.addWidget(self.one_trip_radio)
        radio_layout.addWidget(self.two_trips_radio)

        self.first_trip_range = DateRangeEdit()
        self.second_trip_range = DateRangeEdit()

        self.sick_note_checkbox = QCheckBox("Krankmeldung liegt vor")
        self.sick_note_range = DateRangeEdit()

        self.form_layout = QFormLayout()
        self.form_layout.addRow("1. Fahrt (Hin – Rück):", self.first_trip_range)
        self.form_layout.addRow("2. Fahrt (Hin – Rück):", self.second_trip_range)
        self.form_layout.addRow("", self.sick_note_checkbox)
        self.form_layout.addRow("Zeitraum Krankmeldung:", self.sick_note_range)

        self.create_button = QPushButton("Dokument erstellen")
        self.create_button.setObjectName("primaryButton")
        self.create_button.setCursor(Qt.CursorShape.PointingHandCursor)

        self.options_button = QPushButton("Optionen")
        self.options_button.setCursor(Qt.CursorShape.PointingHandCursor)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.options_button)
        button_layout.addWidget(self.create_button)

        footer_label = QLabel(f"© {QDate.currentDate().year()} Ricky Remm · v{APP_VERSION}")
        footer_label.setObjectName("footerLabel")
        footer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 12)
        main_layout.setSpacing(14)
        main_layout.addLayout(radio_layout)
        main_layout.addLayout(self.form_layout)
        main_layout.addLayout(button_layout)
        main_layout.addWidget(footer_label)

        self.setLayout(main_layout)

        self._appear_animation = None

        self.one_trip_radio.toggled.connect(self.toggle_second_trip_fields)
        self.sick_note_checkbox.toggled.connect(self.toggle_sick_note_fields)
        self.create_button.clicked.connect(self.create_document)
        self.options_button.clicked.connect(self.open_options)

        self.toggle_second_trip_fields()
        self.toggle_sick_note_fields()

        self._start_update_check()

        if self.is_first_launch or not is_config_complete(self.config):
            self.open_required_options()

    def _start_update_check(self):
        """Beim Start still im Hintergrund nach Updates suchen."""
        self._update_worker = UpdateCheckWorker(self)
        self._update_worker.finished_check.connect(self._on_update_check_done)
        self._update_worker.start()

    def _on_update_check_done(self, info, error):
        # Fehler beim stillen Check werden bewusst ignoriert (z. B. offline)
        if error is None and info:
            show_update_dialog(self, info)

    def showEvent(self, event):
        super().showEvent(event)

        if self._appear_animation is None:
            self._appear_animation = fade_in_window(self)

    def toggle_second_trip_fields(self):
        is_two_trips = self.two_trips_radio.isChecked()
        was_hidden = not self.second_trip_range.isVisible()

        self.form_layout.labelForField(self.second_trip_range).setVisible(is_two_trips)
        self.second_trip_range.setVisible(is_two_trips)

        if is_two_trips and was_hidden:
            self._second_trip_animation = fade_in_widget(self.second_trip_range)

    def toggle_sick_note_fields(self):
        has_sick_note = self.sick_note_checkbox.isChecked()
        was_hidden = not self.sick_note_range.isVisible()

        self.form_layout.labelForField(self.sick_note_range).setVisible(has_sick_note)
        self.sick_note_range.setVisible(has_sick_note)

        if has_sick_note and was_hidden:
            self._sick_note_animation = fade_in_widget(self.sick_note_range)

    def open_options(self):
        dialog = OptionsDialog(self.config, self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.config = dialog.get_config()
            save_config(self.config)

            QMessageBox.information(self, "Gespeichert", "Optionen wurden gespeichert.")

    def open_required_options(self):
        dialog = OptionsDialog(self.config, self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.config = dialog.get_config()
            save_config(self.config)

            QMessageBox.information(self, "Gespeichert", "Optionen wurden gespeichert.")
        else:
            QMessageBox.warning(
                self,
                "Optionen erforderlich",
                "Die Anwendung kann erst verwendet werden, wenn alle Optionen ausgefüllt wurden."
            )

    def validate_dates(self):
        """Check date plausibility. Returns an error message or None."""
        if self.two_trips_radio.isChecked():
            if self.second_trip_range.start_date < self.first_trip_range.end_date:
                return "Die 2. Fahrt darf nicht vor dem Ende der 1. Fahrt beginnen."

        return None

    def ask_mail_program(self):
        """Ask once which mail program to use and remember the choice."""
        programs = available_mail_programs()

        if not programs:
            return None

        choice, ok = QInputDialog.getItem(
            self,
            "Mail-Programm wählen",
            "Mit welchem Programm sollen die Mails verschickt werden?\n"
            "(Die Auswahl wird gespeichert und lässt sich in den Optionen ändern.)",
            programs,
            0,
            False,
        )

        if not ok or not choice:
            return None

        self.config["mail-program"] = choice
        save_config(self.config)
        return choice

    def offer_mail_send(self, pdf_path, date_from, date_to):
        message = "Dokument wurde erfolgreich erstellt.\nDOCX und PDF gespeichert."

        answer = QMessageBox.question(
            self,
            "Erfolg",
            message + "\n\nPDF jetzt per E-Mail verschicken?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        program = self.config.get("mail-program", "")
        if not program:
            program = self.ask_mail_program()
            if not program:
                return

        name = self.config.get("name", "")
        subject = "Fahrtkostenabrechnung"
        body = (
            "Guten Tag,\n\n"
            f"anbei die Fahrtkostenabrechnung für die Familienheimfahrt "
            f"im Zeitraum {date_from} – {date_to}.\n\n"
            f"Mit freundlichen Grüßen\n{name}"
        )

        opened = send_pdf_via_mail(
            pdf_path,
            self.config.get("mail-to", ""),
            subject,
            body,
            program,
        )

        if not opened:
            QMessageBox.warning(
                self,
                "Mail-Versand",
                f"Der Mail-Entwurf konnte nicht in {program} geöffnet werden.\n"
                "Die PDF liegt am eingestellten Speicherort und kann manuell verschickt werden."
            )

    def create_document(self):
        if not is_config_complete(self.config):
            QMessageBox.warning(
                self,
                "Optionen unvollständig",
                "Bitte fülle zuerst alle Optionen aus."
            )
            self.open_required_options()
            return

        date_error = self.validate_dates()
        if date_error:
            QMessageBox.warning(self, "Ungültige Daten", date_error)
            return

        hin = self.first_trip_range.start_date.toString(DATE_FORMAT)
        back = self.first_trip_range.end_date.toString(DATE_FORMAT)
        km = self.config.get("kilometers", "")

        hin1 = None
        back1 = None

        if self.two_trips_radio.isChecked():
            hin1 = self.second_trip_range.start_date.toString(DATE_FORMAT)
            back1 = self.second_trip_range.end_date.toString(DATE_FORMAT)

        krank = None
        if self.sick_note_checkbox.isChecked():
            krank = (
                self.sick_note_range.start_date.toString(DATE_FORMAT),
                self.sick_note_range.end_date.toString(DATE_FORMAT),
            )

        if not km:
            QMessageBox.warning(self, "Fehler", "Bitte Kilometer in den Optionen eingeben.")
            return

        try:
            pdf_path = self.generate_document_callback(
                hin,
                back,
                hin1,
                back1,
                km,
                self.config,
                krank=krank,
            )

            if pdf_path:
                self.offer_mail_send(pdf_path, hin, back1 or back)
            else:
                QMessageBox.information(
                    self,
                    "Hinweis",
                    "DOCX-Dokument wurde erstellt.\n"
                    "PDF-Konvertierung fehlgeschlagen (ist Microsoft Word installiert?)."
                )
        except Exception as error:
            QMessageBox.critical(
                self,
                "Fehler",
                f"Dokument konnte nicht erstellt werden:\n{error}"
            )
            print(error)
