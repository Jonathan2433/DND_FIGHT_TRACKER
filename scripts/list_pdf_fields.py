"""Liste les noms de champs d'un PDF fillable DnD5."""
from __future__ import annotations

import argparse
from pathlib import Path

from pypdf import PdfReader


def main() -> int:
    parser = argparse.ArgumentParser(description="Lister les champs d'un formulaire PDF")
    parser.add_argument("pdf_path", type=Path, help="Chemin du PDF fillable")
    args = parser.parse_args()

    reader = PdfReader(str(args.pdf_path))
    fields = reader.get_fields() or {}
    for key in sorted(fields.keys()):
        print(key)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
