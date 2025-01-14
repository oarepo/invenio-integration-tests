import json
import sys
from pathlib import Path

import yaml


def convert_forks_to_json(yaml_file: Path):
    data = yaml.safe_load(yaml_file.open())
    print(json.dumps(data, indent=2))


if __name__ == "__main__":
    convert_forks_to_json(Path(sys.argv[1]))
