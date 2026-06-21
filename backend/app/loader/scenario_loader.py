from pathlib import Path
import yaml
from ..models.scenario import ScenarioDefinition


class ScenarioLoadError(Exception):
    pass


def load_scenario(path: Path) -> ScenarioDefinition:
    if not path.exists():
        raise ScenarioLoadError(f"Archivo no encontrado: {path}")
    with open(path, encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    try:
        return ScenarioDefinition.model_validate(raw)
    except Exception as exc:
        raise ScenarioLoadError(f"YAML inválido en {path.name}: {exc}") from exc


def load_all_scenarios(scenarios_dir: Path) -> dict[str, ScenarioDefinition]:
    result: dict[str, ScenarioDefinition] = {}
    for yaml_file in sorted(scenarios_dir.glob("*.yaml")):
        scenario = load_scenario(yaml_file)
        result[scenario.id] = scenario
    return result
