"""Demo workflow using statesman."""

import json
from pathlib import Path

from statesman.core.base import Statesman
from statesman.models.state import FileState


class P1Step(Statesman):
    """Step 1: Interpolate parameters."""

    def run(self):
        output_json = self.workdir / "output.json"
        output_vtu = self.workdir / "output.vtu"
        if not output_json.exists():
            with open(output_json, "w") as f:
                json.dump(self.config["geometry"], f)
            with open(output_vtu, "w") as f:
                f.write("Dummy VTU data")
        self.save_state(
            "geometry", self.has_section_changed("geometry")
        )  # Actually save hash


class P2Step(Statesman):
    """Step 2: Mesh according to parameters."""

    def validate(self):
        json_path = self.workdir / "output.json"
        vtu_path = self.workdir / "output.vtu"
        state = FileState(path=json_path, newer_than=self.config_path)
        self.validate_state(state)
        state = FileState(path=vtu_path, newer_than=self.config_path)
        self.validate_state(state)

    def run(self):
        self.validate()
        output_json2 = self.workdir / "output2.json"
        if not output_json2.exists() or self.has_section_changed("geometry"):
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
