:: Run the population simulation for the bay area

:create_seed
python create_seed_population.py
if ERRORLEVEL 1 goto error

:year_loop
for %%Y in (2000 2005 2010 2015) do (

  rem households
  mkdir households\output_%%Y
  python run_populationsim.py --model_year %%Y  --config households\configs     --output households\output_%%Y    --data households\data
  if ERRORLEVEL 1 goto error

  rem group_quarters
  mkdir group_quarters\output_%%Y
  python run_populationsim.py --model_year %%Y --config group_quarters\configs --output group_quarters\output_%%Y  --data group_quarters\data
  if ERRORLEVEL 1 goto error
)

:success
echo Completed run_populationsim.bat successfully!

:error
echo An error occurred

:end