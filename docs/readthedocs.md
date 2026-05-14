# Publishing

This page is for maintainers who publish the documentation site. Regular users can start with Installation, Features, Code Workflow, Calculations, Function Reference, and Code Reference.

## Read the Docs Build

The documentation is built with MkDocs Material and published by Read the Docs from the GitHub repository:

```text
https://github.com/MShirazAhmad/IndentAnalyzer
```

The current development documentation branch is:

```text
indevelopment
```

When that branch is connected in Read the Docs, pushing a documentation commit can trigger a new hosted build.

## Local Check Before Publishing

Before pushing documentation changes, run:

```bash
python -m pip install -r docs/requirements.txt
mkdocs build --clean --strict
```

The generated HTML is written to:

```text
site/
```

The `site/` directory is a build output and does not need to be committed.

## Source Code Reference

The Code Reference is generated during the MkDocs build from the Python files under `src/`. This keeps the published documentation synchronized with the actual code on the branch being built.

When a new Python module is added under `src/`, it is automatically included in the generated Code Reference during the next documentation build.

## Maintainer Notes

- The documentation build does not need to launch the PyQt GUI.
- Hand-written pages live under `docs/`.
- The generated Code Reference is created at build time, so generated `docs/reference/` files should not be committed.
- Math equations are rendered by MathJax through the MkDocs configuration.
