# Sabueso — Public API (Conceptual)

## Core Objects
- **Card**: single entity representation with evidence.
- **Deck**: collection of Cards with consistent operations.

Users can choose to operate on a single Card or a Deck.

## Ops (Internal, Consistent Semantics)
Ops are methods on Card/Deck with predictable behavior.

Examples:
- CardOps: `compare`, `extract`, `expand`, `to_deck`.
- DeckOps: `filter`, `sort`, `compare`, `map`, `reduce`.

## Tools (Public, Heterogeneous)
Tools are standalone functions grouped by module:
- `tools.db.*`: per‑database modules
- `tools.card.*`: tools operating on Card
- `tools.deck.*`: tools operating on Deck

Tools are **ad‑hoc by design** and can return any output type.

## Mixed API Style
The public API is mixed OO + functional:
- Cards/Decks expose ops as methods.
- Tools are standalone functions.

