
:: Batch script to run the population simulation for all years required for PBA50
:: 2050, 2040, 2035, 2030, 2025

:: prioritize 2050 and 2035
call run_populationsim 2050
call run_populationsim 2035

:: other interim years
call run_populationsim 2040
call run_populationsim 2030
call run_populationsim 2025