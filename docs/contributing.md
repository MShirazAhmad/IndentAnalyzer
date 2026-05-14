# Contributing to the documentation

## Documentation governance

This repository now separates the short project landing page from the full documentation set.

### Keep in `README.md`

- project summary,
- quick install and launch pointers,
- links into the docs set.

### Keep in the Read the Docs content under `/home/runner/work/IndentAnalyzer/IndentAnalyzer/docs`

- the full end-user workflow,
- equations and reporting guidance,
- configuration details,
- developer architecture and API notes.

## Source alignment rules

When changing the application, update docs whenever you change:

- workflow steps or tab names,
- result-table columns,
- default thresholds or fitting settings,
- calibration assumptions,
- launch commands,
- exported result behavior.

## Scope rules

- Treat `README.md` and active code under `src/` as the documentation baseline.
- Do not treat `dump/` as current product documentation unless content is intentionally restored.

## Local docs build

Install the docs toolchain and build locally:

```bash
python -m pip install -r docs/requirements.txt -r requirements.txt
sphinx-build -b html docs docs/_build/html
```

## Review checklist

Before publishing docs updates:

- build the docs locally,
- verify screenshots render,
- verify math renders correctly,
- verify internal links resolve,
- verify developer references still match the active code.
