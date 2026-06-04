from app.utils.io import read_file
from pathlib import Path
def open_file(args):

    file_path = Path(args.file)
    if not file_path.exists():
        raise ValueError(f"Datei nicht gefunden: {args.file}")
    if not file_path.is_file():
        raise ValueError(f"Keine gültige Datei: {args.file}")
    content = read_file(file_path)
    return content


