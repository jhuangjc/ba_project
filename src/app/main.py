import argparse
import json

from app.commands.file_commands import open_file
from app.commands.triple_generator import gen_triples
# constants

#hilfasfunktionen



def main():
    parser = argparse.ArgumentParser()
    #adding subparsers
    subparsers = parser.add_subparsers(dest="command")
    
    #open befehl
    open_parser = subparsers.add_parser("open")
    open_parser.add_argument("file")
    open_parser.set_defaults(func=open_file)

    #generate befehl
    generate_parser = subparsers.add_parser("generate")
    generate_parser.add_argument("file")
    generate_parser.set_defaults(func=gen_triples)
    #paerse cli input zu args
    args = parser.parse_args()
    #funktionsaufruf
    #catcht den case wenn kein gültiger Subcommand bzw. keine zugehörige Funktion vorhanden
    if hasattr(args, "func"):
        result = args.func(args)
        if result is not None:
            if isinstance(result, (dict, list)):
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                print(result)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()