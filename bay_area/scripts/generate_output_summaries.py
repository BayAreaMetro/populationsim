from pathlib import Path
import csv

ROOT = Path(r"c:\GitHub\populationsim\bay_area")
OUT_DIR = ROOT / 'docs'
OUT_FILE = OUT_DIR / 'TM2_OUTPUT_SUMMARIES.md'
SEARCH_DIR = ROOT / 'output_2023'

OUT_DIR.mkdir(parents=True, exist_ok=True)

files = sorted(SEARCH_DIR.rglob('*.csv'))

md_lines = []
md_lines.append('# TM2 Output Summaries — Full Enumeration')
md_lines.append('')
md_lines.append('This file lists every CSV found under `output_2023/` and shows the header plus up to 3 sample rows.')
md_lines.append('')
md_lines.append('Generated automatically by scripts/generate_output_summaries.py')
md_lines.append('')

for f in files:
    try:
        rel = f.relative_to(ROOT)
    except Exception:
        rel = f
    md_lines.append('---')
    md_lines.append(f'## {rel}')
    md_lines.append('')
    md_lines.append(f'*Path*: `{f}`')
    try:
        size = f.stat().st_size
        md_lines.append(f'*File size*: {size} bytes')
    except Exception:
        pass
    md_lines.append('')
    # Read header + up to 3 rows safely
    try:
        with f.open('r', encoding='utf-8', errors='replace', newline='') as fh:
            reader = csv.reader(fh)
            header = next(reader, None)
            samples = []
            for i, row in enumerate(reader):
                if i >= 3:
                    break
                samples.append(row)
    except Exception as e:
        header = None
        samples = []
        md_lines.append(f'**Error reading file:** {e}')

    if header is None:
        md_lines.append('File appears empty or could not read header.')
        md_lines.append('')
        continue

    md_lines.append('**Header:**')
    md_lines.append('')
    md_lines.append('```csv')
    md_lines.append(','.join(header))
    md_lines.append('```')
    md_lines.append('')
    if samples:
        md_lines.append('**Sample rows (up to 3):**')
        md_lines.append('')
        md_lines.append('```csv')
        for r in samples:
            md_lines.append(','.join(r))
        md_lines.append('```')
        md_lines.append('')
    else:
        md_lines.append('_No data rows available (file may contain header only)._')
        md_lines.append('')

# Write out
with OUT_FILE.open('w', encoding='utf-8') as out:
    out.write('\n'.join(md_lines))

print(f'Wrote {OUT_FILE} with {len(files)} files documented')
