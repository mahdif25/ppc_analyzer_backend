import re
import sys

def fix_fstrings_in_file(filepath):
    try:
        with open(filepath, 'r') as file:
            lines = file.readlines()
    except FileNotFoundError:
        print(f"Error: File {filepath} not found.")
        sys.exit(1)

    new_lines = []
    corrected_count = 0
    for line_num, line in enumerate(lines):
        original_line = line
        # Only apply to lines that are likely f-strings starting with f"...
        # and specifically target problematic patterns identified.
        if 'f"' in line: # A simple check for f-string, can be refined
            # Pattern 1: len(response_json["recommendations"]) in f-string
            if 'len(response_json["recommendations"])' in line:
                line = line.replace('len(response_json["recommendations"])', "len(response_json['recommendations'])")
            
            # Pattern 2: response_json["errors"] in f-string
            if 'response_json["errors"]' in line:
                line = line.replace('response_json["errors"]', "response_json['errors']")
            
            # Add more specific, known problematic patterns here if they arise
            # Example: response_json["some_other_key"]
            # line = line.replace('response_json["some_other_key"]', "response_json['some_other_key']")

        if line != original_line:
            print(f"INFO: Line {line_num + 1} was corrected in {filepath}.")
            corrected_count += 1
        new_lines.append(line)

    try:
        with open(filepath, 'w') as file:
            file.writelines(new_lines)
        if corrected_count > 0:
            print(f"INFO: {corrected_count} line(s) corrected in {filepath}.")
        else:
            print(f"INFO: No lines seemed to require correction in {filepath} based on current patterns.")
    except IOError:
        print(f"Error: Could not write to file {filepath}.")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python fix_fstring.py <path_to_python_file>")
        sys.exit(1)
    
    file_to_fix = sys.argv[1]
    print(f"INFO: Attempting to fix f-strings in {file_to_fix}...")
    fix_fstrings_in_file(file_to_fix)
    print(f"INFO: Script finished processing {file_to_fix}.")

