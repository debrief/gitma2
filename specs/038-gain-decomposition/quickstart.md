# Quickstart: spec 038

```bash
uv run pytest -q tests/unit/test_headroom_edit.py tests/unit/test_regress_decomp.py
uv run python scripts/research/gd_plan.py --stage dev-a      # writes configs/headroom/gd-dev-a-*.json
git push origin HEAD:headroom/gd-dev-a                        # runs headroom.yml
uv run python scripts/research/gd_tables.py --record experiments/<record>
```
