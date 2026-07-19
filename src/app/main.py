import argparse
import json

from app.commands.run import run


def main():
    parser = argparse.ArgumentParser(
        description="Wissensgraph-Extraktions-Pipeline"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # run als einziger Subcommand
    run_parser = subparsers.add_parser("run", help="Experiment aus Registry laden und Tripel generieren")
    run_parser.add_argument("expId", help="Experiment-ID aus der Registry (z.B. clean_00)")
    run_parser.add_argument("-o","--output_dir",type=str,default=None, help="Optionales Verzeichnis zum Speichern der Ergebnisse")
    run_parser.set_defaults(func=run)

    args = parser.parse_args()
    result = args.func(args, output_dir=args.output_dir)
    if result is not None:
        if isinstance(result, (dict, list)):
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()