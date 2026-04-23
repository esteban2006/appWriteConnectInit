import re

INPUT_FILE = "j.txt"
OUTPUT_FILE = "prueba.txt"


def get_initials(name: str) -> str:
    # Take first letter of each word in the name
    parts = name.strip().split()
    return "".join(word[0].upper() for word in parts if word)


def clean_chat_file(input_file, output_file):
    cleaned_lines = []

    with open(input_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            # Match: date - Name: message
            match = re.match(r"^.*? - (.*?):\s*(.*)$", line)

            if match:
                name = match.group(1)
                message = match.group(2)

                initials = get_initials(name)
                cleaned_lines.append(f"{initials}: {message}")
            else:
                # System message or unknown format
                cleaned_lines.append(line)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(cleaned_lines))


clean_chat_file(INPUT_FILE, OUTPUT_FILE)
print("Chat cleaned successfully.")
