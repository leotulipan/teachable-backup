#!/usr/bin/env python3

import os
import sys
import re

def is_nonzero_two_digit(s):
    """
    Checks if s is exactly two digits, with a leading zero allowed,
    and numerically > 0. E.g.: "01", "07", "19", "22", etc.
    """
    return bool(re.fullmatch(r"[0-9]{2}", s)) and int(s) > 0

def block2_differs_by_one(b2_zero, b2_nonzero):
    """
    Returns True if the integer values of block2 differ by exactly 1.
    """
    try:
        z_val = int(b2_zero)
        n_val = int(b2_nonzero)
        return abs(z_val - n_val) == 1
    except ValueError:
        return False

def handle_off_by_one(zero_path, nonzero_path):
    """
    1) Parse filenames for both files.
    2) Rename the non-zero file, using:
       - block1 from the non-zero file
       - block2, block3, block4 from the zero file
       - the 'rest' from the non-zero file
    3) Remove the zero file.
    """
    # Separate directory from filename
    dir_z, filename_z = os.path.split(zero_path)
    dir_n, filename_n = os.path.split(nonzero_path)

    # Parse the filenames (split into 5 parts).
    # zero file
    z_parts = filename_z.split("_", 4)
    # non-zero file
    n_parts = filename_n.split("_", 4)

    if len(z_parts) < 5 or len(n_parts) < 5:
        return  # safety check, though we wouldn't be here if we didn't already validate

    z_b1, z_b2, z_b3, z_b4, z_rest = z_parts
    n_b1, n_b2, n_b3, n_b4, n_rest = n_parts

    # Construct the new filename for the non-zero file:
    #  - block1 from the non-zero file: n_b1
    #  - block2, block3, block4 from the zero file: z_b2, z_b3, z_b4
    #  - 'rest' from the non-zero file: n_rest
    new_filename = f"{n_b1}_{z_b2}_{z_b3}_{z_b4}_{n_rest}"
    new_path = os.path.join(dir_n, new_filename)

    # Attempt to rename the non-zero file
    # (If a file with that name already exists, this could overwrite it—
    #  you might want to handle that case carefully if it’s a possibility).
    os.rename(nonzero_path, new_path)
    # Now remove the 00_ file
    print(f"x", end="", flush=True)  # simple progress indicator
    os.remove(zero_path)

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
        # if root == base_dir:
        #     continue

        for filename in files:
            # We'll split into exactly 5 parts (up to 4 underscores in the first 4 blocks).
            parts = filename.split("_", 4)
            if len(parts) < 5:
                continue
            
            block1, block2, block3, block4, _rest = parts

            # Check if block1 is "00" or a valid nonzero 2-digit number
            if block1 == "00" or is_nonzero_two_digit(block1):
                full_path = os.path.join(root, filename)
                try:
                    size = os.path.getsize(full_path)
                except OSError:
                    continue
                
                key = (root, block3, block4)  
                # NOTE: We used to include block2 in the key for exact matches,
                # but because we now want to detect the ±1 case in block2,
                # we group by (root, block3, block4) only, then handle block2 logic below.
                
                # We'll store (block1, block2, full_path, size).
                files_dict.setdefault(key, []).append((block1, block2, full_path, size))

    # Now compare entries in each key-group to find pairs:
    for key, fileinfo_list in files_dict.items():
        # We’ll look for "00"-files vs non-"00" files that share block3, block4, same size,
        # and then compare block2 either for exact match or off-by-one.

        # Partition into zero_list and nonzero_list
        zero_list    = [(b1, b2, fp, sz) for (b1, b2, fp, sz) in fileinfo_list if b1 == "00"]
        nonzero_list = [(b1, b2, fp, sz) for (b1, b2, fp, sz) in fileinfo_list if b1 != "00" and is_nonzero_two_digit(b1)]
        
        if zero_list and nonzero_list:
            for (z_b1, z_b2, z_fp, z_sz) in zero_list:
                for (n_b1, n_b2, n_fp, n_sz) in nonzero_list:
                    if z_sz == n_sz:
                        # They have the same size, so possible duplicates.
                        # Check block2 logic:
                        if z_b2 == n_b2:
                            # EXACT match => remove the 00_ file
                            print(".", end="\r")  # simple progress indicator
                            os.remove(z_fp)

                        elif block2_differs_by_one(z_b2, n_b2):
                            # BLOCK2 differs by ±1 => rename + remove the 00_ file
                            print(".", end="", flush=True)  # simple progress indicator
                            handle_off_by_one(z_fp, n_fp)

if __name__ == "__main__":
    main()
