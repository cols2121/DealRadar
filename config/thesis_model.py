from pydantic import BaseModel
from pathlib import Path
import yaml


class ThesisConfig(BaseModel):
    stage: str
    geography: list[str]
    must_have: list[str]
    bonus: list[str]
    exclude: list[str]
    notes: str = ""


def load_thesis(path: Path = Path("config/thesis.yaml")) -> ThesisConfig:
    data = yaml.safe_load(path.read_text())
    return ThesisConfig(**data["thesis"])
