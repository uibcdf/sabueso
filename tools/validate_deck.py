"""Validate a Deck (list of card dicts) against the formal YAML schema."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import json

from validate_card import validate_card


def validate_deck(cards: List[Dict[str, Any]]) -> List[str]:
    errors: List[str] = []
    for i, card in enumerate(cards):
        card_errors = validate_card(card)
        for err in card_errors:
            errors.append(f"card[{i}]: {err}")
    return errors


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("path", help="Path to deck JSONL file")
    args = parser.parse_args()

    cards: List[Dict[str, Any]] = []
    for line in Path(args.path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        cards.append(json.loads(line))

    errors = validate_deck(cards)
    if errors:
        print("Invalid deck:")
        for err in errors:
            print("-", err)
        raise SystemExit(1)
    print("OK: deck matches schema (basic)")


if __name__ == "__main__":
    main()
