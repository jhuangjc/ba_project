import json
from app.utils.io import PROJECT_ROOT, read_file, load_input_files
REGISTRY_PATH = PROJECT_ROOT / "data/registry/registry.json"
def run(args):
    ex_id = args.expId
    registry_data = json.loads(read_file(REGISTRY_PATH))
    experiments =registry_data["experiments"]
    exp = None
    for e in experiments:

        if (e["experiment_id"] == ex_id):
            exp=e
            break
    if exp is None:
        raise ValueError( f"{ex_id} nicht in der Registry")
    # lade den input test 
    input_files = load_input_files(exp)

    # generiere die Tripel

    #checkpoint