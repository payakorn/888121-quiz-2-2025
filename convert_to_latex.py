import sys
import os
import glob
import re
from docx import Document

# Define categories and keyword matchers
CATEGORIES = {
    "big_data": [
        "big data",
        "volume",
        "velocity",
        "variety",
        "dikw",
        "sql",
        "structured",
        "unstructured",
        "metadata",
        "wisdom",
    ],
    "metaverse": [
        "metaverse",
        "vr",
        "ar",
        "web 3.0",
        "digital twin",
        "virtual",
        "avatar",
    ],
    "ai": [
        "ai",
        "artificial intelligence",
        "machine learning",
        "prompt",
        "chatgpt",
        "supervised",
        "unsupervised",
        "blue-collar",
        "white-collar",
        "learning",
    ],
    "iot": ["iot", "internet of things", "sensor", "gateway"],
    "cloud_computing": [
        "cloud",
        "iaas",
        "paas",
        "saas",
        "edge computing",
        "public cloud",
        "private cloud",
    ],
    "smart_city": [
        "smart city",
        "smart infrastructure",
        "smart environment",
        "smart energy",
        "smart citizen",
        "smart mobility",
        "infrastructure",
    ],
}


def guess_category(text):
    text_lower = text.lower()

    # Priority matches
    if "iot" in text_lower or "sensor" in text_lower:
        return "iot"
    if (
        "cloud" in text_lower
        or "iaas" in text_lower
        or "paas" in text_lower
        or "saas" in text_lower
    ):
        return "cloud_computing"
    if "smart" in text_lower or "infrastructure" in text_lower:
        return "smart_city"
    if "metaverse" in text_lower or "virtual" in text_lower:
        return "metaverse"
    if (
        "data" in text_lower
        or "dikw" in text_lower
        or "metadata" in text_lower
        or "sql" in text_lower
    ):
        return "big_data"
    if "ai" in text_lower or "learning" in text_lower or "prompt" in text_lower:
        return "ai"

    # Secondary matching
    for cat, keywords in CATEGORIES.items():
        for keyword in keywords:
            if keyword in text_lower:
                return cat

    return "general"


def parse_docx(filepath):
    doc = Document(filepath)
    questions = []

    for p in doc.paragraphs:
        text = p.text.strip()
        if not text:
            continue

        if "A)" not in text or "B)" not in text:
            continue

        q_data = {
            "question": "",
            "A": "",
            "B": "",
            "C": "",
            "D": "",
            "correct": None,
            "category": "general",
        }
        current_part = "question"

        char_props = []
        for r in p.runs:
            for char in r.text.replace("\n", " "):
                char_props.append((char, r.bold))

        collected_text = ""
        has_bold = False

        i = 0
        while i < len(char_props):
            char, is_bold = char_props[i]

            if (
                i + 1 < len(char_props)
                and char in ["A", "B", "C", "D"]
                and char_props[i + 1][0] == ")"
            ):
                if current_part == "question":
                    q_data["question"] = collected_text.strip()
                else:
                    q_data[current_part] = collected_text.strip()
                    if has_bold:
                        q_data["correct"] = current_part

                current_part = char
                collected_text = ""
                has_bold = False
                i += 2
                continue

            collected_text += char
            if is_bold and char.strip():
                has_bold = True
            i += 1

        if current_part in q_data and current_part != "question":
            q_data[current_part] = collected_text.strip()
            if has_bold:
                q_data["correct"] = current_part

        if q_data["question"] and q_data["A"] and q_data["B"]:
            q_text = q_data["question"]
            q_text = re.sub(r"^\d+\.\s*", "", q_text)
            q_data["question"] = q_text

            # Categorize based on question and choices text
            all_text = (
                q_data["question"]
                + " "
                + q_data["A"]
                + " "
                + q_data["B"]
                + " "
                + q_data["C"]
                + " "
                + q_data["D"]
            )
            q_data["category"] = guess_category(all_text)

            questions.append(q_data)

    return questions


def generate_latex():
    words_dir = "/Users/payakornsaksuriya/projects/888121-final-2-2025/words"
    output_file = "/Users/payakornsaksuriya/projects/888121-final-2-2025/categorized_questions.tex"

    docx_files = glob.glob(os.path.join(words_dir, "*.docx"))

    all_questions = []
    for docx_file in sorted(docx_files):
        print(f"Processing: {os.path.basename(docx_file)}")
        questions = parse_docx(docx_file)
        all_questions.extend(questions)
        print(f"Added {len(questions)} questions.")

    # Group by category
    categorized = {}
    for q in all_questions:
        cat = q["category"]
        if cat not in categorized:
            categorized[cat] = []
        categorized[cat].append(q)

    print(f"\nTotal Categorization Results:")
    for cat, qs in categorized.items():
        print(f"  {cat}: {len(qs)}")

    # Write to LaTeX
    all_latex = []
    q_num = 1

    # Sort categories to ensure deterministic output order
    sorted_cats = sorted(categorized.keys())

    for cat in sorted_cats:
        cat_display = cat.replace("_", " ").title()

        all_latex.append(
            "% ======================================================================"
        )
        all_latex.append(f"% Topic: {cat_display}")
        all_latex.append(
            "% ======================================================================\n"
        )

        for q in categorized[cat]:
            all_latex.append(f"\\element{{{cat}}}{{")
            all_latex.append(f"  \\begin{{question}}{{Q{q_num:03d}}}")
            all_latex.append(f"    {q['question']}")
            all_latex.append(r"    \begin{choices}")

            for choice_letter in ["A", "B", "C", "D"]:
                if choice_letter in q and q[choice_letter]:
                    choice_text = q[choice_letter]
                    if q["correct"] == choice_letter:
                        all_latex.append(f"        \\correctchoice{{{choice_text}}}")
                    else:
                        all_latex.append(f"        \\wrongchoice{{{choice_text}}}")

            all_latex.append(r"    \end{choices}")
            all_latex.append(r"  \end{question}")
            all_latex.append(r"}")
            all_latex.append("")
            q_num += 1

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(all_latex))

    print(f"\nSuccessfully wrote {q_num - 1} questions to {output_file}")


if __name__ == "__main__":
    generate_latex()
