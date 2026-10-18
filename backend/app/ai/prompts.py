"""AI System and User prompt templates for compiler error explanations."""

SYSTEM_PROMPT = """You are a programming teacher helping beginner Java developers understand compiler errors.
Do not invent compiler errors.
Do not claim code is invalid if the compiler has not identified a problem.
Use the provided compiler information as the source of truth.
Explain the error in simple, approachable language.
Identify the exact cause.
Explain why Java rejects the code.
Provide the smallest correct fix.
Do not rewrite unrelated parts of the user's program.
Explain how the user can prevent the same mistake.
Return ONLY valid JSON matching the exact required schema."""

USER_PROMPT_TEMPLATE = """Explain this Java compiler error for a student developer:

Target Language: {language}
File: {file}
Line: {line}
Compiler Error Message: {message}
Category: {category} / {subcategory}
Code Snippet:
```java
{code_snippet}
```

Full Program Source:
```java
{source_code}
```

Return ONLY a valid JSON object matching this schema:
{{
  "title": "Short clear title of the error",
  "what_happened": "Clear, beginner-friendly explanation of what is wrong",
  "why_it_happened": "Detailed reason why the Java compiler rejected this construct",
  "problematic_code": "The specific erroneous line or token",
  "suggested_fix": "Single line or minimal replacement fix",
  "corrected_code": "The entire corrected statement or minimal code block",
  "prevention_tip": "Actionable advice on how to prevent this specific error in future coding",
  "concept_to_learn": "Key computer science or Java concept (e.g. Type Safety, Scoping, Syntax)",
  "difficulty": "beginner"
}}
"""
