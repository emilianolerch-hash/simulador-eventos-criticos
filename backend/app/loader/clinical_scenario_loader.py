from pathlib import Path
import yaml
from ..models.clinical_scenario import ClinicalScenarioSpec


class ClinicalScenarioLoadError(Exception):
    pass


def load_clinical_scenario(path: Path) -> ClinicalScenarioSpec:
    if not path.exists():
        raise ClinicalScenarioLoadError(f"Archivo no encontrado: {path}")
    with open(path, encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    try:
        return ClinicalScenarioSpec.model_validate(raw)
    except Exception as exc:
        raise ClinicalScenarioLoadError(
            f"Esquema clínico inválido en {path.name}: {exc}"
        ) from exc
