from pathlib import Path
from bs4 import BeautifulSoup, NavigableString
import re


def normalize_whitespace(text: str) -> str:
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
    text = "\n".join(line.strip() for line in text.splitlines())
    return text.strip()


def replace_math_with_latex(soup: BeautifulSoup):
    """
    Replace MathJax SVG-heavy math spans with compact LaTeX.
    """
    for math_span in soup.select("span.math"):
        classes = math_span.get("class", [])
        is_display = "display" in classes

        latex_candidates = []

        for node in math_span.select("[data-latex]"):
            latex = node.get("data-latex", "").strip()
            if latex:
                latex_candidates.append(latex)

        if latex_candidates:
            # Pick the longest candidate because nested MathJax nodes often contain
            # partial symbols like "r", while parent nodes contain the full formula.
            latex = max(latex_candidates, key=len)

            if is_display:
                replacement = f"\n\$$\n{latex}\n\$$\n"
            else:
                replacement = f"\${latex}\$"

            math_span.replace_with(NavigableString(replacement))
        else:
            # If no LaTeX metadata exists, fall back to plain text.
            fallback = math_span.get_text(" ", strip=True)
            math_span.replace_with(NavigableString(fallback))


def simplify_images_and_figures(soup: BeautifulSoup):
    """
    Replace images with compact textual descriptions.
    """
    for img in soup.select("img"):
        alt = img.get("alt") or img.get("aria-label") or ""
        src = img.get("src") or ""

        if alt:
            replacement = f"[Image: {alt}]"
        elif src:
            replacement = f"[Image: {Path(src).name}]"
        else:
            replacement = "[Image]"

        img.replace_with(NavigableString(replacement))


def remove_noise(slide):
    """
    Remove elements that are mostly rendering/UI noise.
    """
    noise_selectors = [
        "script",
        "style",
        "svg",
        "mjx-container",
        "defs",
        "metadata",
        "nav",
        "button",
        "canvas",
        "video",
        "dialog",
        ".whiteboard",
        ".sr-only",
        ".controls",
        ".progress",
        ".speaker-notes",
    ]

    for selector in noise_selectors:
        for node in slide.select(selector):
            node.decompose()


def extract_slide_content(slide):
    """
    Extract clean text from one slide after math/image simplification.
    """
    # Remove screen-reader slide-number boilerplate.
    for sr in slide.select(".sr-only"):
        sr.decompose()

    replace_math_with_latex(slide)
    simplify_images_and_figures(slide)
    remove_noise(slide)

    title = ""
    h1 = slide.find("h1")
    if h1:
        title = normalize_whitespace(h1.get_text(" ", strip=True))

    # Extract the whole slide text after cleanup.
    text = slide.get_text("\n", strip=True)
    text = normalize_whitespace(text)

    # Remove duplicate title at start if present.
    if title and text.startswith(title):
        text = text[len(title):].strip()

    return title, text


def extract_deck(html_path: Path):
    html = html_path.read_text(encoding="utf-8", errors="ignore")
    soup = BeautifulSoup(html, "lxml")

    slides = soup.select("div.slides > section")

    records = []

    for i, slide in enumerate(slides, start=1):
        slide_id = slide.get("id", "")

        title, content = extract_slide_content(slide)

        if not title and not content:
            continue

        records.append({
            "file": html_path.name,
            "slide": i,
            "id": slide_id,
            "title": title,
            "content": content,
        })

    return records


def write_markdown(records, output_path):
    output_path = Path(output_path)

    with output_path.open("w", encoding="utf-8") as f:
        current_file = None

        for r in records:
            if r["file"] != current_file:
                current_file = r["file"]
                f.write(f"\n# {current_file}\n\n")

            f.write(f"## Slide {r['slide']}: {r['title']}\n\n")
            f.write(r["content"])
            f.write("\n\n")


def process_directory(input_dir: str, output_path: str):
    input_dir = Path(input_dir)
    output_path = Path(output_path)

    all_records = []

    for html_path in sorted(input_dir.glob("*.html")):
        records = extract_deck(html_path)
        all_records.extend(records)

    write_markdown(all_records, output_path)

    print(f"Wrote {len(all_records)} slide records to {output_path}")


if __name__ == "__main__":
    process_directory(
        input_dir="html_decks",
        output_path="extracted_slides.md"
    )