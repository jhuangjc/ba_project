import argparse
from app.commands.file_commands import open_file
# constants

#hilfasfunktionen



def main():
    parser = argparse.ArgumentParser()
    #adding subparsers
    subparsers = parser.add_subparsers(dest="command")
    
    #files befehl
    file_parser = subparsers.add_parser("open")
    file_parser.add_argument("file")
    file_parser.set_defaults(func=open_file)
    #paerse cli input zu args
    args = parser.parse_args()
    #funktionsaufruf
    #catcht den case wenn kein gültiger Subcommand bzw. keine zugehörige Funktion vorhanden
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()