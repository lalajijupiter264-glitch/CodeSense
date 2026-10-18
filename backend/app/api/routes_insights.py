from collections import Counter
from typing import List, Dict
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.database.models import Submission, CompilerErrorRecord
from app.schemas.insights import (
    InsightsResponse,
    CategoryBreakdown,
    RecommendedTopic
)

router = APIRouter(prefix="/api", tags=["Insights"])

RECOMMENDATION_TOPICS_MAP = {
    "TYPE_ERROR": [
        RecommendedTopic(
            title="Java Data Types & Type Conversion",
            category="Type Errors",
            description="Understand the difference between primitive types (int, double, boolean) and reference types (String).",
            key_takeaway="Remember: '20' in quotes is a String; 20 without quotes is an int. Use Integer.parseInt() to convert text to integers."
        ),
        RecommendedTopic(
            title="Type Casting & Precision",
            category="Type Errors",
            description="Learn when explicit casting is necessary and how to prevent lossy conversions between doubles and ints.",
            key_takeaway="Use (int) cast when deliberately truncating decimals, or change variable type to double."
        )
    ],
    "SYNTAX_ERROR": [
        RecommendedTopic(
            title="Java Statement Structure & Punctuation",
            category="Syntax Errors",
            description="Master semicolon placement, brace pairing {}, and parentheses () in control flow.",
            key_takeaway="Every variable assignment and method invocation must end with a semicolon ';'."
        ),
        RecommendedTopic(
            title="Block Scope & Delimiters",
            category="Syntax Errors",
            description="Learn how to pair curly braces accurately for classes, methods, loops, and conditional statements.",
            key_takeaway="Proper code indentation visually highlights missing closing braces before the compiler complains."
        )
    ],
    "VARIABLE_ERROR": [
        RecommendedTopic(
            title="Variable Declaration, Initialization & Scope",
            category="Variable Errors",
            description="Understand where variables live, how block scope limits access, and the requirement of definite assignment.",
            key_takeaway="Always declare a variable with its data type before use and provide a default starting value."
        )
    ],
    "METHOD_ERROR": [
        RecommendedTopic(
            title="Method Signatures & Parameter Matching",
            category="Method Errors",
            description="Learn how Java selects methods by argument count and types, and how return statements work.",
            key_takeaway="Non-void methods must return a value on every possible execution path."
        )
    ],
    "CLASS_ERROR": [
        RecommendedTopic(
            title="Packages & Import Statements",
            category="Class Errors",
            description="Understand Java's package system and how to import utility classes like Scanner and ArrayList.",
            key_takeaway="Classes outside java.lang must be imported at the top of the file (e.g. import java.util.Scanner;)."
        )
    ]
}


@router.get(
    "/insights",
    response_model=InsightsResponse,
    summary="Get Personalized Learning Insights",
    description="Calculates comprehensive learning analytics including error taxonomy distribution percentages, dominant error categories, learning trajectory trends, and actionable topic recommendations."
)
def get_insights(db: Session = Depends(get_db)):
    """Generate personalized insights, error profile distribution, and recommendations."""
    total_submissions = db.query(Submission).count()
    successful_compilations = db.query(Submission).filter(Submission.compile_success == True).count()

    errors = db.query(CompilerErrorRecord).all()
    total_errors = len(errors)

    if total_errors == 0:
        # Default starter insights when no errors exist
        return InsightsResponse(
            total_submissions=total_submissions,
            total_errors=0,
            successful_compilations=successful_compilations,
            most_common_category="None yet",
            most_common_error="No errors recorded",
            category_distribution=[],
            recommendations=[
                RecommendedTopic(
                    title="Getting Started with Java",
                    category="Basics",
                    description="Run your first program through CodeSense to begin tracking your error profile.",
                    key_takeaway="Compile early and frequently to catch errors right when they are typed."
                )
            ],
            improvement_trend="No errors recorded yet. Analyze code to generate your error profile!"
        )

    # Calculate category counts
    category_counts = Counter(e.category for e in errors)
    subcategory_counts = Counter(e.subcategory or e.compiler_message for e in errors)

    distribution: List[CategoryBreakdown] = []
    category_display_names = {
        "TYPE_ERROR": "Type Errors",
        "SYNTAX_ERROR": "Syntax Errors",
        "VARIABLE_ERROR": "Variable Errors",
        "METHOD_ERROR": "Method Errors",
        "CLASS_ERROR": "Class Errors",
        "ACCESS_ERROR": "Access Errors",
        "CODE_QUALITY": "Code Quality"
    }

    for cat, count in category_counts.most_common():
        pct = round((count / total_errors) * 100, 1)
        distribution.append(CategoryBreakdown(
            category=cat,
            count=count,
            percentage=pct,
            display_name=category_display_names.get(cat, cat.replace("_", " ").title())
        ))

    most_common_cat = category_counts.most_common(1)[0][0]
    most_common_sub = subcategory_counts.most_common(1)[0][0].replace("_", " ").title()

    # Pick recommended topics tailored to student's most frequent categories
    recommendations: List[RecommendedTopic] = []
    for cat, _ in category_counts.most_common(3):
        if cat in RECOMMENDATION_TOPICS_MAP:
            recommendations.extend(RECOMMENDATION_TOPICS_MAP[cat])

    if not recommendations:
        recommendations = RECOMMENDATION_TOPICS_MAP["TYPE_ERROR"]

    # Trend description
    if total_submissions > 3:
        recent_subs = db.query(Submission).order_by(Submission.created_at.desc()).limit(3).all()
        recent_clean = sum(1 for s in recent_subs if s.compile_success)
        if recent_clean >= 2:
            trend = f"Strong improvement: {recent_clean} of your last 3 submissions compiled cleanly without errors!"
        else:
            trend = f"Frequent pattern detected: Most errors are related to {category_display_names.get(most_common_cat, most_common_cat)}."
    else:
        trend = "Initial baseline established. Keep compiling to monitor improvement trends."

    return InsightsResponse(
        total_submissions=total_submissions,
        total_errors=total_errors,
        successful_compilations=successful_compilations,
        most_common_category=category_display_names.get(most_common_cat, most_common_cat),
        most_common_error=most_common_sub,
        category_distribution=distribution,
        recommendations=recommendations[:4],
        improvement_trend=trend
    )
