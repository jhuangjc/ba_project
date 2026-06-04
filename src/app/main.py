import argparse
import json

from app.commands.file_commands import open_file
from app.commands.triple_generator import gen_triples
from app.commands.run import run
# constants

#hilfasfunktionen



def main():
    parser = argparse.ArgumentParser()
    #adding subparsers
    subparsers = parser.add_subparsers(dest="command", required = True)
    # parent parser fuer files
    file_parser = argparse.ArgumentParser(add_help = False)
    file_parser.add_argument("file", help = "Path to the file") 

    #open befehl
    open_parser = subparsers.add_parser("open", parents = [file_parser], help =" Öffnet eine Datei und printet sie in der Konsole")
    open_parser.set_defaults(func = open_file)

    #generate befehl
    generate_parser = subparsers.add_parser("generate", parents = [file_parser], help = "Generiert Tripel aus einer Inputdatei und printet sie in der Konsolse")
    generate_parser.set_defaults(func =  gen_triples)
    # neuer befahler: run
    # weitere funktionen werden später hinzugefügt.
    run_parser = subparsers.add_parser("run", help = "Geniert das Experiment setup basierend auf die Exp_id aus")
    run_parser.add_argument("expId", required = True, help ="Hier die Exp id eingeben")
    run_parser.set_defaults(func = run)

    #paerse cli input zu args
    args = parser.parse_args()
    #funktionsaufruf
    #catcht den case wenn kein gültiger Subcommand bzw. keine zugehörige Funktion vorhanden
    result = args.func(args)
    if result is not None:
        if isinstance(result, (dict, list)):
            print(json.dumps(result, ensure_ascii = False, indent = 2))
        else:
            print(result)


if __name__ == "__main__":
    main()