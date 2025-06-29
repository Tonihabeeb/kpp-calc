#!/usr/bin/env python3
"""Check for unmatched triple quotes in engine.py"""


def check_triple_quotes():
    with open("simulation/engine.py", "r") as f:
        lines = f.readlines()
        content = "".join(lines)

    triple_quotes = content.count('"""')
    print(f"Total triple quotes: {triple_quotes}")
    print(f"Even (properly paired): {triple_quotes % 2 == 0}")

    if triple_quotes % 2 != 0:
        print("ERROR: Odd number of triple quotes - there is an unmatched docstring!")

        # Find all positions
        positions = []
        start = 0
        while True:
            pos = content.find('"""', start)
            if pos == -1:
                break
            line_num = content[:pos].count("\n") + 1
            positions.append((pos, line_num))
            start = pos + 3

        print("Triple quote positions with context:")
        for i, (pos, line) in enumerate(positions):
            status = "OPEN" if i % 2 == 0 else "CLOSE"
            # Show the line content
            line_content = lines[line - 1].strip() if line <= len(lines) else "EOF"
            print(f'  Line {line}: {status} - "{line_content}"')
    else:
        print("All triple quotes are properly paired.")


if __name__ == "__main__":
    check_triple_quotes()
