@echo off
REM ============================================================
REM run_pipeline.bat — Full dissertation pipeline (v0.3)
REM ============================================================
echo.
echo ============================================================
echo  STEP 1: Rule-based annotation
echo ============================================================
python annotate_records.py
if %ERRORLEVEL% NEQ 0 goto :error

echo.
echo ============================================================
echo  STEP 2: LLM-assisted annotation (requires ANTHROPIC_API_KEY)
echo ============================================================
python llm_annotate.py
if %ERRORLEVEL% NEQ 0 goto :error

echo.
echo ============================================================
echo  STEP 3: Three-way method comparison (keyword / LLM / hybrid)
echo ============================================================
python compare_methods.py
if %ERRORLEVEL% NEQ 0 goto :error

echo.
echo ============================================================
echo  STEP 4: Error analysis (confusion matrices, disagreements)
echo ============================================================
python error_analysis.py
if %ERRORLEVEL% NEQ 0 goto :error

echo.
echo ============================================================
echo  STEP 5: Agreement evaluation (AIAAIC pilot + master table)
echo ============================================================
python evaluate_annotations.py
if %ERRORLEVEL% NEQ 0 goto :error

echo.
echo ============================================================
echo  STEP 6: Export JSON-LD (DPV/VAIR vocabulary-aligned)
echo ============================================================
python export_semantic.py
if %ERRORLEVEL% NEQ 0 goto :error

echo.
echo ============================================================
echo  STEP 7: FRIA-style demonstration scenarios
echo ============================================================
python fria_demo.py
if %ERRORLEVEL% NEQ 0 goto :error

echo.
echo ============================================================
echo  STEP 8: Generate dissertation figures
echo ============================================================
python generate_figures.py
if %ERRORLEVEL% NEQ 0 goto :error

echo.
echo ============================================================
echo  PIPELINE COMPLETE
echo ============================================================
echo.
echo Output files:
echo   master_annotation_table.csv         (keyword annotations)
echo   master_annotation_table_llm.csv     (+ LLM annotations)
echo   master_annotation_table_hybrid.csv  (+ hybrid column)
echo   risk_records.jsonld                 (JSON-LD export)
echo   method_comparison_results.csv       (3-way comparison)
echo   confusion_matrix_domain.csv         (confusion matrix)
echo   confusion_matrix_pattern.csv        (confusion matrix)
echo   disagreement_examples.csv           (error examples)
echo   error_analysis_report.txt           (full error report)
echo   evaluate_results.csv                (agreement metrics)
echo   fig_*.png                           (dissertation figures)
echo.
goto :eof

:error
echo.
echo !! Pipeline failed at the step above. Fix the error and re-run.
pause
