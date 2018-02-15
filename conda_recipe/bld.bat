
:: conda build --no-remove-work-dir --old-build-string --dirty .

setlocal enableextensions

set SETUPTOOLS_SYS_PATH_TECHNIQUE=None


"%PYTHON%" setup.py install --single-version-externally-managed --record=record.txt
if %errorlevel% neq 0 exit 1

