/**
 * TypeScript types matching backend Pydantic schemas
 * 
 * These types ensure type safety between frontend and backend.
 * Requirements: Type safety
 */

// ============================================================================
// User Types (from backend/app/schemas/user.py)
// ============================================================================

/**
 * Base user information
 */
export interface UserBase {
  email: string;
  name: string | null;
  avatar_url: string | null;
}

/**
 * User response from API endpoints
 */
export interface UserResponse extends UserBase {
  id: string;
  google_id: string;
  created_at: string;
}

/**
 * Token response from authentication
 */
export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: UserResponse;
}

// ============================================================================
// Scan Types (from backend/app/schemas/scan.py)
// ============================================================================

/**
 * Request to create a new scan
 */
export interface ScanCreate {
  video_id: string;
  video_url?: string | null;
}

/**
 * Basic scan response
 */
export interface ScanResponse {
  id: string;
  video_id: string;
  video_title: string | null;
  status: ScanStatus;
  task_id: string | null;
  created_at: string;
}


/**
 * Scan status enum
 */
export type ScanStatus = 'pending' | 'processing' | 'completed' | 'failed';

/**
 * Individual scan result (comment prediction)
 */
export interface ScanResultResponse {
  id: string;
  comment_id: string;
  comment_text: string;
  author_name: string | null;
  is_gambling: boolean;
  confidence: number;
}

/**
 * Detailed scan response with results
 */
export interface ScanDetailResponse extends ScanResponse {
  video_thumbnail: string | null;
  channel_name: string | null;
  total_comments: number;
  gambling_count: number;
  clean_count: number;
  scanned_at: string | null;
  results: ScanResultResponse[];
}

/**
 * Paginated list of scans
 */
export interface ScanListResponse {
  items: ScanResponse[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}

// ============================================================================
// Prediction Types (from backend/app/schemas/prediction.py)
// ============================================================================

/**
 * Request for batch prediction
 */
export interface PredictionRequest {
  texts: string[];
  async_mode?: boolean;
}

/**
 * Single prediction response
 */
export interface PredictionResponse {
  text: string;
  is_gambling: boolean;
  confidence: number;
}

/**
 * Batch prediction response
 */
export interface BatchPredictionResponse {
  predictions: PredictionResponse[];
  task_id: string | null;
}

// ============================================================================
// YouTube Types (from backend/app/schemas/youtube.py)
// ============================================================================

/**
 * YouTube video information
 */
export interface VideoInfo {
  id: string;
  title: string;
  description: string | null;
  thumbnail_url: string;
  channel_name: string;
  channel_id: string;
  view_count: number;
  comment_count: number;
  published_at: string;
}

/**
 * YouTube comment information
 */
export interface CommentInfo {
  id: string;
  text: string;
  author_name: string;
  author_avatar: string | null;
  author_channel_id: string | null;
  like_count: number;
  published_at: string;
}

/**
 * Paginated video list response
 */
export interface VideoListResponse {
  items: VideoInfo[];
  next_page_token: string | null;
  total_results: number;
}

/**
 * Paginated comment list response
 */
export interface CommentListResponse {
  items: CommentInfo[];
  next_page_token: string | null;
  total_results: number;
}


// ============================================================================
// Dashboard Types
// ============================================================================

/**
 * Dashboard statistics
 */
export interface DashboardStats {
  total_scans: number;
  total_comments: number;
  gambling_comments: number;
  clean_comments: number;
  detection_rate: number;
}

/**
 * Chart data point for time series
 */
export interface ChartDataPoint {
  date: string;
  scans: number;
  gambling_count: number;
  clean_count: number;
}

/**
 * Chart data response
 */
export interface ChartData {
  data: ChartDataPoint[];
}

/**
 * Scanned video for filter dropdown
 */
export interface ScannedVideo {
  video_id: string;
  video_title: string | null;
  video_thumbnail: string | null;
  channel_name: string | null;
  scan_count: number;
  last_scanned: string | null;
}

/**
 * Scanned videos response
 */
export interface ScannedVideosResponse {
  videos: ScannedVideo[];
}

/**
 * Top video with gambling stats
 */
export interface TopVideo {
  video_id: string;
  video_title: string | null;
  video_thumbnail: string | null;
  channel_name: string | null;
  gambling_count: number;
  clean_count: number;
  total_comments: number;
  detection_rate: number;
}

/**
 * Top videos response
 */
export interface TopVideosResponse {
  videos: TopVideo[];
}

/**
 * Dashboard filter state
 */
export interface DashboardFilters {
  videoIds: string[];
  startDate: string | null;
  endDate: string | null;
  days: number;
}

// ============================================================================
// Error Types
// ============================================================================

/**
 * API error response
 */
export interface ErrorResponse {
  error: string;
  error_code: string;
  message: string;
  details?: Record<string, unknown>;
}

/**
 * Validation error detail
 */
export interface ValidationErrorDetail {
  loc: (string | number)[];
  msg: string;
  type: string;
}

/**
 * Validation error response (422)
 */
export interface ValidationErrorResponse {
  detail: ValidationErrorDetail[];
}

// ============================================================================
// Task Status Types
// ============================================================================

/**
 * Async task status
 */
export type TaskStatus = 'pending' | 'started' | 'success' | 'failure' | 'retry';

/**
 * Task status response
 */
export interface TaskStatusResponse<T = unknown> {
  task_id: string;
  status: TaskStatus;
  result?: T;
  error?: string;
}

// ============================================================================
// Bulk Operation Types
// ============================================================================

/**
 * Bulk delete response
 */
export interface BulkDeleteResponse {
  deleted: string[];
  failed: string[];
}

// ============================================================================
// Validation Types (from backend/app/schemas/validation.py)
// ============================================================================

/**
 * Request to submit a single validation
 */
export interface ValidationSubmit {
  scan_result_id: string;
  is_correct: boolean;
  corrected_label?: boolean | null;
}

/**
 * Batch validation action type
 */
export type BatchAction = 'confirm_all' | 'mark_gambling' | 'mark_clean';

/**
 * Request to submit batch validation
 */
export interface BatchValidationSubmit {
  result_ids: string[];
  action: BatchAction;
}

/**
 * Validation response from API
 */
export interface ValidationResponse {
  id: string;
  scan_result_id: string;
  is_correction: boolean;
  corrected_label: boolean;
  validated_at: string;
  can_undo: boolean;
}

/**
 * Validation statistics
 */
export interface ValidationStats {
  total_validated: number;
  corrections_made: number;
  pending_for_training: number;
  threshold: number;
  progress_percent: number;
}

/**
 * Batch validation result
 */
export interface BatchValidationResult {
  total_submitted: number;
  successful: number;
  failed: number;
  validations: ValidationResponse[];
  errors: string[];
}

/**
 * Full validation feedback record (matches ValidationFeedback SQLAlchemy model)
 */
export interface ValidationFeedback {
  id: string;
  scan_result_id: string;
  user_id: string;
  comment_text: string;
  original_prediction: boolean;
  original_confidence: number;
  corrected_label: boolean;
  is_correction: boolean;
  validated_at: string;
  used_in_training: boolean;
  model_version_id: string | null;
}

/**
 * Validation error response
 */
export interface ValidationError {
  error: string;
  error_code: string;
  message: string;
  details?: Record<string, unknown> | null;
}

// ============================================================================
// Model Version Types (from backend/app/schemas/model.py)
// ============================================================================

/**
 * Model version information (matches ModelVersion SQLAlchemy model)
 */
export interface ModelVersion {
  id: string;
  version: string;
  file_path: string;
  training_samples: number;
  validation_samples: number;
  accuracy: number | null;
  precision_score: number | null;
  recall_score: number | null;
  f1_score: number | null;
  is_active: boolean;
  created_at: string;
  activated_at: string | null;
  deactivated_at: string | null;
}

/**
 * Model version response (simplified for API responses)
 */
export interface ModelVersionResponse {
  id: string;
  version: string;
  accuracy: number | null;
  is_active: boolean;
  created_at: string;
  training_samples: number;
  validation_samples: number;
}

/**
 * Model metrics for dashboard display
 */
export interface ModelMetrics {
  current_version: string;
  accuracy: number | null;
  precision: number | null;
  recall: number | null;
  f1_score: number | null;
  training_samples: number;
  validation_samples: number;
  last_trained: string | null;
}

/**
 * Model improvement notification data
 */
export interface ModelImprovement {
  previous_version: string;
  new_version: string;
  accuracy_change: number;
  improvement_percent: number;
  deployed_at: string;
}

/**
 * Model metrics for dashboard display (Requirements: 10.1)
 */
export interface ModelMetricsDisplay {
  current_version: string | null;
  accuracy: number | null;
  precision: number | null;
  recall: number | null;
  f1_score: number | null;
  training_samples: number | null;
  validation_samples: number | null;
  last_trained: string | null;
}

/**
 * Model improvement notification for dashboard (Requirements: 10.2)
 */
export interface ModelImprovementDisplay {
  has_improvement: boolean;
  previous_version: string | null;
  new_version: string | null;
  accuracy_change: number | null;
  improvement_percent: number | null;
  deployed_at: string | null;
}

/**
 * User's validation contribution statistics (Requirements: 10.3)
 */
export interface ValidationContributionDisplay {
  total_validations: number;
  contributed_to_training: number;
  corrections_made: number;
  model_versions_contributed: number;
}

// ============================================================================
// Model Management Types (Admin)
// ============================================================================

/**
 * Full model version response from admin API
 */
export interface ModelVersionFull {
  id: string;
  version: string;
  accuracy: number | null;
  precision_score: number | null;
  recall_score: number | null;
  f1_score: number | null;
  is_active: boolean;
  training_samples: number;
  validation_samples: number;
  created_at: string;
  activated_at: string | null;
  deactivated_at: string | null;
}

/**
 * Model metrics response
 */
export interface ModelMetricsAdmin {
  current_version: string | null;
  accuracy: number | null;
  precision: number | null;
  recall: number | null;
  f1: number | null;
  training_samples: number | null;
  validation_samples: number | null;
  total_versions: number;
  pending_validations: number;
}

/**
 * Single point in metrics trend
 */
export interface MetricsTrendPoint {
  version: string;
  accuracy: number | null;
  precision: number | null;
  recall: number | null;
  f1: number | null;
  created_at: string;
}

/**
 * Metrics trend response
 */
export interface MetricsTrendResponse {
  trend: MetricsTrendPoint[];
  improvement_summary: {
    accuracy_change?: number;
    accuracy_percent?: number;
    f1_change?: number;
    f1_percent?: number;
  };
}

/**
 * Retraining progress response
 */
export interface RetrainingProgressResponse {
  is_training: boolean;
  current_step: string | null;
  progress_percent: number;
  started_at: string | null;
  estimated_completion: string | null;
  error_message: string | null;
}

/**
 * Retraining response (async start)
 */
export interface RetrainingResponse {
  success: boolean;
  message: string;
  task_id: string | null;
}

/**
 * Retraining task status response
 */
export interface RetrainingTaskStatus {
  task_id: string;
  status: 'PENDING' | 'STARTED' | 'PROGRESS' | 'SUCCESS' | 'FAILURE' | 'RETRY';
  progress: number | null;
  stage: string | null;
  message: string | null;
  result: {
    status: string;
    model_version?: string;
    model_version_id?: string;
    metrics?: {
      accuracy: number;
      precision: number;
      recall: number;
      f1: number;
      training_samples: number;
      validation_samples: number;
    };
    reason?: string;
    message?: string;
  } | null;
}

/**
 * Rollback response
 */
export interface RollbackResponse {
  success: boolean;
  message: string;
  model_version: ModelVersionFull | null;
}

/**
 * Retraining preview response
 */
export interface RetrainingPreviewResponse {
  original_dataset_samples: number;
  total_validations: number;  // All validations (used + unused)
  pending_validations: number;  // Only new/unused validations
  total_samples_after_training: number;
  corrections_count: number;
  confirmations_count: number;
  current_model_version: string | null;
  current_model_accuracy: number | null;
  can_retrain: boolean;
  message: string | null;
}
