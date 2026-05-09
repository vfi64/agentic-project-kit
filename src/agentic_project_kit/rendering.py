from pathlib import Path
from string import Template


def render_template_string(template: str, context: dict[str, str]) -> str:
    return Template(template).safe_substitute(context)


def write_file(path: Path, content: str, overwrite: bool = False) -> None:
    if path.exists() and not overwrite:
        raise FileExistsError(f"Refusing to overwrite existing file: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.lstrip(), encoding="utf-8")
