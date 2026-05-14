# Read the Docs Setup

This repository is ready to build on Read the Docs using MkDocs Material.

## Files Used by Read the Docs

- `.readthedocs.yaml` selects the Read the Docs build image, Python version, MkDocs builder, and documentation dependency file.
- `mkdocs.yml` defines the site metadata, navigation, theme, Markdown extensions, and API reference generation.
- `docs/requirements.txt` lists the Python packages needed only for the documentation build.
- `docs/gen_ref_pages.py` generates API reference pages from Python modules under `src/`.
- `docs/*.md` contains the hand-written documentation pages.

## Import the Project

1. Go to Read the Docs.
2. Choose **Import a Project**.
3. Connect or select the GitHub repository:

   ```text
   https://github.com/MShirazAhmad/IndentAnalyzer
   ```

4. Select the branch you want Read the Docs to build. For current development documentation, use:

   ```text
   indevelopment
   ```

5. Keep the default configuration-file path:

   ```text
   .readthedocs.yaml
   ```

6. Trigger a build.

## Expected Build Command

Read the Docs will install `docs/requirements.txt` and run MkDocs using `mkdocs.yml`. Locally, the equivalent command is:

```bash
python -m pip install -r docs/requirements.txt
mkdocs build --clean --strict
```

## API Reference

The API reference is generated automatically during the MkDocs build. You do not need to commit generated files under `docs/reference/`; they are created at build time by `docs/gen_ref_pages.py`.

## Notes

- The documentation build does not need to run the PyQt GUI.
- Sample data files remain in the repository for user workflows, but generated local outputs such as offset CSV files are ignored.
- If new Python modules are added under `src/`, they are automatically included in the generated API reference.

