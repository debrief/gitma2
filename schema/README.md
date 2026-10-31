# Schema

`tma.yaml` is the single source of truth for every persisted data type (constitution I), carried
unchanged from gitma (schema 0.16.0) so that files are interchangeable between the repositories.

Regenerate after any edit, and bump `version:`:

```bash
uv run python scripts/gen_types.py          # Pydantic models + JSON Schema into src/tma2/types/generated/
uv run python scripts/gen_types.py --check  # what CI runs: fails if the committed output is stale
uv run python scripts/data_dictionary.py    # site/docs/data-dictionary.md (the site's prebuild runs it)
```
