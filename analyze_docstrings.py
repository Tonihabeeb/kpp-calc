#!/usr/bin/env python3
"""Advanced docstring analyzer to find the exact location of unmatched quotes"""


def find_unmatched_docstring():
    with open("simulation/engine.py", "r") as f:
        lines = f.readlines()

    # Track docstring state
    in_docstring = False
    docstring_start_line = None
    quote_count = 0

    print("Analyzing triple quotes line by line:")

    for i, line in enumerate(lines, 1):
        if '"""' in line:
            count_in_line = line.count('"""')
            quote_count += count_in_line

            print(
                f"Line {i}: {count_in_line} quotes, total: {quote_count}, line: {repr(line.strip())}"
            )

            # If this line has an odd number of quotes, it toggles the state
            if count_in_line % 2 == 1:
                if not in_docstring:
                    in_docstring = True
                    docstring_start_line = i
                    print(f"  -> Starting docstring at line {i}")
                else:
                    in_docstring = False
                    print(
                        f"  -> Ending docstring that started at line {docstring_start_line}"
                    )
                    docstring_start_line = None

    print("\nFinal state:")
    print(f"Total quotes: {quote_count}")
    print(f"In docstring: {in_docstring}")
    if in_docstring:
        print(f"Unclosed docstring started at line: {docstring_start_line}")
        print('This is the line that needs a closing """')


if __name__ == "__main__":
    find_unmatched_docstring()
