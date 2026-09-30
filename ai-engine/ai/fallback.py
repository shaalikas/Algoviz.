from typing import Any


def _items(value: Any) -> list:
    return value if isinstance(value, list) else []


def _names(items: list, key: str = "name") -> list[str]:
    out = []
    for item in items:
        if isinstance(item, str):
            out.append(item)
        elif isinstance(item, dict) and item.get(key):
            out.append(str(item[key]))
    return out


def generate_fallback(metadata: dict) -> str:
    """Generate a deterministic explanation using only supplied metadata."""
    repo = metadata.get("repository") if isinstance(metadata.get("repository"), dict) else {}
    files = _items(metadata.get("files"))
    dependencies = _items(metadata.get("dependencies"))
    risks = _items(metadata.get("detected_risks") or metadata.get("risks"))
    circular = _items(metadata.get("circular_dependencies"))
    architecture = metadata.get("architecture")

    name = repo.get("name") or metadata.get("name") or "the repository"
    language = repo.get("language") or metadata.get("language")
    file_paths = [
        str(f.get("path"))
        for f in files
        if isinstance(f, dict) and f.get("path")
    ]
    file_paths = [p for p in file_paths if p]

    components = []
    if isinstance(architecture, dict):
        components = _names(
            architecture.get("components")
            or architecture.get("layers")
            or []
        )
    elif isinstance(architecture, list):
        components = _names(architecture)

    dep_names = _names(dependencies)
    risk_text = []
    for risk in risks:
        if isinstance(risk, str):
            risk_text.append(risk)
        elif isinstance(risk, dict):
            text = risk.get("description") or risk.get("name") or risk.get("type")
            if text:
                risk_text.append(str(text))

    lines = [
        "Repository overview",
        f"- Repository: {name}.",
    ]
    if language:
        lines.append(f"- Primary language: {language}.")
    if file_paths:
        lines.append(f"- Metadata describes {len(file_paths)} file(s).")
    else:
        lines.append("- No file paths were supplied in the metadata.")

    lines += ["", "Where to start"]
    if file_paths:
        likely = []
        for p in file_paths:
            low = p.lower().replace("\\", "/")
            if any(token in low for token in ("main.", "app.", "server.", "index.", "__main__", "manage.py")):
                likely.append(p)
        if likely:
            lines.append("- Start with: " + ", ".join(likely[:5]) + ".")
        else:
            lines.append("- No clear entry-point filename is identified by the supplied metadata.")
            lines.append("- Start with the file paths/symbols marked as entry points by your repository analyzer, if available.")
    else:
        lines.append("- The metadata does not identify a starting file.")

    lines += ["", "Architecture and components"]
    if components:
        lines.append("- Detected components/layers: " + ", ".join(components) + ".")
    else:
        lines.append("- No explicit architectural components/layers were supplied.")
    lines.append("- This fallback intentionally does not infer architecture beyond the metadata.")

    lines += ["", "Important dependencies"]
    if dep_names:
        lines.append("- " + ", ".join(dep_names[:20]) + ".")
    else:
        lines.append("- No dependencies were supplied.")

    lines += ["", "Risks and circular dependencies"]
    if risk_text:
        for risk in risk_text[:10]:
            lines.append(f"- Risk: {risk}.")
    else:
        lines.append("- No detected risks were supplied.")
    if circular:
        for cycle in circular[:10]:
            if isinstance(cycle, list):
                lines.append("- Circular dependency: " + " -> ".join(map(str, cycle)) + ".")
            else:
                lines.append(f"- Circular dependency: {cycle}.")
    else:
        lines.append("- No circular dependencies were supplied.")

    lines += ["", "Onboarding guide"]
    lines.append("- Use the supplied file paths, symbols, imports, dependencies, and architecture metadata as the source of truth.")
    lines.append("- Trace imports/dependencies outward from the identified entry point before reading lower-level implementation details.")
    lines.append("- Review every listed risk and circular dependency before making structural changes.")
    lines.append("- This is a local metadata-only explanation; it does not inspect repository source code itself.")

    return "\n".join(lines)
