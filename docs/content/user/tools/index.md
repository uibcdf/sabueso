# Tools

Tools are the functions around cards and decks:

- **DB tools**: raw source records through `sabueso.tools.db.<source>.get_*`
  ({doc}`db/sources`), and the offline card builders for saved records. The online
  builders and `fetch_*_json` are deprecated in favour of `sabueso.resolve` and `get_*`
  ({doc}`/content/user/upgrading`).
- **Card and Deck tools**: saving and loading cards and decks as JSON, JSONL and SQLite
  files. For cards you will cite, prefer the knowledge store ({doc}`/content/user/storage`).

```{toctree}
:maxdepth: 2

card/index
deck/index
db/index
```
