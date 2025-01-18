#!/usr/bin/env python3


# Takes a directory as a command-line argument (e.g., python check_duplicates.py /path/to/base_dir).
# Recursively walks all subdirectories of the given directory (ignoring files directly in the base directory if desired).
# Looks for files whose name starts with 00_ and parses out the first four underscore-separated “blocks.”
# Tries to find a “matching” file in the same subdirectory whose first block is a non-zero two-digit number (e.g., 07, 19, etc.) while blocks 2, 3, 4 match the 00_ file.
# Compares file sizes (must be exactly the same).
# If a match is found, prints a line indicating “duplicate found” and also prints a commented-out rm command for the 00_ file.


import os
import sys
import re

def is_nonzero_two_digit(s):
    """
    Checks if s is exactly two digits, with a leading zero allowed,
    and numerically > 0. E.g.: "01", "07", "19", "22", etc.
    """
    return bool(re.fullmatch(r"[0-9]{2}", s)) and int(s) > 0

def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} /path/to/base_dir")
        sys.exit(1)
    
    base_dir = sys.argv[1]
    
    # Dictionary to hold files by (subdir, block2, block3, block4).
    # Each key => list of tuples (block1, full_path, file_size).
    files_dict = {}

    # Walk through the directory tree
    for root, dirs, files in os.walk(base_dir):
        # If you want to skip checking files *directly* under base_dir, uncomment:
        if root == base_dir:
            continue

        for filename in files:
            # We'll split into exactly 5 parts (up to 4 underscores in the first 4 blocks).
            parts = filename.split("_", 4)
            if len(parts) < 5:
                # Not enough underscores to consider
                continue
            
            block1, block2, block3, block4, _rest = parts
            
            # Check if block1 is "00" or a valid nonzero 2-digit number
            if block1 == "00" or is_nonzero_two_digit(block1):
                full_path = os.path.join(root, filename)
                try:
                    size = os.path.getsize(full_path)
                except OSError:
                    # If file is inaccessible, skip
                    continue
                
                # We'll group files by (root, block2, block3, block4)
                key = (root, block2, block3, block4)
                files_dict.setdefault(key, []).append((block1, full_path, size))

    # Now compare entries in each key-group to find pairs:
    for key, fileinfo_list in files_dict.items():
        # fileinfo_list is a list of (block1, full_path, size)
        # We'll look for any "00"-file that has the same size as a non-"00" 2-digit file.

        zero_list    = [(b1, fp, sz) for (b1, fp, sz) in fileinfo_list if b1 == "00"]
        nonzero_list = [(b1, fp, sz) for (b1, fp, sz) in fileinfo_list if b1 != "00" and is_nonzero_two_digit(b1)]
        
        # If we have at least one zero-file and one non-zero-file in the same group:
        if zero_list and nonzero_list:
            for (b1z, fpz, szz) in zero_list:
                for (b1n, fpn, szn) in nonzero_list:
                    if szz == szn:
                        # print("Duplicate found:")
                        # print(f"  00-file:     {fpz}")
                        # print(f"  non-00-file: {fpn}")
                        # print()  # blank line for readability

                        print(".", end="\r")  # progress indicator
                        #remove the file with the 00_ prefix with a python command
                        os.remove(fpz)
        print()

if __name__ == "__main__":
    main()
