import csv
from pathlib import Path

# Adjust these paths if your outputs are in a different folder
base = Path(r"c:\GitHub\populationsim\bay_area\output_2023\populationsim_working_dir\output")
house_file = base / "synthetic_households.csv"
person_file = base / "synthetic_persons.csv"

out_dir = Path(r"c:\GitHub\populationsim\bay_area\docs")
out_dir.mkdir(parents=True, exist_ok=True)

def sample_csv(in_path, out_path, n=10):
    if not in_path.exists():
        print(f"MISSING: {in_path}")
        return False
    with in_path.open('r', encoding='utf-8', errors='replace', newline='') as inf:
        reader = csv.reader(inf)
        try:
            header = next(reader)
        except StopIteration:
            print(f"EMPTY: {in_path}")
            return False
        rows = []
        for i, row in enumerate(reader):
            rows.append(row)
            if i+1 >= n:
                break
    # write sample as CSV and a pretty text version
    with (out_path.with_suffix('.csv')).open('w', encoding='utf-8', newline='') as outf:
        writer = csv.writer(outf)
        writer.writerow(header)
        writer.writerows(rows)
    with out_path.open('w', encoding='utf-8') as outf:
        outf.write(','.join(header) + '\n')
        for r in rows:
            outf.write(','.join(r) + '\n')
    print(f"WROTE: {out_path} and {out_path.with_suffix('.csv')}")
    return True

sample_csv(house_file, out_dir / 'sample_synthetic_households.txt', n=10)
sample_csv(person_file, out_dir / 'sample_synthetic_persons.txt', n=10)
print('done')
