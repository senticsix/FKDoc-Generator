"""Mail-Versand der erzeugten PDF über das vom Nutzer gewählte Mail-Programm.

Es wird immer nur ein Entwurf mit Anhang geöffnet - gesendet wird von Hand.
"""

import os
import platform
import subprocess
from pathlib import Path

APPLE_MAIL = "Apple Mail"
OUTLOOK = "Microsoft Outlook"
THUNDERBIRD = "Thunderbird"


def available_mail_programs():
    """Mail programs selectable on this platform."""
    system = platform.system()

    if system == "Darwin":
        return [APPLE_MAIL, OUTLOOK, THUNDERBIRD]

    if system == "Windows":
        return [OUTLOOK, THUNDERBIRD]

    return []


def send_pdf_via_mail(pdf_path, recipient="", subject="", body="", program=""):
    """Open a mail draft with the PDF attached in the chosen mail program."""
    system = platform.system()

    if program == THUNDERBIRD:
        return _send_thunderbird(pdf_path, recipient, subject, body)

    if system == "Darwin":
        if program == OUTLOOK:
            return _send_outlook_mac(pdf_path, recipient, subject, body)
        return _send_apple_mail(pdf_path, recipient, subject, body)

    if system == "Windows":
        return _send_outlook_windows(pdf_path, recipient, subject, body)

    print(f"Mail-Versand wird auf {system} nicht unterstützt.")
    return False


def _applescript_escape(text):
    return str(text).replace("\\", "\\\\").replace('"', '\\"')


def _run_applescript(script):
    result = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True,
        text=True,
        timeout=30,
    )

    if result.returncode != 0:
        print(f"AppleScript-Fehler: {result.stderr}")
        return False

    return True


def _send_apple_mail(pdf_path, recipient, subject, body):
    try:
        pdf_path = Path(pdf_path).absolute()

        recipient_line = ""
        if recipient:
            recipient_line = (
                'make new to recipient at end of to recipients '
                f'with properties {{address:"{_applescript_escape(recipient)}"}}'
            )

        script = f'''
        tell application "Mail"
            set newMessage to make new outgoing message with properties {{subject:"{_applescript_escape(subject)}", content:"{_applescript_escape(body)}" & linefeed & linefeed, visible:true}}
            tell newMessage
                {recipient_line}
                make new attachment with properties {{file name:POSIX file "{_applescript_escape(pdf_path)}"}} at after the last paragraph
            end tell
            activate
        end tell
        '''

        return _run_applescript(script)
    except Exception as e:
        print(f"Mail-Versand (Apple Mail) fehlgeschlagen: {e}")
        return False


def _send_outlook_mac(pdf_path, recipient, subject, body):
    try:
        pdf_path = Path(pdf_path).absolute()

        recipient_line = ""
        if recipient:
            recipient_line = (
                f'make new recipient at newMessage with properties '
                f'{{email address:{{address:"{_applescript_escape(recipient)}"}}}}'
            )

        script = f'''
        tell application "Microsoft Outlook"
            set newMessage to make new outgoing message with properties {{subject:"{_applescript_escape(subject)}", plain text content:"{_applescript_escape(body)}"}}
            {recipient_line}
            make new attachment at newMessage with properties {{file:POSIX file "{_applescript_escape(pdf_path)}"}}
            open newMessage
            activate
        end tell
        '''

        return _run_applescript(script)
    except Exception as e:
        print(f"Mail-Versand (Outlook/macOS) fehlgeschlagen: {e}")
        return False


def _send_outlook_windows(pdf_path, recipient, subject, body):
    try:
        import win32com.client

        pdf_path = Path(pdf_path).absolute()

        outlook = win32com.client.Dispatch("Outlook.Application")
        mail = outlook.CreateItem(0)  # 0 = MailItem

        if recipient:
            mail.To = recipient
        mail.Subject = subject
        mail.Body = body
        mail.Attachments.Add(str(pdf_path))

        mail.Display()
        return True
    except ImportError:
        print("pywin32 nicht installiert - Outlook-Versand nicht möglich.")
        return False
    except Exception as e:
        print(f"Mail-Versand (Outlook/Windows) fehlgeschlagen: {e}")
        return False


def _thunderbird_executable():
    system = platform.system()

    if system == "Darwin":
        candidates = [
            Path("/Applications/Thunderbird.app/Contents/MacOS/thunderbird"),
            Path.home() / "Applications" / "Thunderbird.app" / "Contents" / "MacOS" / "thunderbird",
        ]
    else:
        program_dirs = [
            os.environ.get("ProgramFiles", r"C:\Program Files"),
            os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"),
            os.environ.get("LOCALAPPDATA", ""),
        ]
        candidates = [
            Path(d) / "Mozilla Thunderbird" / "thunderbird.exe"
            for d in program_dirs
            if d
        ]

    return next((c for c in candidates if c.exists()), None)


def _send_thunderbird(pdf_path, recipient, subject, body):
    try:
        executable = _thunderbird_executable()

        if executable is None:
            print("Thunderbird wurde nicht gefunden.")
            return False

        pdf_path = Path(pdf_path).absolute()

        def clean(text):
            # Zeichen entschärfen, die die -compose-Syntax brechen würden
            return str(text).replace("'", "’").replace("\n", "\\n")

        compose = (
            f"to='{clean(recipient)}',"
            f"subject='{clean(subject)}',"
            f"body='{clean(body)}',"
            f"attachment='{pdf_path.as_uri()}'"
        )

        subprocess.Popen([str(executable), "-compose", compose])
        return True
    except Exception as e:
        print(f"Mail-Versand (Thunderbird) fehlgeschlagen: {e}")
        return False
