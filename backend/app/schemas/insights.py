from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class SubmissionSummary(BaseModel):
    """Brief summary of a previous code submission for history list."""
    id: str = Field(..., description="Submission UUID")
    language: str = Field(default="java", description="Programming language")
    compile_success: bool = Field(..., description="Whether compilation succeeded")
    error_count: int = Field(..., description="Number of compiler errors diagnosed")
    warning_count: int = Field(..., description="Number of static code quality warnings")
    main_error_type: Optional[str] = Field(default=None, description="Primary taxonomy category")
    main_error_message: Optional[str] = Field(default=None, description="Primary compiler diagnostic message")
    compilation_time_ms: float = Field(..., description="Compilation time in milliseconds")
    created_at: datetime = Field(..., description="Timestamp of submission")


class HistoryResponse(BaseModel):
    """List of previous submissions with pagination metadata."""
    total: int = Field(..., description="Total count of recorded submissions")
    submissions: List[SubmissionSummary] = Field(default_factory=list, description="List of submission summaries")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "total": 1,
                    "submissions": [
                        {
                            "id": "7f13b2c1-d45e-4a67-b89c-0123456789ab",
                            "language": "java",
                            "compile_success": False,
                            "error_count": 1,
                            "warning_count": 0,
                            "main_error_type": "Type Error",
                            "main_error_message": "incompatible types: String cannot be converted to int",
                            "compilation_time_ms": 412.5,
                            "created_at": "2026-09-08T00:00:00Z"
                        }
                    ]
                }
            ]
        }
    )


class CategoryBreakdown(BaseModel):
    """Error counts and percentage for one taxonomy category."""
    category: str = Field(..., description="Internal taxonomy key (e.g. TYPE_ERROR)")
    count: int = Field(..., description="Total frequency of occurrence")
    percentage: float = Field(..., description="Percentage of all diagnosed errors")
    display_name: str = Field(..., description="Human-friendly label (e.g. Type Errors)")


class RecommendedTopic(BaseModel):
    """Personalized learning topic based on frequent error types."""
    title: str = Field(..., description="Topic headline")
    category: str = Field(..., description="Taxonomy group")
    description: str = Field(..., description="Educational context")
    key_takeaway: str = Field(..., description="Actionable rule of thumb")


class InsightsResponse(BaseModel):
    """Personalized analytics and insights dashboard data."""
    total_submissions: int = Field(..., description="Total submissions evaluated")
    total_errors: int = Field(..., description="Total errors encountered across all submissions")
    successful_compilations: int = Field(..., description="Count of clean zero-error compilations")
    most_common_category: Optional[str] = Field(default=None, description="Dominant error taxonomy")
    most_common_error: Optional[str] = Field(default=None, description="Most frequent compiler diagnostic")
    category_distribution: List[CategoryBreakdown] = Field(default_factory=list, description="Taxonomy breakdown")
    recommendations: List[RecommendedTopic] = Field(default_factory=list, description="Personalized study recommendations")
    improvement_trend: str = Field(..., description="Human-readable learning trajectory trend")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "total_submissions": 12,
                    "total_errors": 7,
                    "successful_compilations": 5,
                    "most_common_category": "TYPE_ERROR",
                    "most_common_error": "incompatible types",
                    "category_distribution": [
                        {
                            "category": "TYPE_ERROR",
                            "count": 4,
                            "percentage": 57.1,
                            "display_name": "Type Errors"
                        },
                        {
                            "category": "SYNTAX_ERROR",
                            "count": 3,
                            "percentage": 42.9,
                            "display_name": "Syntax Errors"
                        }
                    ],
                    "recommendations": [
                        {
                            "title": "Java Data Types & Type Conversion",
                            "category": "Type Errors",
                            "description": "Understand the difference between primitive types and reference types.",
                            "key_takeaway": "Remember: '20' is a String; 20 without quotes is an int."
                        }
                    ],
                    "improvement_trend": "Improving: Error rate decreased over your recent submissions."
                }
            ]
        }
    )
