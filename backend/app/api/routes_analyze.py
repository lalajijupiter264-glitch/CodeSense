import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.database.models import (
    Submission,
    CompilerErrorRecord,
    AnalysisRecord,
    StaticWarningRecord
)
from app.schemas.analysis import (
    AnalyzeRequest,
    CompileRequest,
    ExplainRequest,
    AnalysisResponse,
    ErrorDetail
)
from app.compiler.java_compiler import JavaCompilerService
from app.compiler.error_parser import JavaErrorParser
from app.classifiers.error_classifier import ErrorClassifier
from app.analyzers.static_analyzer import JavaStaticAnalyzer
from app.ai.ai_service import AIExplanationService, AIExplanationResponse
from app.utils.logger import logger

router = APIRouter(prefix="/api", tags=["Analysis"])

# Service singletons
compiler_service = JavaCompilerService()
error_parser = JavaErrorParser()
classifier_service = ErrorClassifier()
static_analyzer = JavaStaticAnalyzer()
ai_service = AIExplanationService()


@router.post(
    "/analyze",
    response_model=AnalysisResponse,
    summary="Full Java Compilation and Educational Analysis",
    description="Compiles Java code using OpenJDK javac, parses raw compiler stderr into structured diagnostic tokens, classifies errors into an educational taxonomy, performs heuristic static analysis, generates validated fixes, and persists submission records."
)
def analyze_code(req: AnalyzeRequest, db: Session = Depends(get_db)):
    """
    Complete analysis pipeline:
    1. Compile source code via OpenJDK javac.
    2. Parse compiler errors into structured tokens.
    3. Classify errors deterministically into taxonomy.
    4. Generate beginner-friendly AI/KB explanations.
    5. Run heuristic static analysis for warnings.
    6. Persist to database for history and learning analytics.
    """
    lang = req.language.lower().strip()
    if lang != "java":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Language '{req.language}' is not supported yet. Currently supported: Java."
        )

    # Security: limit source code size to 64KB
    if len(req.source_code) > 65536:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Source code exceeds maximum allowed size limit of 64KB."
        )


    logger.info(f"Initiating full analysis pipeline for {len(req.source_code)} bytes of {lang}")

    # 1. Compile
    comp_result = compiler_service.compile(req.source_code)

    # 2. Parse errors
    parsed_errors = error_parser.parse(comp_result.stderr)

    # Fallback: If compilation failed or timed out but no standard diagnostics were parsed
    if not comp_result.success and not parsed_errors:
        synthesized_msg = comp_result.stderr.strip() or comp_result.error_message or "Compilation process failed."
        timeout_code = "COMPILATION_TIMEOUT" if comp_result.exit_code == -2 else "COMPILATION_FAILED"
        from app.compiler.error_parser import ParsedCompilerError
        parsed_errors.append(ParsedCompilerError(
            line=1,
            column=1,
            severity="error",
            message=synthesized_msg,
            compiler_code=timeout_code,
            problematic_line=""
        ))

    # 3. Classify & Explain each compiler error
    error_details: List[ErrorDetail] = []
    for err in parsed_errors:
        classification = classifier_service.classify(err)
        explanation = ai_service.explain(req.source_code, err, classification, language="Java")
        error_details.append(ErrorDetail(
            error=err,
            classification=classification,
            explanation=explanation
        ))

    # Multi-error fix coordination across entire source code
    if len(parsed_errors) > 1:
        overall_fix = ai_service.fix_engine.fix_and_validate(req.source_code, parsed_errors, max_iterations=3)
        if overall_fix.fix_available and overall_fix.validated and error_details and error_details[0].explanation:
            error_details[0].explanation.corrected_code = overall_fix.corrected_code
            error_details[0].explanation.fix_available = True
            error_details[0].explanation.fix_confidence = overall_fix.fix_confidence
            error_details[0].explanation.changed_lines = overall_fix.changed_lines
            error_details[0].explanation.fix_explanation = overall_fix.fix_explanation
            error_details[0].explanation.validated = True

    # 4. Heuristic Static Analysis
    warnings = static_analyzer.analyze(req.source_code)

    # 5. Determine Primary Error and effective success
    primary_detail: Optional[ErrorDetail] = error_details[0] if error_details else None

    has_compiler_errors = (not comp_result.success) or any(
        err.severity == "error" or err.compiler_code == "DIVISION_BY_ZERO"
        for err in parsed_errors
    )
    is_success = comp_result.success and not has_compiler_errors
    effective_exit_code = comp_result.exit_code if not has_compiler_errors else (comp_result.exit_code or 1)

    # Summary message
    if is_success:
        if warnings:
            summary = f"Code compiled successfully with {len(warnings)} potential code quality recommendation(s)."
        else:
            summary = "Success! Code compiled cleanly with no errors detected."
    else:
        err_count = len(error_details)
        summary = f"Compilation failed with {err_count} compiler error{'s' if err_count > 1 else ''}."

    # 6. Database Persistence
    submission_id = str(uuid.uuid4())
    try:
        submission = Submission(
            id=submission_id,
            user_id=req.user_id,
            language=lang,
            source_code=req.source_code,
            compile_success=is_success,
            compilation_time=comp_result.compilation_time_ms
        )
        db.add(submission)

        for detail in error_details:
            err_record_id = str(uuid.uuid4())
            err_rec = CompilerErrorRecord(
                id=err_record_id,
                submission_id=submission_id,
                category=detail.classification.category,
                subcategory=detail.classification.subcategory,
                severity=detail.error.severity,
                line=detail.error.line,
                column=detail.error.column,
                compiler_message=detail.error.message,
                raw_snippet=detail.error.code_snippet
            )
            db.add(err_rec)

            if detail.explanation:
                exp_rec = AnalysisRecord(
                    id=str(uuid.uuid4()),
                    error_id=err_record_id,
                    title=detail.explanation.title,
                    explanation=detail.explanation.what_happened,
                    cause=detail.explanation.why_it_happened,
                    suggested_fix=detail.explanation.suggested_fix,
                    corrected_code=detail.explanation.corrected_code,
                    prevention_tip=detail.explanation.prevention_tip,
                    concept_to_learn=detail.explanation.concept_to_learn,
                    ai_generated=detail.explanation.ai_generated
                )
                db.add(exp_rec)

        for w in warnings:
            warn_rec = StaticWarningRecord(
                id=str(uuid.uuid4()),
                submission_id=submission_id,
                rule_id=w.rule_id,
                severity=w.severity,
                line=w.line,
                message=w.message,
                suggestion=w.suggestion
            )
            db.add(warn_rec)

        db.commit()
        logger.info(f"Persisted submission {submission_id} with {len(error_details)} errors and {len(warnings)} warnings.")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to persist submission to database: {e}")
        # Analysis results are still returned to user even if DB write encountered an error

    return AnalysisResponse(
        submission_id=submission_id,
        language="java",
        success=is_success,
        exit_code=effective_exit_code,
        compilation_time_ms=comp_result.compilation_time_ms,
        raw_output=comp_result.stderr if not is_success else comp_result.stdout,
        errors=error_details,
        warnings=warnings,
        primary_error=primary_detail,
        summary_message=summary
    )


@router.post(
    "/compile",
    summary="Compile Java Code Only",
    description="Invokes OpenJDK javac compiler directly and returns raw output and parsed error tokens without triggering educational or AI explanation generation."
)
def compile_only(req: CompileRequest):
    """Compile code without generating AI explanations."""
    comp_result = compiler_service.compile(req.source_code)
    parsed_errors = error_parser.parse(comp_result.stderr)
    has_compiler_errors = (not comp_result.success) or any(
        err.severity == "error" or err.compiler_code == "DIVISION_BY_ZERO"
        for err in parsed_errors
    )
    is_success = comp_result.success and not has_compiler_errors
    effective_exit_code = comp_result.exit_code if not has_compiler_errors else (comp_result.exit_code or 1)
    return {
        "success": is_success,
        "exit_code": effective_exit_code,
        "compilation_time_ms": comp_result.compilation_time_ms,
        "raw_stderr": comp_result.stderr,
        "raw_stdout": comp_result.stdout,
        "errors": parsed_errors
    }


@router.post(
    "/explain",
    response_model=AIExplanationResponse,
    summary="Explain Specific Error Diagnostic",
    description="Generates beginner-friendly educational breakdown, root cause explanation, prevention advice, and compiler-verified fix for an isolated diagnostic token."
)
def explain_error(req: ExplainRequest):
    """Generate explanation for a specific error on demand."""
    classification = req.classification or classifier_service.classify(req.error)
    explanation = ai_service.explain(req.source_code, req.error, classification, language=req.language)
    return explanation
