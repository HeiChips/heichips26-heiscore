#!/usr/bin/env python3
import re
import sys

file = sys.argv[1] if len(sys.argv) > 1 else 'ims-arcade_constraints.ccf'
loc_to_net = {}

rex = re.compile(r'(?:Net|Pin_in|Pin_out|Pin_inout)\s+"([^"]+)"\s+Loc\s*=\s*"([^"]+)"')
errors = 0

print(f'Checking {file} for duplicate pin assignments...')

with open(file, 'r') as f:
    for line in f:
        line = line.strip()
        if line.startswith('#'):
            continue
        cmt = line.find('#')
        if cmt > 0:
            line = line[0:cmt]
        if len(line) == 0:
            continue
        matches = rex.match(line)
        if not matches:
            print(f'ERROR: Cannot understand line: {line}')
        loc = matches[2].upper().strip()
        net = matches[1]
        if loc in loc_to_net:
            print(f'ERROR: Duplicate assignment to {loc}: {net} but already connected to {loc_to_net[loc]}!')
            errors += 1
        else:
            loc_to_net[loc] = net
            print(f'OK: {loc} <= {net}')

if errors:
    print(f'ERRORS: {errors}')
    exit(1)
else:
    print(f'CHECK COMPLETE - OK.')
    exit(0)
