from app.utils.file_utils import read_file

def open_file(args):
    try:
        content = read_file(args.file)
        print(content)
    except FileNotFoundError:
        print(f"Datei nicht gefunden: {args.file}")