# Disjoint income bin mapping: assign each ACS bin to the 2010$ control with the largest overlap
# Output: analysis/DISJOINT_INCOME_BIN_MAPPING.txt

cpi_2010 = 218.056
cpi_2023 = 310.0
cpi_ratio = cpi_2023 / cpi_2010

# Standard 2010$ bins (edit as needed)
standard_2010_bins = [
    (0, 13999),
    (14000, 29999),
    (30000, 44999),
    (45000, 59999),
    (60000, 74999),
    (75000, 99999),
    (100000, 124999),
    (125000, 149999),
    (150000, 199999),
    (200000, 9999999)
]

# ACS 2023$ bins and variables
acs_bins = [
    (0, 9999, 'B19001_002E'),
    (10000, 14999, 'B19001_003E'),
    (15000, 19999, 'B19001_004E'),
    (20000, 24999, 'B19001_005E'),
    (25000, 29999, 'B19001_006E'),
    (30000, 34999, 'B19001_007E'),
    (35000, 39999, 'B19001_008E'),
    (40000, 44999, 'B19001_009E'),
    (45000, 49999, 'B19001_010E'),
    (50000, 59999, 'B19001_011E'),
    (60000, 74999, 'B19001_012E'),
    (75000, 99999, 'B19001_013E'),
    (100000, 124999, 'B19001_014E'),
    (125000, 149999, 'B19001_015E'),
    (150000, 199999, 'B19001_016E'),
    (200000, 9999999, 'B19001_017E')
]

# Convert 2010$ bins to 2023$
converted_bins = []
for min2010, max2010 in standard_2010_bins:
    min2023 = min2010 * cpi_ratio
    max2023 = max2010 * cpi_ratio
    converted_bins.append((min2010, max2010, min2023, max2023))

# Assign each ACS bin to the 2010$ bin with the largest overlap
acs_to_control = {}
for amin, amax, avar in acs_bins:
    best_control = None
    best_overlap = 0
    for i, (min2010, max2010, min2023, max2023) in enumerate(converted_bins):
        overlap = max(0, min(amax, max2023) - max(amin, min2023) + 1)
        if overlap > best_overlap:
            best_overlap = overlap
            best_control = i
    acs_to_control[avar] = best_control

# Build disjoint mapping: for each control, list assigned ACS bins
control_to_acs = {i: [] for i in range(len(standard_2010_bins))}
for avar, idx in acs_to_control.items():
    control_to_acs[idx].append(avar)

# Output mapping
lines = []
lines.append("# Disjoint Income Bin Mapping (2010$ to 2023$ and ACS bins)\n")
lines.append(f"# CPI 2010: {cpi_2010}, CPI 2023: {cpi_2023}, Ratio: {cpi_ratio:.3f}\n")
lines.append("[")
for i, (min2010, max2010, min2023, max2023) in enumerate(converted_bins):
    acs_vars = control_to_acs[i]
    lines.append(f"    {{\n        'control': 'hhinc_{min2010//1000}_{max2010//1000}',")
    lines.append(f"        '2010_bin': ({min2010}, {max2010}),")
    lines.append(f"        '2023_bin': ({int(round(min2023))}, {int(round(max2023))}),")
    lines.append(f"        'acs_vars': {acs_vars},")
    lines.append("    },")
lines.append("]\n")

with open('analysis/DISJOINT_INCOME_BIN_MAPPING.txt', 'w') as f:
    f.write('\n'.join(lines))

print("✓ Disjoint income bin mapping written to analysis/DISJOINT_INCOME_BIN_MAPPING.txt")
