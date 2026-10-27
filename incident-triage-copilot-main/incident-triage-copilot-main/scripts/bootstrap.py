from __future__ import annotations

from src.classification.train import train_model
from src.config import settings
from src.data.generate import generate_incidents, generate_runbooks


def main() -> None:
    generate_incidents(settings.incident_path)
    generate_runbooks(settings.runbook_path)
    report = train_model()
    print(f"Bootstrap complete. Classifier accuracy: {report['accuracy']:.3f}")


if __name__ == "__main__":
    main()
