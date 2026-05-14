from pathlib import Path

import mkdocs_gen_files


nav = mkdocs_gen_files.Nav()
source_root = Path("src")


for path in sorted(source_root.rglob("*.py")):
    module_path = path.relative_to(source_root).with_suffix("")
    parts = list(module_path.parts)

    if not parts:
        continue

    if parts[-1] == "__init__":
        parts = parts[:-1]
        if not parts:
            continue
        doc_path = Path("reference", *parts, "index.md")
    else:
        doc_path = Path("reference", *parts).with_suffix(".md")

    ident = ".".join(parts)
    nav[parts] = doc_path.relative_to("reference").as_posix()

    with mkdocs_gen_files.open(doc_path, "w") as fd:
        fd.write(f"# `{ident}`\n\n")
        fd.write(f"::: {ident}\n")

    mkdocs_gen_files.set_edit_path(doc_path, path)


with mkdocs_gen_files.open("reference/index.md", "w") as index_file:
    index_file.write("# Code Reference\n\n")
    index_file.write(
        "The pages in this section are generated from the Python modules under `src/`.\n"
    )


with mkdocs_gen_files.open("reference/SUMMARY.md", "w") as nav_file:
    nav_file.writelines(nav.build_literate_nav())
