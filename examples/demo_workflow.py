"""Demo workflow using statesman."""

import json
from pathlib import Path

from statesman.core.base import Statesman, ManagedFile


class P1Step(Statesman):
    """Step 1: Interpolate parameters."""

    dependent_sections = ["geometry"]
    output_files = ["output.json", "output.vtu"]

    def _execute(self):
        output_json = self.workdir / "output.json"
        output_vtu = self.workdir / "output.vtu"
        with open(output_json, "w") as f:
            json.dump(self.config["geometry"], f)
        with open(output_vtu, "w") as f:
            f.write("Dummy VTU data")


class P2Step(Statesman):
    """Step 2: Mesh according to parameters."""

    input_files = [
        ManagedFile(name="output.json", non_empty=True, newer_than="config"),
        ManagedFile(name="output.vtu", non_empty=True, newer_than="config"),
    ]
    output_files = ["output2.json"]
    dependent_sections = ["geometry"]

    def _execute(self):
        output_json2 = self.workdir / "output2.json"
        with open(output_json2, "w") as f:
            json.dump({"meshed": True}, f)


# Medium complex demo
if __name__ == "__main__":
    workdir = Path(__file__).parent / "demo_dir"
    workdir.mkdir(exist_ok=True)
    config_path = Path(__file__).parent / "sample_config.yaml"
    p1 = P1Step(str(workdir), str(config_path))
    p1.run()
    p2 = P2Step(str(workdir), str(config_path))
    p2.run()
