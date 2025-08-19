# PYTHONPATH and Local Imports for Analysis Scripts

Many analysis and utility scripts in this project import modules from the local `tm2_control_utils` package (and others) using lines like:

```python
from tm2_control_utils.config_census import INCOME_BIN_MAPPING
```

## How to Run Analysis Scripts

To ensure these imports work, you must run scripts with the `PYTHONPATH` set to the project directory containing `tm2_control_utils` (usually the `bay_area` directory). This allows Python to find local modules.

### Example (Windows PowerShell)

From the `bay_area` directory, run:

```powershell
$env:PYTHONPATH = "$PWD"
python analysis\your_script.py
```

Or, for the pipeline:

```powershell
$env:PYTHONPATH = "$PWD"
python tm2_pipeline.py analysis
```

This ensures all scripts can import local modules without errors.

---

If you see errors like `ModuleNotFoundError: No module named 'tm2_control_utils'`, check that you are running from the correct directory and that `PYTHONPATH` is set as above.
