# Requirements Document

## Introduction

Gambling Comment Detector adalah sistem untuk mendeteksi komentar judi online pada video YouTube menggunakan Machine Learning. Sistem ini memungkinkan pengguna untuk login dengan akun YouTube, melakukan scan komentar pada video sendiri atau video publik, dan menghapus komentar judi yang terdeteksi. Sistem terdiri dari backend FastAPI dengan ML model, frontend Next.js (Horizon UI), dan infrastruktur Docker dengan PostgreSQL, Redis, dan Celery.

## Glossary

- **System**: Gambling Comment Detector application
- **User**: Authenticated person using the application via YouTube OAuth
- **Scan**: Process of analyzing comments on a YouTube video for gambling content
- **Gambling_Comment**: A comment identified by the ML model as containing gambling-related content
- **ML_Model**: Pre-trained scikit-learn pipeline (model_pipeline.joblib) for text classification
- **Prediction_Service**: Backend service that loads and runs the ML model
- **YouTube_API**: Google YouTube Data API v3 for fetching videos and comments
- **OAuth_Flow**: Google OAuth 2.0 authentication process
- **JWT**: JSON Web Token used for session management
- **Celery_Worker**: Background task processor for async operations
- **Confidence_Score**: Float value (0-1) indicating ML model's certainty about prediction

## Requirements

### Requirement 1: User Authentication

**User Story:** As a user, I want to login with my YouTube/Google account, so that I can access my videos and manage comments.

#### Acceptance Criteria

1. WHEN a user clicks the login button THEN the System SHALL redirect to Google OAuth consent screen with required YouTube scopes
2. WHEN Google OAuth callback is received with valid authorization code THEN the System SHALL exchange the code for access and refresh tokens
3. WHEN OAuth tokens are obtained THEN the System SHALL create or update the user record in the database with encrypted tokens
4. WHEN authentication succeeds THEN the System SHALL issue a JWT token with user information
5. WHEN a user requests token refresh THEN the System SHALL validate the refresh token and issue new access token
6. WHEN a user logs out THEN the System SHALL revoke OAuth tokens and invalidate the session
7. IF OAuth callback contains an error parameter THEN the System SHALL redirect to login page with appropriate error message

### Requirement 2: ML Prediction Service

**User Story:** As a system operator, I want the ML model to classify comments accurately, so that gambling content can be identified reliably.

#### Acceptance Criteria

1. WHEN the application starts THEN the Prediction_Service SHALL load the ML_Model from backend/ml/model_pipeline.joblib
2. WHEN a single comment text is submitted for prediction THEN the Prediction_Service SHALL return is_gambling boolean and confidence_score
3. WHEN a batch of comment texts is submitted THEN the Prediction_Service SHALL process all texts and return predictions for each
4. WHEN prediction is requested THEN the Prediction_Service SHALL return confidence_score as a float between 0.0 and 1.0
5. WHEN the ML_Model file is missing or corrupted THEN the Prediction_Service SHALL raise a descriptive error and prevent application startup
6. WHEN serializing prediction results THEN the Prediction_Service SHALL produce valid JSON that can be deserialized back to equivalent prediction objects (round-trip consistency)

### Requirement 3: Video Scanning

**User Story:** As a user, I want to scan YouTube video comments for gambling content, so that I can identify and manage spam comments.

#### Acceptance Criteria

1. WHEN a user submits a video URL or ID for scanning THEN the System SHALL create a scan record with status "pending"
2. WHEN a scan is created THEN the Celery_Worker SHALL fetch all comments from the YouTube_API
3. WHEN comments are fetched THEN the Prediction_Service SHALL classify each comment as gambling or clean
4. WHEN classification completes THEN the System SHALL store results in scan_results table with comment details and predictions
5. WHEN scan completes successfully THEN the System SHALL update scan status to "completed" with gambling_count and clean_count
6. IF YouTube_API returns an error THEN the System SHALL update scan status to "failed" with error_message
7. WHILE scan is processing THEN the System SHALL allow status polling via GET /api/scan/{scan_id}/status

### Requirement 4: User's Own Videos

**User Story:** As a user, I want to view and scan my own YouTube videos, so that I can manage comments on my channel.

#### Acceptance Criteria

1. WHEN an authenticated user requests their videos THEN the System SHALL fetch videos from YouTube_API using the user's OAuth token
2. WHEN displaying user videos THEN the System SHALL show video title, thumbnail, and view count
3. WHEN a user scans their own video THEN the System SHALL enable the delete comment functionality
4. WHEN fetching user videos THEN the System SHALL handle pagination with pageToken parameter

### Requirement 5: Public Video Browsing

**User Story:** As a user, I want to search and scan public YouTube videos, so that I can analyze gambling comments on any video.

#### Acceptance Criteria

1. WHEN a user searches for videos THEN the System SHALL query YouTube_API search endpoint with the search term
2. WHEN displaying search results THEN the System SHALL show video title, channel name, thumbnail, and publish date
3. WHEN a user scans a public video THEN the System SHALL perform prediction but disable delete functionality
4. WHEN search returns no results THEN the System SHALL display appropriate empty state message

### Requirement 6: Comment Deletion

**User Story:** As a channel owner, I want to delete gambling comments from my videos, so that I can keep my channel clean.

#### Acceptance Criteria

1. WHEN a user requests to delete a single comment THEN the System SHALL call YouTube_API comments.delete with the comment_id
2. WHEN a user requests bulk deletion THEN the System SHALL delete each comment sequentially with rate limiting
3. WHEN comment deletion succeeds THEN the System SHALL return 204 status and update local records
4. IF comment deletion fails due to permission error THEN the System SHALL return appropriate error message indicating ownership requirement
5. IF comment deletion fails due to API quota THEN the System SHALL queue remaining deletions for retry

### Requirement 7: Dashboard and Statistics

**User Story:** As a user, I want to see statistics about my scans, so that I can understand gambling comment patterns.

#### Acceptance Criteria

1. WHEN a user views the dashboard THEN the System SHALL display total scans, total comments analyzed, and gambling detection rate
2. WHEN displaying chart data THEN the System SHALL provide time-series data for scans over the past 30 days
3. WHEN a user requests scan history THEN the System SHALL return paginated list of past scans with summary statistics
4. WHEN a user views scan details THEN the System SHALL display all detected comments with confidence scores

### Requirement 8: Data Export

**User Story:** As a user, I want to export scan results, so that I can analyze data externally or keep records.

#### Acceptance Criteria

1. WHEN a user requests CSV export THEN the System SHALL generate a CSV file with comment_id, text, author, is_gambling, and confidence columns
2. WHEN a user requests JSON export THEN the System SHALL generate a JSON file with complete scan results
3. WHEN export is generated THEN the System SHALL include scan metadata (video_id, video_title, scan_date)
4. WHEN serializing export data THEN the System SHALL produce output that can be parsed back to equivalent data structures (round-trip consistency)

### Requirement 9: Background Task Processing

**User Story:** As a system operator, I want scans to run asynchronously, so that the API remains responsive during long operations.

#### Acceptance Criteria

1. WHEN a scan is initiated THEN the System SHALL queue the task in Celery and return task_id immediately
2. WHEN Celery_Worker processes a scan task THEN the System SHALL update scan status progressively
3. WHEN multiple scans are queued THEN the Celery_Worker SHALL process them with configured concurrency limits
4. WHEN a task fails THEN the Celery_Worker SHALL retry with exponential backoff up to 3 times
5. WHILE tasks are running THEN the System SHALL allow monitoring via Flower dashboard on port 5555

### Requirement 10: Database Persistence

**User Story:** As a system operator, I want data to be persisted reliably, so that user data and scan results are not lost.

#### Acceptance Criteria

1. WHEN a user authenticates THEN the System SHALL store user record with encrypted OAuth tokens
2. WHEN a scan completes THEN the System SHALL store all scan_results with foreign key to scan record
3. WHEN a user is deleted THEN the System SHALL cascade delete all associated scans and results
4. WHEN database operations fail THEN the System SHALL rollback transactions and return appropriate error
5. WHEN storing timestamps THEN the System SHALL use UTC timezone consistently

### Requirement 11: API Security

**User Story:** As a system operator, I want the API to be secure, so that user data is protected.

#### Acceptance Criteria

1. WHEN a request lacks valid JWT token on protected endpoints THEN the System SHALL return 401 Unauthorized
2. WHEN a JWT token is expired THEN the System SHALL return 401 with token_expired error code
3. WHEN storing OAuth tokens THEN the System SHALL encrypt tokens before database storage
4. WHEN handling requests THEN the System SHALL validate all input using Pydantic schemas
5. IF request contains malformed data THEN the System SHALL return 422 with validation error details

### Requirement 12: Rate Limiting and Quotas

**User Story:** As a system operator, I want to manage API usage, so that YouTube API quotas are not exceeded.

#### Acceptance Criteria

1. WHEN calling YouTube_API THEN the System SHALL respect rate limits of 10 requests per minute for scan operations
2. WHEN calling prediction endpoint THEN the System SHALL allow up to 30 requests per minute
3. IF YouTube API quota is exceeded THEN the System SHALL return 429 status with retry-after header
4. WHEN processing bulk operations THEN the System SHALL implement delays between API calls
