import axios from 'axios';
import {
  AnalysisResponse,
  HistoryResponse,
  InsightsResponse,
  HealthData,
  AIExplanationResponse,
  ParsedCompilerError,
  ClassificationResult
} from '../types';

const getApiBaseUrl = (): string => {
  const envUrl = import.meta.env.VITE_API_URL;
  if (envUrl && envUrl.trim() !== '') {
    return envUrl.trim().replace(/\/$/, '');
  }
  // Default to live OpenJDK Render backend
  return 'https://codesense-api-5618.onrender.com';
};

const API_BASE_URL = getApiBaseUrl();

const api = axios.create({
  baseURL: `${API_BASE_URL}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (!error.response) {
      error.message = `Unable to connect to CodeSense backend at ${API_BASE_URL}. Make sure the CodeSense backend is running.`;
    } else if (error.response.data?.detail) {
      error.message = typeof error.response.data.detail === 'string'
        ? error.response.data.detail
        : JSON.stringify(error.response.data.detail);
    }
    return Promise.reject(error);
  }
);

export const analyzeCode = async (sourceCode: string, language: string = 'java'): Promise<AnalysisResponse> => {
  const res = await api.post<AnalysisResponse>('/analyze', {
    language,
    source_code: sourceCode,
    user_id: 'guest',
  });
  return res.data;
};

export const compileCodeOnly = async (sourceCode: string, language: string = 'java') => {
  const res = await api.post('/compile', {
    language,
    source_code: sourceCode,
  });
  return res.data;
};

export const explainError = async (
  sourceCode: string,
  error: ParsedCompilerError,
  classification?: ClassificationResult
): Promise<AIExplanationResponse> => {
  const res = await api.post<AIExplanationResponse>('/explain', {
    language: 'java',
    source_code: sourceCode,
    error,
    classification,
  });
  return res.data;
};

export const getHistory = async (limit: number = 50, offset: number = 0): Promise<HistoryResponse> => {
  const res = await api.get<HistoryResponse>('/history', {
    params: { limit, offset },
  });
  return res.data;
};

export const getSubmissionDetail = async (submissionId: string): Promise<AnalysisResponse> => {
  const res = await api.get<AnalysisResponse>(`/history/${submissionId}`);
  return res.data;
};

export const getInsights = async (): Promise<InsightsResponse> => {
  const res = await api.get<InsightsResponse>('/insights');
  return res.data;
};

export const getHealth = async (): Promise<HealthData> => {
  const res = await api.get<HealthData>('/health');
  return res.data;
};
