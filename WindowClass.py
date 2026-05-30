from PyQt6.QtCore import QDate
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
)
from PIL import Image
import os

from ConfigManager import load_config, save_config, config_exists, is_config_complete


class OptionsDialog(QDialog):
    def __init__(self, config, parent=None):
        super().__init__(parent)

        self.config = dict(config)

        self.setWindowTitle("Optionen")
        self.resize(520, 280)

        self.name_input = QLineEdit()
        self.name_input.setText(self.config.get("name", ""))

        self.initial_date_input = QLineEdit()
        self.initial_date_input.setText(self.config.get("date-init", ""))

        self.kilometers_input = QLineEdit()
        self.kilometers_input.setText(self.config.get("kilometers", ""))

        self.output_path_input = QLineEdit()
        self.output_path_input.setReadOnly(True)
        self.output_path_input.setText(self.config.get("output_path", ""))

        self.output_path_button = QPushButton("Durchsuchen...")
        self.output_path_button.clicked.connect(self.browse_output_path)

        output_path_layout = QHBoxLayout()
        output_path_layout.addWidget(self.output_path_input)
        output_path_layout.addWidget(self.output_path_button)

        self.signature_input = QLineEdit()
        self.signature_input.setReadOnly(True)
        signature_status = "Vorhanden" if os.path.exists("signatur.png") else "Nicht vorhanden"
        self.signature_input.setText(signature_status)

        self.signature_button = QPushButton("Durchsuchen...")
        self.signature_button.clicked.connect(self.browse_signature)

        signature_layout = QHBoxLayout()
        signature_layout.addWidget(self.signature_input)
        signature_layout.addWidget(self.signature_button)

        form_layout = QFormLayout()
        form_layout.addRow("Name:", self.name_input)
        form_layout.addRow("Erstanreise:", self.initial_date_input)
        form_layout.addRow("Kilometer:", self.kilometers_input)
        form_layout.addRow("Speicherpfad:", output_path_layout)
        form_layout.addRow("Signatur:", signature_layout)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )

        layout = QVBoxLayout()
        layout.addLayout(form_layout)
        layout.addWidget(self.button_box)

        self.setLayout(layout)

        self.button_box.accepted.connect(self.validate_and_accept)
        self.button_box.rejected.connect(self.reject)

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

    def browse_signature(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Signatur auswählen",
            "",
            "Bilddateien (*.png *.jpg *.jpeg *.bmp *.gif)"
        )

        if file_path:
            try:
                # Open and convert image to PNG format
                img = Image.open(file_path)
                # Save as signatur.png in the current directory
                img.save("signatur.png", "PNG")

                # Update the status display
                self.signature_input.setText("Vorhanden")

                QMessageBox.information(
                    self,
                    "Erfolg",
                    "Signatur wurde erfolgreich gespeichert."
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Fehler",
                    f"Signatur konnte nicht gespeichert werden:\n{e}"
                )

    def validate_and_accept(self):
        config = self.get_config()

        if not is_config_complete(config):
            QMessageBox.warning(
                self,
                "Unvollständige Optionen",
                "Bitte fülle alle Felder aus, bevor du speicherst."
            )
            return

        self.accept()

    def get_config(self):
        self.config["name"] = self.name_input.text().strip()
        self.config["date-init"] = self.initial_date_input.text().strip()
        self.config["kilometers"] = self.kilometers_input.text().strip()
        self.config["output_path"] = self.output_path_input.text().strip()

        return self.config


class FahrtkostenWindow(QWidget):
    def __init__(self, generate_document_callback):
        super().__init__()

        self.generate_document_callback = generate_document_callback
        self.is_first_launch = not config_exists()
        self.config = load_config()

        self.setWindowTitle("Fahrtkostenerstattung")
        self.resize(420, 300)

        self.one_trip_radio = QRadioButton("1 Fahrt")
        self.two_trips_radio = QRadioButton("2 Fahrten")
        self.one_trip_radio.setChecked(True)

        self.trip_group = QButtonGroup(self)
        self.trip_group.addButton(self.one_trip_radio)
        self.trip_group.addButton(self.two_trips_radio)

        radio_layout = QHBoxLayout()
        radio_layout.addWidget(self.one_trip_radio)
        radio_layout.addWidget(self.two_trips_radio)

        self.first_departure_date = QDateEdit()
        self.first_departure_date.setCalendarPopup(True)
        self.first_departure_date.setDate(QDate.currentDate())
        self.first_departure_date.setDisplayFormat("dd.MM.yyyy")

        self.first_return_date = QDateEdit()
        self.first_return_date.setCalendarPopup(True)
        self.first_return_date.setDate(QDate.currentDate())
        self.first_return_date.setDisplayFormat("dd.MM.yyyy")

        self.second_departure_date = QDateEdit()
        self.second_departure_date.setCalendarPopup(True)
        self.second_departure_date.setDate(QDate.currentDate())
        self.second_departure_date.setDisplayFormat("dd.MM.yyyy")

        self.second_return_date = QDateEdit()
        self.second_return_date.setCalendarPopup(True)
        self.second_return_date.setDate(QDate.currentDate())
        self.second_return_date.setDisplayFormat("dd.MM.yyyy")

        self.form_layout = QFormLayout()
        self.form_layout.addRow("Abreisedatum:", self.first_departure_date)
        self.form_layout.addRow("Rückreisedatum:", self.first_return_date)
        self.form_layout.addRow("Abreisedatum 2. Fahrt:", self.second_departure_date)
        self.form_layout.addRow("Rückreisedatum 2. Fahrt:", self.second_return_date)

        self.create_button = QPushButton("Dokument erstellen")
        self.options_button = QPushButton("Optionen")

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.options_button)
        button_layout.addWidget(self.create_button)

        main_layout = QVBoxLayout()
        main_layout.addLayout(radio_layout)
        main_layout.addLayout(self.form_layout)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

        self.one_trip_radio.toggled.connect(self.toggle_second_trip_fields)
        self.create_button.clicked.connect(self.create_document)
        self.options_button.clicked.connect(self.open_options)

        self.toggle_second_trip_fields()

        if self.is_first_launch or not is_config_complete(self.config):
            self.open_required_options()

    def toggle_second_trip_fields(self):
        is_two_trips = self.two_trips_radio.isChecked()

        self.form_layout.labelForField(self.second_departure_date).setVisible(is_two_trips)
        self.second_departure_date.setVisible(is_two_trips)

        self.form_layout.labelForField(self.second_return_date).setVisible(is_two_trips)
        self.second_return_date.setVisible(is_two_trips)

    def open_options(self):
        dialog = OptionsDialog(self.config, self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.config = dialog.get_config()
            save_config(self.config)

            QMessageBox.information(self, "Gespeichert", "Optionen wurden gespeichert.")

    def open_required_options(self):
        while not is_config_complete(self.config):
            dialog = OptionsDialog(self.config, self)

            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.config = dialog.get_config()
                save_config(self.config)

                QMessageBox.information(self, "Gespeichert", "Optionen wurden gespeichert.")
                return

            QMessageBox.warning(
                self,
                "Optionen erforderlich",
                "Die Anwendung kann erst verwendet werden, wenn alle Optionen ausgefüllt wurden."
            )
            return

    def create_document(self):
        if not is_config_complete(self.config):
            QMessageBox.warning(
                self,
                "Optionen unvollständig",
                "Bitte fülle zuerst alle Optionen aus."
            )
            self.open_required_options()
            return

        hin = self.first_departure_date.date().toString("dd.MM.yyyy")
        back = self.first_return_date.date().toString("dd.MM.yyyy")
        km = self.config.get("kilometers", "")

        hin1 = None
        back1 = None

        if self.two_trips_radio.isChecked():
            hin1 = self.second_departure_date.date().toString("dd.MM.yyyy")
            back1 = self.second_return_date.date().toString("dd.MM.yyyy")

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
                self.config
            )

            if pdf_path:
                QMessageBox.information(
                    self,
                    "Erfolg",
                    f"Dokument wurde erfolgreich erstellt.\nDOCX und PDF gespeichert."
                )
            else:
                QMessageBox.information(
                    self,
                    "Erfolg",
                    "DOCX-Dokument wurde erstellt.\nPDF-Konvertierung fehlgeschlagen (LibreOffice nicht installiert?)."
                )
        except Exception as error:
            QMessageBox.critical(
                self,
                "Fehler",
                f"Dokument konnte nicht erstellt werden:\n{error}"
            )
            print(error)