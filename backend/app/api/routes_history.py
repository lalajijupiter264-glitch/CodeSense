from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.database.models import Submission, CompilerErrorRecord, StaticWarningRecord, AnalysisRecord
from app.schemas.insights import HistoryResponse, SubmissionSummary
from app.schemas.analysis import AnalysisResponse, ErrorDetail
from app.compiler.error_parser import ParsedCompilerError
from app.classifiers.error_classifier import ClassificationResult
from app.ai.ai_service import AIExplanationResponse
from app.analyzers.static_analyzer import StaticWarning

router = APIRouter(prefix="/api", tags=["History"])


@router.get(
    "/history",
    response_model=HistoryResponse,
    summary="Get Submission History",
    description="Returns a paginated list of previous code submission summaries, compilation results, timing metrics, and primary error categories."
)
def get_history(limit: int = 50, offset: int = 0, db: Session = Depends(get_db)):
    """Retrieve history of previous submissions."""
    query = db.query(Submission).order_by(Submission.created_at.desc())
    total = query.count()
    submissions = query.offset(offset).limit(limit).all()

    summaries: List[SubmissionSummary] = []
    for sub in submissions:
        err_count = len(sub.errors)
        warn_count = len(sub.warnings)
        main_type = None
        main_msg = None
        if sub.errors:
            first_err = sub.errors[0]
            main_type = first_err.category.replace("_", " ").title()
            main_msg = first_err.compiler_message

        summaries.append(SubmissionSummary(
            id=sub.id,
            language=sub.language,
            compile_success=sub.compile_success,
            error_count=err_count,
            warning_count=warn_count,
            main_error_type=main_type,
            main_error_message=main_msg,
            compilation_time_ms=sub.compilation_time,
            created_at=sub.created_at
        ))

    return HistoryResponse(total=total, submissions=summaries)


@router.get(
    "/history/{submission_id}",
    response_model=AnalysisResponse,
    summary="Get Historical Submission Detail",
    description="Retrieves complete retrospective analysis record for a specific submission, including compiler errors, classification taxonomy, and saved explanations."
)
def get_submission_detail(submission_id: str, db: Session = Depends(get_db)):
    """Retrieve full analysis detail for a single previous submission."""
    sub = db.query(Submission).filter(Submission.id == submission_id).first()
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Submission '{submission_id}' not found."
        )

    # Reconstruct ErrorDetails
    error_details: List[ErrorDetail] = []
    for err in sub.errors:
        parsed_err = ParsedCompilerError(
            id=err.id,
            file="Main.java",
            line=err.line or 1,
            column=err.column,
            severity=err.severity,
            message=err.compiler_message,
            code_snippet=err.raw_snippet,
            compiler_code=err.subcategory or "COMPILER_ERROR"
        )
        classification = ClassificationResult(
            category=err.category,
            subcategory=err.subcategory or "GENERAL",
            severity=err.severity.upper(),
            confidence=0.95,
            description=err.compiler_message
        )
        explanation = None
        if err.analysis:
            explanation = AIExplanationResponse(
                title=err.analysis.title,
                what_happened=err.analysis.explanation,
                why_it_happened=err.analysis.cause,
                problematic_code=err.raw_snippet or "",
                suggested_fix=err.analysis.suggested_fix,
                corrected_code=err.analysis.corrected_code,
                prevention_tip=err.analysis.prevention_tip,
                concept_to_learn=err.analysis.concept_to_learn or "Java",
                difficulty="beginner",
                ai_generated=err.analysis.ai_generated
            )
        error_details.append(ErrorDetail(
            error=parsed_err,
            classification=classification,
            explanation=explanation
        ))

    # Reconstruct warnings
    warnings: List[StaticWarning] = []
    for w in sub.warnings:
        warnings.append(StaticWarning(
            id=w.id,
            rule_id=w.rule_id,
            severity=w.severity,
            line=w.line or 1,
            title=w.rule_id.replace("_", " ").title(),
            message=w.message,
            why_it_matters="",
            suggestion=w.suggestion or ""
        ))

    primary = error_details[0] if error_details else None
    summary_msg = "Clean compilation." if sub.compile_success else f"Encountered {len(error_details)} errors."

    return AnalysisResponse(
        submission_id=sub.id,
        language=sub.language,
        success=sub.compile_success,
        exit_code=0 if sub.compile_success else 1,
        compilation_time_ms=sub.compilation_time,
        raw_output="",
        errors=error_details,
        warnings=warnings,
        primary_error=primary,
        summary_message=summary_msg
    )
