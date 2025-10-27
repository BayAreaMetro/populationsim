import pandas as pd

fn = 'output_2023/charts/county_analysis/county_detailed_results.csv'
print('Reading', fn)
df = pd.read_csv(fn)
size_vars = ['hh_size_1','hh_size_2','hh_size_3','hh_size_4','hh_size_5','hh_size_6_plus']

rows = []
for cid in sorted(df['county_id'].unique()):
    sub = df[df['county_id']==cid]
    name = sub['county_name'].iloc[0]
    control_size_sum = sub[sub['control_name'].isin(size_vars)]['control'].sum()
    result_size_sum = sub[sub['control_name'].isin(size_vars)]['result'].sum()
    numhh_gq_control = sub[sub['control_name']=='numhh_gq']['control'].sum()
    numhh_gq_result = sub[sub['control_name']=='numhh_gq']['result'].sum()
    rows.append({
        'county_id': cid,
        'county_name': name,
        'control_size_sum': control_size_sum,
        'result_size_sum': result_size_sum,
        'numhh_gq_control': numhh_gq_control,
        'numhh_gq_result': numhh_gq_result,
        'size_diff_control_minus_result': control_size_sum - result_size_sum,
        'total_diff_control_minus_result': numhh_gq_control - numhh_gq_result
    })

out = pd.DataFrame(rows)

pd.set_option('display.width', 160)
print('\nPer-county summary:')
print(out[['county_name','control_size_sum','result_size_sum','numhh_gq_control','numhh_gq_result','size_diff_control_minus_result','total_diff_control_minus_result']])

# Regional totals
r_control_size = out['control_size_sum'].sum()
r_result_size = out['result_size_sum'].sum()
r_numhh_control = out['numhh_gq_control'].sum()
r_numhh_result = out['numhh_gq_result'].sum()

print('\nRegional sums:')
print(f'  Sum hh_size controls  : {r_control_size:,.0f}')
print(f'  Sum hh_size results   : {r_result_size:,.0f}')
print(f'  Sum numhh_gq controls : {r_numhh_control:,.0f}')
print(f'  Sum numhh_gq results  : {r_numhh_result:,.0f}')
print(f'  Diff (size ctrl - size res): {r_control_size - r_result_size:,.0f}')
print(f'  Diff (total ctrl - total res): {r_numhh_control - r_numhh_result:,.0f}')

# Check if size sums + GQ equals numhh_gq
# For each county, compute (size_sum + numhh_gq_univ + numhh_gq_noninst) vs numhh_gq
for cid in sorted(df['county_id'].unique()):
    sub = df[df['county_id']==cid]
    name = sub['county_name'].iloc[0]
    size_sum = sub[sub['control_name'].isin(size_vars)]['control'].sum()
    gq_univ = sub[sub['control_name']=='hh_gq_university']['control'].sum()
    gq_non = sub[sub['control_name']=='hh_gq_noninstitutional']['control'].sum()
    numhh_gq = sub[sub['control_name']=='numhh_gq']['control'].sum()
    combined = size_sum + gq_univ + gq_non
    if numhh_gq != 0:
        pct = (combined - numhh_gq) / numhh_gq * 100
    else:
        pct = float('nan')
    print(f"{name}: size_sum + gq = {combined:,.0f}, numhh_gq = {numhh_gq:,.0f}, diff = {combined - numhh_gq:,.0f} ({pct:+.2f}%)")

print('\nDone')

# Additional check: compare using COUNTY_balanced_weight and COUNTY_integer_weight
print('\nChecking COUNTY_balanced_weight and COUNTY_integer_weight alignment...')
dfb = pd.read_csv(fn)
rows2 = []
for cid in sorted(dfb['county_id'].unique()):
    sub = dfb[dfb['county_id']==cid]
    name = sub['county_name'].iloc[0]
    bal_size_sum = sub[sub['control_name'].isin(size_vars)]['COUNTY_balanced_weight'].sum()
    bal_numhh = sub[sub['control_name']=='numhh_gq']['COUNTY_balanced_weight'].sum()
    int_size_sum = sub[sub['control_name'].isin(size_vars)]['COUNTY_integer_weight'].sum()
    int_numhh = sub[sub['control_name']=='numhh_gq']['COUNTY_integer_weight'].sum()
    rows2.append({'county_name': name, 'bal_size_sum': bal_size_sum, 'bal_numhh': bal_numhh, 'int_size_sum': int_size_sum, 'int_numhh': int_numhh})

df2 = pd.DataFrame(rows2)
pd.options.display.float_format = '{:,.0f}'.format
print('\nPer-county balanced vs integer weight check:')
print(df2[['county_name','bal_size_sum','bal_numhh','int_size_sum','int_numhh']])

print('\nIf COUNTY_balanced_weight sums align but control_value sums do not, the control breakdowns likely come from mismatched control sources or were not normalized to the same total during control generation.')
