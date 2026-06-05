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
    run_parser.set_defaults(func=run)

    args = parser.parse_args()
    result = args.func(args)
    if result is not None:
        if isinstance(result, (dict, list)):
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(result)


if __name__ == "__main__":
    main()