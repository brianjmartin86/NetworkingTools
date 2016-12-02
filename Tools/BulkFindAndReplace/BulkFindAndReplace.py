#!/usr/bin/env python3

import argparse
import os
# DEFINE ALL FIND/REPLACE STRINGS HERE:
replacements = {
        'oldstring1': 'newstring1',
        'oldstring2': 'newstring2',
        'oldstring3': 'newstring3',
        'oldstring4': 'newstring4',
        'oldstring5': 'newstring5',
        'oldstring6': 'newstring6'
    }


# DO NOT EDIT BELOW HERE:
# Collect User input from CLI:
def check_cli_args():
    parser = argparse.ArgumentParser(
        description="Performs a Find/Replace All of multiple strings in an entire file")

    parser.add_argument(
        '-f', '--file', type=str, help='File to be converted', required=True
    )

    args = parser.parse_args()
    return args


# Find and replace all items in replacements dictionary and output to a new file:
def main():
    args = check_cli_args()
    input_file_name, file_ext = os.path.splitext(args.file)
    output_file_name = '{}_new{}'.format(input_file_name, file_ext)

    with open(args.config) as infile, open(output_file_name, 'w') as outfile:
        for line in infile:
            for src, target in replacements.items():
                line = line.replace(src, target)
            outfile.write(line)
    print(('{0}' * 40).format('*'))
    print('Converted Configuration output saved to {}'.format(output_file_name))
    print(('{0}' * 40).format('*'))

main()
