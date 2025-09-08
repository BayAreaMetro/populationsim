import csv
import os

# Fixed paths relative to the analysis directory
input_file = "../output_2023/populationsim_working_dir/data/maz_data_withDensity.csv"
output_file = "../output_2023/populationsim_working_dir/data/maz_data_withDensity_fixed.csv"
log_file = "../output_2023/populationsim_working_dir/output/maz_data_withDensity_fix_log.txt"
expected_columns = 77

# Create output directory if it doesn't exist
os.makedirs(os.path.dirname(output_file), exist_ok=True)
os.makedirs(os.path.dirname(log_file), exist_ok=True)

print(f"Processing: {input_file}")
print(f"Output will be: {output_file}")
print(f"Log will be: {log_file}")

with open(input_file, newline='', encoding='utf-8') as infile, \
     open(output_file, 'w', newline='', encoding='utf-8') as outfile, \
     open(log_file, 'w', encoding='utf-8') as logfile:
    reader = csv.reader(infile)
    writer = csv.writer(outfile)
    for row_num, row in enumerate(reader, 1):
        original_row = row[:]
        issues = []
        # Replace 'inf' with '0.0'
        if any(str(cell).strip().lower() == 'inf' for cell in row):
            row = ['0.0' if str(cell).strip().lower() == 'inf' else cell for cell in row]
            issues.append("Replaced 'inf' with '0.0'")
        # Pad row if too short
        if len(row) < expected_columns:
            row += [''] * (expected_columns - len(row))
            issues.append(f"Padded row from {len(original_row)} to {expected_columns} columns")
        # Log if there were any issues
        if issues:
            logfile.write(f"Row {row_num}: {', '.join(issues)}\n")
            logfile.write(f"  Original: {original_row}\n")
            logfile.write(f"  Fixed:    {row}\n\n")
        writer.writerow(row)

print("Done. Cleaned file written to", output_file)