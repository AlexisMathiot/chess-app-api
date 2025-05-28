"""
Script pour vérifier et améliorer la qualité du code
Usage: python scripts/quality.py [--check] [--fix]
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], description: str, check_only: bool = False) -> bool:
    """Exécute une commande et affiche le résultat"""
    print(f"🔍 {description}...")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)

        if result.returncode == 0:
            print(f"✅ {description} - OK")
            return True
        print(f"❌ {description} - Erreurs détectées")
        if result.stdout:
            print("STDOUT:", result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return False

    except FileNotFoundError:
        print(f"❌ {description} - Commande non trouvée: {cmd[0]}")
        return False


def main():
    """Fonction principale"""
    check_only = "--check" in sys.argv
    fix_issues = "--fix" in sys.argv or not check_only

    # Vérifier qu'on est dans un projet Python
    if not Path("pyproject.toml").exists():
        print("❌ Fichier pyproject.toml non trouvé!")
        sys.exit(1)

    success = True

    # Black
    if check_only:
        success &= run_command(["black", "--check", "."], "Black (vérification)")
    else:
        success &= run_command(["black", "."], "Black (formatage)")

    # isort
    if check_only:
        success &= run_command(["isort", "--check-only", "."], "isort (vérification)")
    else:
        success &= run_command(["isort", "."], "isort (tri des imports)")

    # Ruff
    if fix_issues:
        success &= run_command(
            ["ruff", "check", ".", "--fix"],
            "Ruff (linting + correction)",
        )
    else:
        success &= run_command(["ruff", "check", "."], "Ruff (linting)")

    # mypy
    success &= run_command(["mypy", "."], "mypy (vérification des types)")

    if success:
        print("\n🎉 Toutes les vérifications sont passées!")
        sys.exit(0)
    else:
        print("\n❌ Des problèmes ont été détectés")
        sys.exit(1)


if __name__ == "__main__":
    main()
