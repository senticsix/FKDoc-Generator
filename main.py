import sys
from datetime import datetime

from docx import Document
from docx.shared import Cm
from PyQt6.QtWidgets import QApplication

from WindowClass import FahrtkostenWindow


def find_and_replace(doc, old_text, new_text):
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    if old_text in paragraph.text:
                        paragraph.text = paragraph.text.replace(old_text, new_text)


def replace_text_with_image(doc, placeholder, image_path, width=Cm(2.0)):
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    if placeholder in paragraph.text:
                        paragraph.text = paragraph.text.replace(placeholder, "")

                        run = paragraph.add_run()
                        run.add_picture(image_path, width=width)


def generate_document(
    hin,
    back,
    hin1=None,
    back1=None,
    km="",
    config=None
):
    if config is None:
        config = {}

    curr_date = datetime.today().strftime("%d.%m.%Y")

    if hin1 is None:
        datum = hin + " - " + back
    else:
        datum = hin + " - " + back1

    output_path = config.get(
        "output_path",
        "/Users/rickyremm/Desktop/Fahrtkostenerstattung_Familienheimfahrt.docx"
    )

    document = Document("Fahrtkostenerstattung_Familienheimfahrt.docx")

    find_and_replace(document, "{DATUM}", datum)
    find_and_replace(document, "{DATUM_HIN}", hin)
    find_and_replace(document, "{DATUM_BACK}", back)
    find_and_replace(document, "{KM}", km)
    find_and_replace(document, "{SIG_DATE}", curr_date)

    find_and_replace(document, "{NAME}", config.get("name", ""))
    find_and_replace(document, "{DATUM_ERSTANR}", config.get("date-init", ""))
    replace_text_with_image(document, "{SIGNATURE}", "signatur.png")

    if hin1 is None:
        find_and_replace(document, "{DATUM_HIN1}", "")
        find_and_replace(document, "{DATUM_BACK1}", "")
    else:
        find_and_replace(document, "{DATUM_HIN1}", hin1)
        find_and_replace(document, "{DATUM_BACK1}", back1)

    document.save(output_path)


def main():
    app = QApplication(sys.argv)

    window = FahrtkostenWindow(generate_document)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()