/**
 * Library exports for Gambling Comment Detector
 */

// API client utilities
export {
  api,
  apiRequest,
  get,
  post,
  put,
  patch,
  del,
  getAccessToken,
  getRefreshToken,
  setTokens,
  clearTokens,
  ApiError,
  type RequestOptions,
} from './api';

// TypeScript types
export type {
  // User types
  UserBase,
  UserResponse,
  TokenResponse,
  // Scan types
  ScanCreate,
  ScanResponse,
  ScanStatus,
  ScanResultResponse,
  ScanDetailResponse,
  ScanListResponse,
  // Prediction types
  PredictionRequest,
  PredictionResponse,
  BatchPredictionResponse,
  // YouTube types
  VideoInfo,
  CommentInfo,
  VideoListResponse,
  CommentListResponse,
  // Dashboard types
  DashboardStats,
  ChartDataPoint,
  ChartData,
  // Error types
  ErrorResponse,
  ValidationErrorDetail,
  ValidationErrorResponse,
  // Task types
  TaskStatus,
  TaskStatusResponse,
  // Bulk operation types
  BulkDeleteResponse,
} from './types';
