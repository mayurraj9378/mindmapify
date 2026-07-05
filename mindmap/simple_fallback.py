def generate_simple_mindmap(text: str) -> str:
    """
    Pure rule-based markdown structure, no AI required. Used only when every
    configured AI provider has failed or hit quota - guarantees the app
    always produces *something* for the user.
    """
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    sections = []
    current_section = {"title": "", "items": []}

    for line in lines[:500]:
        looks_like_heading = len(line) < 150 and (line[0].isupper() or line[0].isdigit())
        if looks_like_heading:
            if current_section["items"]:
                sections.append(current_section)
                current_section = {"title": line, "items": []}
            elif not current_section["title"]:
                current_section["title"] = line
        elif len(line) > 20:
            current_section["items"].append(line[:120])

    if current_section["items"]:
        sections.append(current_section)

    if not sections:
        return (
            "# Document Overview\n"
            "## Content\n"
            "- This document contains text content\n"
            "- Configure an AI provider for a more detailed structure\n"
        )

    markdown = "# Document Content\n\n"
    for i, section in enumerate(sections[:15], 1):
        title = section["title"] or f"Section {i}"
        markdown += f"## {title}\n"
        for item in section["items"][:8]:
            markdown += f"- {item}\n"
        markdown += "\n"

    return markdown
