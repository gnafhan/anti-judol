/**
 * API Client utilities for Gambling Comment Detector
 * 
 * Provides fetch configuration with authentication header injection
 * and automatic token refresh on 401 responses.
 * 
 * Requirements: 11.1, 11.2
 */

import type {
  UserResponse,
  TokenResponse,
  PredictionResponse,
  BatchPredictionResponse,
  ScanResponse,
  ScanListResponse,
  ScanDetailResponse,
  VideoInfo,
  VideoListResponse,
  CommentListResponse,
  DashboardStats,
  ChartData,
  ValidationResponse,
  ValidationStats,
  BatchValidationResult,
  BatchAction,
  ModelMetricsDisplay,
  ModelImprovementDisplay,
  ValidationContributionDisplay,
  ModelVersionFull,
  ModelMetricsAdmin,
  MetricsTrendResponse,
  RetrainingProgressResponse,
  RetrainingResponse,
  RollbackResponse,
  RetrainingPreviewResponse,
} from 'lib/types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Token storage keys
const ACCESS_TOKEN_KEY = 'access_token';
const REFRESH_TOKEN_KEY = 'refresh_token';

/**
 * Get stored access token from localStorage
 */
export function getAccessToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

/**
 * Get stored refresh token from localStorage
 */
export function getRefreshToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

/**
 * Store tokens in localStorage
 */
export function setTokens(accessToken: string, refreshToken?: string): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
  if (refreshToken) {
    localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
  }
}


/**
 * Clear stored tokens (logout)
 */
export function clearTokens(): void {
  if (typeof window === 'undefined') return;
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
}

/**
 * API Error class for handling HTTP errors
 */
export class ApiError extends Error {
  constructor(
    public status: number,
    public statusText: string,
    public data?: unknown
  ) {
    super(`API Error: ${status} ${statusText}`);
    this.name = 'ApiError';
  }
}

/**
 * Attempt to refresh the access token using the refresh token
 */
async function refreshAccessToken(): Promise<string | null> {
  const refreshToken = getRefreshToken();
  if (!refreshToken) return null;

  try {
    const response = await fetch(`${API_BASE_URL}/api/auth/refresh`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    if (!response.ok) {
      clearTokens();
      return null;
    }

    const data = await response.json();
    setTokens(data.access_token, data.refresh_token);
    return data.access_token;
  } catch {
    clearTokens();
    return null;
  }
}

/**
 * Request options for API calls
 */
export interface RequestOptions extends Omit<RequestInit, 'body'> {
  body?: unknown;
  skipAuth?: boolean;
}


/**
 * Make an authenticated API request with automatic token refresh
 * 
 * @param endpoint - API endpoint (e.g., '/api/scan')
 * @param options - Request options
 * @returns Response data
 */
export async function apiRequest<T>(
  endpoint: string,
  options: RequestOptions = {}
): Promise<T> {
  const { body, skipAuth = false, headers: customHeaders, ...restOptions } = options;

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...customHeaders,
  };

  // Add authorization header if not skipped
  if (!skipAuth) {
    const token = getAccessToken();
    if (token) {
      (headers as Record<string, string>)['Authorization'] = `Bearer ${token}`;
    }
  }

  const config: RequestInit = {
    ...restOptions,
    headers,
  };

  if (body !== undefined) {
    config.body = JSON.stringify(body);
  }

  let response = await fetch(`${API_BASE_URL}${endpoint}`, config);

  // Handle 401 - attempt token refresh
  if (response.status === 401 && !skipAuth) {
    const newToken = await refreshAccessToken();
    
    if (newToken) {
      // Retry request with new token
      (headers as Record<string, string>)['Authorization'] = `Bearer ${newToken}`;
      response = await fetch(`${API_BASE_URL}${endpoint}`, {
        ...config,
        headers,
      });
    } else {
      // Redirect to login if refresh failed
      if (typeof window !== 'undefined') {
        window.location.href = '/auth/sign-in';
      }
      throw new ApiError(401, 'Unauthorized', { error: 'token_expired' });
    }
  }

  // Handle error responses
  if (!response.ok) {
    let errorData: unknown;
    try {
      errorData = await response.json();
    } catch {
      errorData = null;
    }
    throw new ApiError(response.status, response.statusText, errorData);
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return undefined as T;
  }

  return response.json();
}


// ============================================================================
// Convenience methods for common HTTP verbs
// ============================================================================

/**
 * GET request
 */
export function get<T>(endpoint: string, options?: RequestOptions): Promise<T> {
  return apiRequest<T>(endpoint, { ...options, method: 'GET' });
}

/**
 * POST request
 */
export function post<T>(endpoint: string, body?: unknown, options?: RequestOptions): Promise<T> {
  return apiRequest<T>(endpoint, { ...options, method: 'POST', body });
}

/**
 * PUT request
 */
export function put<T>(endpoint: string, body?: unknown, options?: RequestOptions): Promise<T> {
  return apiRequest<T>(endpoint, { ...options, method: 'PUT', body });
}

/**
 * PATCH request
 */
export function patch<T>(endpoint: string, body?: unknown, options?: RequestOptions): Promise<T> {
  return apiRequest<T>(endpoint, { ...options, method: 'PATCH', body });
}

/**
 * DELETE request
 */
export function del<T>(endpoint: string, options?: RequestOptions): Promise<T> {
  return apiRequest<T>(endpoint, { ...options, method: 'DELETE' });
}


// ============================================================================
// API Endpoints
// ============================================================================

export const api = {
  // Auth endpoints
  auth: {
    getGoogleAuthUrl: () => `${API_BASE_URL}/api/auth/google`,
    me: () => get<UserResponse>('/api/auth/me'),
    refresh: (refreshToken: string) => 
      post<TokenResponse>('/api/auth/refresh', { refresh_token: refreshToken }, { skipAuth: true }),
    logout: () => post<void>('/api/auth/logout'),
  },

  // Prediction endpoints
  predict: {
    single: (text: string) => 
      post<PredictionResponse>('/api/predict/single', { text }),
    batch: (texts: string[], asyncMode = false) => 
      post<BatchPredictionResponse>('/api/predict', { texts, async_mode: asyncMode }),
    taskStatus: (taskId: string) => 
      get<{ status: string; result?: BatchPredictionResponse }>(`/api/predict/task/${taskId}`),
  },

  // Scan endpoints
  scan: {
    create: (videoId: string, videoUrl?: string, isOwnVideo?: boolean) => 
      post<ScanResponse>('/api/scan', { video_id: videoId, video_url: videoUrl, is_own_video: isOwnVideo ?? false }),
    history: (page = 1, limit = 10) => 
      get<ScanListResponse>(`/api/scan/history?page=${page}&limit=${limit}`),
    get: (scanId: string) => 
      get<ScanDetailResponse>(`/api/scan/${scanId}`),
    status: (scanId: string) => 
      get<{ status: string; error_message?: string }>(`/api/scan/${scanId}/status`),
    delete: (scanId: string) => 
      del<void>(`/api/scan/${scanId}`),
  },

  // YouTube endpoints
  youtube: {
    myVideos: (pageToken?: string) => 
      get<VideoListResponse>(`/api/youtube/my-videos${pageToken ? `?page_token=${pageToken}` : ''}`),
    search: (query: string, pageToken?: string) => 
      get<VideoListResponse>(`/api/youtube/search?q=${encodeURIComponent(query)}${pageToken ? `&page_token=${pageToken}` : ''}`),
    video: (videoId: string) => 
      get<VideoInfo>(`/api/youtube/videos/${videoId}`),
    comments: (videoId: string, pageToken?: string) => 
      get<CommentListResponse>(`/api/youtube/videos/${videoId}/comments${pageToken ? `?page_token=${pageToken}` : ''}`),
    deleteComment: (commentId: string) => 
      del<void>(`/api/youtube/comments/${commentId}`),
    deleteCommentsBulk: (commentIds: string[]) => 
      del<{ deleted: string[]; failed: string[] }>('/api/youtube/comments/bulk', { body: { comment_ids: commentIds } }),
  },

  // Validation endpoints
  validation: {
    /** Submit a single validation */
    submit: (scanResultId: string, isCorrect: boolean, correctedLabel?: boolean) =>
      post<ValidationResponse>('/api/validation/submit', {
        scan_result_id: scanResultId,
        is_correct: isCorrect,
        corrected_label: correctedLabel,
      }),
    /** Submit batch validation */
    batch: (resultIds: string[], action: BatchAction) =>
      post<BatchValidationResult>('/api/validation/batch', {
        result_ids: resultIds,
        action,
      }),
    /** Undo a validation (within time window) */
    undo: (validationId: string) =>
      del<void>(`/api/validation/${validationId}`),
    /** Get validation statistics */
    stats: (userId?: string) => {
      const params = new URLSearchParams();
      if (userId) params.append('user_id', userId);
      const query = params.toString();
      return get<ValidationStats>(`/api/validation/stats${query ? `?${query}` : ''}`);
    },
    /** Get progress toward retraining threshold */
    progress: () =>
      get<{ progress_percent: number; pending_count: number; threshold: number }>('/api/validation/progress'),
    /** Get validations for a specific scan */
    forScan: (scanId: string) =>
      get<ValidationResponse[]>(`/api/validation/scan/${scanId}`),
  },

  // Dashboard endpoints
  dashboard: {
    stats: (videoIds?: string[], source?: string, startDate?: string, endDate?: string) => {
      const params = new URLSearchParams();
      if (videoIds && videoIds.length > 0) params.append('video_ids', videoIds.join(','));
      if (source && source !== 'all') params.append('source', source);
      if (startDate) params.append('start_date', startDate);
      if (endDate) params.append('end_date', endDate);
      const query = params.toString();
      return get<DashboardStats>(`/api/dashboard/stats${query ? `?${query}` : ''}`);
    },
    chartData: (videoIds?: string[], source?: string, days?: number) => {
      const params = new URLSearchParams();
      if (videoIds && videoIds.length > 0) params.append('video_ids', videoIds.join(','));
      if (source && source !== 'all') params.append('source', source);
      if (days) params.append('days', days.toString());
      const query = params.toString();
      return get<ChartData>(`/api/dashboard/chart-data${query ? `?${query}` : ''}`);
    },
    scannedVideos: (source?: string) => {
      const params = new URLSearchParams();
      if (source && source !== 'all') params.append('source', source);
      const query = params.toString();
      return get<{ videos: Array<{ video_id: string; video_title: string | null; video_thumbnail: string | null; channel_name: string | null; scan_count: number; last_scanned: string | null; is_own_video: boolean }> }>(`/api/dashboard/scanned-videos${query ? `?${query}` : ''}`);
    },
    topVideos: (videoIds?: string[], source?: string, limit?: number) => {
      const params = new URLSearchParams();
      if (videoIds && videoIds.length > 0) params.append('video_ids', videoIds.join(','));
      if (source && source !== 'all') params.append('source', source);
      if (limit) params.append('limit', limit.toString());
      const query = params.toString();
      return get<{ videos: Array<{ video_id: string; video_title: string | null; video_thumbnail: string | null; channel_name: string | null; gambling_count: number; clean_count: number; total_comments: number; detection_rate: number }> }>(`/api/dashboard/top-videos${query ? `?${query}` : ''}`);
    },
    exportCsv: (scanId: string) => 
      `${API_BASE_URL}/api/dashboard/export/${scanId}?format=csv`,
    exportJson: (scanId: string) => 
      `${API_BASE_URL}/api/dashboard/export/${scanId}?format=json`,
    /** Get model metrics for dashboard display (Requirements: 10.1) */
    modelMetrics: () =>
      get<ModelMetricsDisplay>('/api/dashboard/model-metrics'),
    /** Get model improvement notification data (Requirements: 10.2) */
    modelImprovement: () =>
      get<ModelImprovementDisplay>('/api/dashboard/model-improvement'),
    /** Get user's validation contribution statistics (Requirements: 10.3) */
    validationContributions: () =>
      get<ValidationContributionDisplay>('/api/dashboard/validation-contributions'),
  },

  // Model management endpoints (Admin)
  model: {
    /** Get all model versions */
    versions: (limit = 10) =>
      get<ModelVersionFull[]>(`/api/model/versions?limit=${limit}`),
    /** Get current active model */
    current: () =>
      get<ModelVersionFull | null>('/api/model/current'),
    /** Get model metrics */
    metrics: () =>
      get<ModelMetricsAdmin>('/api/model/metrics'),
    /** Get metrics trend over versions */
    metricsTrend: (limit = 10) =>
      get<MetricsTrendResponse>(`/api/model/metrics/trend?limit=${limit}`),
    /** Get training progress */
    trainingProgress: () =>
      get<RetrainingProgressResponse>('/api/model/training/progress'),
    /** Trigger manual retraining (async) */
    retrain: () =>
      post<RetrainingResponse>('/api/model/retrain'),
    /** Get retraining task status */
    taskStatus: (taskId: string) =>
      get<import('lib/types').RetrainingTaskStatus>(`/api/model/training/task/${taskId}`),
    /** Rollback to a previous version */
    rollback: (versionId: string) =>
      post<RollbackResponse>(`/api/model/rollback/${versionId}`),
    /** Get retraining preview */
    retrainPreview: () =>
      get<RetrainingPreviewResponse>('/api/model/retrain/preview'),
  },
};

export default api;
