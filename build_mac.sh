#!/bin/bash
# Baut die macOS-App (dist/FKscript.app).
# Im Projektordner ausführen: ./build_mac.sh
set -e
cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

.venv/bin/python -m pip install --upgrade pip -q
.venv/bin/python -m pip install -r requirements.txt pyinstaller -q

.venv/bin/pyinstaller --noconfirm --clean --windowed --name FKscript \
    --add-data "Fahrtkostenerstattung_Familienheimfahrt.docx:." \
    main.py

echo ""
echo "Fertig: dist/FKscript.app"
