# Group ACS 2023$ bins into new control bins that best match 2010$ bins after CPI adjustment
# Output: analysis/ACS_ALIGNED_INCOME_BINS.txt

cpi_2010 = 218.056
cpi_2023 = 310.0
cpi_ratio = cpi_2023 / cpi_2010

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

def to_2010(val_2023):
    return int(round(val_2023 / cpi_ratio))

# Group ACS bins into new controls, aiming to match 2010$ bins as closely as possible
# You can adjust these groupings as needed for your use case
acs_groups = [
    ['B19001_002E', 'B19001_003E', 'B19001_004E'],  # <20k
    ['B19001_005E', 'B19001_006E', 'B19001_007E', 'B19001_008E', 'B19001_009E'],  # 20k-45k
    ['B19001_010E', 'B19001_011E'],  # 45k-60k
    ['B19001_012E'],  # 60k-75k
    ['B19001_013E'],  # 75k-100k
    ['B19001_014E', 'B19001_015E'],  # 100k-150k
    ['B19001_016E'],  # 150k-200k
    ['B19001_017E'],  # 200k+
]

# Build output
lines = []
lines.append("# ACS-aligned Income Control Bins (grouped from ACS 2023$ bins)\n")
lines.append(f"# CPI 2010: {cpi_2010}, CPI 2023: {cpi_2023}, Ratio: {cpi_ratio:.3f}\n")
lines.append("[")
for group in acs_groups:
    group_bins = [b for b in acs_bins if b[2] in group]
    min_2023 = group_bins[0][0]
    max_2023 = group_bins[-1][1]
    min_2010 = to_2010(min_2023)
    max_2010 = to_2010(max_2023)
    lines.append(f"    {{\n        'acs_vars': {group},")
    lines.append(f"        '2023_bin': ({min_2023}, {max_2023}),")
    lines.append(f"        '2010_bin': ({min_2010}, {max_2010}),")
    lines.append("    },")
lines.append("]\n")

with open('analysis/ACS_ALIGNED_INCOME_BINS.txt', 'w') as f:
    f.write('\n'.join(lines))

print("✓ ACS-aligned income bins written to analysis/ACS_ALIGNED_INCOME_BINS.txt")
