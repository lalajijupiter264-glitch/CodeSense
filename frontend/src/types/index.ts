export interface ParsedCompilerError {
  id: string;
  file: string;
  line: number;
  column?: number | null;
  severity: string;
  message: string;
  compiler_code: string;
  code_snippet?: string | null;
  symbol?: string | null;
  location?: string | null;
  is_primary: boolean;
}

export interface ClassificationResult {
  category: string;
  subcategory: string;
  severity: string;
  confidence: number;
  description: string;
}

export interface AIExplanationResponse {
  title: string;
  what_happened: string;
  why_it_happened: string;
  problematic_code: string;
  suggested_fix: string;
  corrected_code?: string | null;
  prevention_tip: string;
  concept_to_learn?: string | null;
  difficulty: string;
  ai_generated: boolean;
  fix_available?: boolean;
  fix_confidence?: number;
  original_code?: string | null;
  changed_lines?: number[];
  fix_explanation?: string | null;
  validated?: boolean;
}

export interface StaticWarning {
  id: string;
  rule_id: string;
  severity: string;
  line: number;
  column?: number | null;
  title: string;
  message: string;
  why_it_matters: string;
  suggestion: string;
  is_potential: boolean;
}

export interface ErrorDetail {
  error: ParsedCompilerError;
  classification: ClassificationResult;
  explanation?: AIExplanationResponse | null;
}

export interface AnalysisResponse {
  submission_id: string;
  language: string;
  success: boolean;

  exit_code: number;
  compilation_time_ms: number;
  raw_output: string;
  errors: ErrorDetail[];
  warnings: StaticWarning[];
  primary_error?: ErrorDetail | null;
  summary_message: string;
}

export interface SubmissionSummary {
  id: string;
  language: string;
  compile_success: boolean;
  error_count: number;
  warning_count: number;
  main_error_type?: string | null;
  main_error_message?: string | null;
  compilation_time_ms: number;
  created_at: string;
}

export interface HistoryResponse {
  total: number;
  submissions: SubmissionSummary[];
}

export interface CategoryBreakdown {
  category: string;
  count: number;
  percentage: number;
  display_name: string;
}

export interface RecommendedTopic {
  title: string;
  category: string;
  description: string;
  key_takeaway: string;
}

export interface InsightsResponse {
  total_submissions: number;
  total_errors: number;
  successful_compilations: number;
  most_common_category?: string | null;
  most_common_error?: string | null;
  category_distribution: CategoryBreakdown[];
  recommendations: RecommendedTopic[];
  improvement_trend: string;
}

export interface HealthData {
  status: string;
  app: string;
  environment: string;
  compiler?: {
    configured_path: string;
    available: boolean;
    version: string;
  };
  ai?: {
    enabled: boolean;
    model: string;
  };
  database?: {
    type: string;
    status: string;
  };
}
