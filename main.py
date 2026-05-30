import sys
import platform
import subprocess
from datetime import datetime
from pathlib import Path

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


def convert_docx_to_pdf_windows(docx_path):
    """Convert DOCX to PDF using MS Word COM on Windows."""
    try:
        import win32com.client
        
        docx_path = Path(docx_path).absolute()
        pdf_path = docx_path.with_suffix('.pdf')
        
        print(f"Converting: {docx_path} -> {pdf_path}")
        
        # Create Word application
        word = win32com.client.Dispatch("Word.Application")
        word.Visible = False
        
        # Open document
        doc = word.Documents.Open(str(docx_path))
        
        # Save as PDF (FileFormat=17 is wdFormatPDF)
        doc.SaveAs(str(pdf_path), FileFormat=17)
        
        # Close document and Word
        doc.Close()
        word.Quit()
        
        print(f"PDF created successfully: {pdf_path}")
        return str(pdf_path)
    except ImportError as e:
        print(f"pywin32 not installed: {e}")
        return None
    except Exception as e:
        print(f"Windows PDF conversion failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def convert_docx_to_pdf_mac(docx_path):
    """Convert DOCX to PDF using MS Word AppleScript on macOS."""
    try:
        docx_path = Path(docx_path).absolute()
        pdf_path = docx_path.with_suffix('.pdf')
        
        print(f"Converting: {docx_path} -> {pdf_path}")
        
        # AppleScript to control MS Word
        applescript = f'''
        tell application "Microsoft Word"
            activate
            set theDoc to open POSIX file "{docx_path}"
            save as theDoc file name "{pdf_path}" file format format PDF
            close theDoc saving no
        end tell
        '''
        
        # Execute AppleScript
        result = subprocess.run(
            ["osascript", "-e", applescript],
            check=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0 and pdf_path.exists():
            print(f"PDF created successfully: {pdf_path}")
            return str(pdf_path)
        else:
            print(f"AppleScript stderr: {result.stderr}")
            print(f"AppleScript stdout: {result.stdout}")
            return None
            
    except subprocess.TimeoutExpired:
        print("PDF conversion timed out")
        return None
    except subprocess.CalledProcessError as e:
        print(f"AppleScript failed: {e.stderr}")
        return None
    except Exception as e:
        print(f"macOS PDF conversion failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def convert_docx_to_pdf_mac(docx_path):
    """Convert DOCX to PDF using MS Word AppleScript on macOS."""
    try:
        # Check if Word is installed
        check_word = subprocess.run(
            ["osascript", "-e", 'tell application "System Events" to return name of processes'],
            capture_output=True,
            text=True
        )

        # Try different Word app names
        word_apps = [
            "Microsoft Word",
            "Word",
            "/Applications/Microsoft Word.app"
        ]

        word_app = None
        for app in word_apps:
            test_script = f'tell application "{app}" to return name'
            result = subprocess.run(
                ["osascript", "-e", test_script],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                word_app = app
                print(f"Found Word app: {word_app}")
                break

        if not word_app:
            print("Microsoft Word not found on this system")
            return None

        docx_path = Path(docx_path).absolute()
        pdf_path = docx_path.with_suffix('.pdf')

        print(f"Converting: {docx_path} -> {pdf_path}")

        # Simpler AppleScript approach
        applescript = f'''
        tell application "{word_app}"
            open POSIX file "{docx_path}"
            set theDoc to active document
            save as theDoc file name "{pdf_path}" file format format PDF
            close theDoc saving no
            quit
        end tell
        '''

        result = subprocess.run(
            ["osascript", "-e", applescript],
            capture_output=True,
            text=True,
            timeout=30
        )

        if pdf_path.exists():
            print(f"PDF created successfully: {pdf_path}")
            return str(pdf_path)
        else:
            print(f"PDF file not created. Check console for errors.")
            print(f"stderr: {result.stderr}")
            print(f"stdout: {result.stdout}")
            return None

    except Exception as e:
        print(f"macOS PDF conversion failed: {e}")
        import traceback
        traceback.print_exc()
        return None


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
    print(f"DOCX saved to: {output_path}")
    
    # Convert to PDF
    pdf_path = convert_docx_to_pdf_mac(output_path)
    return pdf_path


def main():
    app = QApplication(sys.argv)

    window = FahrtkostenWindow(generate_document)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()