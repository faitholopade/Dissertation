@echo off
REM run_pipeline.bat — Full dissertation pipeline

echo Step 1: Rule-based annotation
python annotate_records.py
if %ERRORLEVEL% NEQ 0 goto :error

echo Step 2: LLM-assisted annotation
python llm_annotate.py
if %ERRORLEVEL% NEQ 0 goto :error

echo Step 3: Three-way method comparison
python compare_methods.py
if %ERRORLEVEL% NEQ 0 goto :error

echo Step 4: Error analysis
python error_analysis.py
if %ERRORLEVEL% NEQ 0 goto :error

echo Step 5: Agreement evaluation
python evaluate_annotations.py
if %ERRORLEVEL% NEQ 0 goto :error

echo Step 6: Export JSON-LD
python export_semantic.py
if %ERRORLEVEL% NEQ 0 goto :error

echo Step 7: FRIA-style demonstration scenarios
python fria_demo.py
if %ERRORLEVEL% NEQ 0 goto :error

echo Step 8: Generate dissertation figures
python generate_figures.py
if %ERRORLEVEL% NEQ 0 goto :error

echo Pipeline complete.
goto :eof

:error
echo Pipeline failed at the step above. Fix the error and re-run.
pause
