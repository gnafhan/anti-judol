# Implementation Plan

## Phase 1: Backend Foundation

- [x] 1. Set up backend project structure and configuration
  - [x] 1.1 Create backend directory structure (app/, models/, schemas/, routers/, services/, workers/)
    - Initialize Python package with `__init__.py` files
    - Create requirements.txt with all dependencies
    - _Requirements: Project Structure_
  - [x] 1.2 Implement configuration management with Pydantic Settings
    - Create `app/config.py` with Settings class
    - Define all environment variables (DATABASE_URL, REDIS_URL, GOOGLE_CLIENT_ID, etc.)
    - _Requirements: Environment Variables_
  - [x] 1.3 Set up database connection with SQLAlchemy
    - Create `app/database.py` with async engine and session factory
    - Configure connection pooling
    - _Requirements: 10.1, 10.2_
  - [x] 1.4 Create FastAPI application entry point
    - Create `app/main.py` with FastAPI app instance
    - Configure CORS, middleware, and exception handlers
    - Include all routers
    - _Requirements: API Endpoints_

- [x] 2. Implement database models and migrations
  - [x] 2.1 Create User SQLAlchemy model
    - Define User model with all fields (id, google_id, email, name, avatar_url, tokens, timestamps)
    - Add indexes on google_id
    - _Requirements: 1.3, 10.1_
  - [x] 2.2 Create Scan and ScanResult SQLAlchemy models
    - Define Scan model with status, counts, and relationships
    - Define ScanResult model with prediction fields
    - Configure cascade delete relationships
    - _Requirements: 3.1, 3.4, 3.5, 10.2, 10.3_
  - [x] 2.3 Write property test for cascade delete
    - **Property 14: Cascade Delete Integrity**
    - **Validates: Requirements 10.3**
  - [x] 2.4 Set up Alembic for database migrations
    - Initialize Alembic configuration
    - Create initial migration for all tables
    - _Requirements: Database Schema_

- [-] 3. Implement Pydantic schemas
  - [x] 3.1 Create User schemas (UserBase, UserResponse, TokenResponse)
    - Define request/response models for auth endpoints
    - _Requirements: 1.4, 11.4_
  - [x] 3.2 Create Scan schemas (ScanCreate, ScanResponse, ScanDetailResponse, ScanListResponse)
    - Define models for scan CRUD operations
    - Include pagination support
    - _Requirements: 3.1, 7.3_
  - [x] 3.3 Create Prediction schemas (PredictionRequest, PredictionResponse, BatchPredictionResponse)
    - Define models with validation constraints (confidence 0-1, texts max 1000)
    - _Requirements: 2.2, 2.3, 2.4_
  - [x] 3.4 Create YouTube schemas (VideoInfo, CommentInfo, VideoListResponse, CommentListResponse)
    - Define models matching YouTube API response structure
    - _Requirements: 4.2, 5.2_
  - [x] 3.5 Write property test for input validation
    - **Property 17: Input Validation Enforcement**
    - **Validates: Requirements 11.4, 11.5**

- [x] 4. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Phase 2: Core Services

- [x] 5. Implement Auth Service
  - [x] 5.1 Create token encryption/decryption utilities
    - Implement encrypt_token() and decrypt_token() using cryptography library
    - Use Fernet symmetric encryption
    - _Requirements: 1.3, 10.1, 11.3_
  - [x] 5.2 Write property test for token encryption round-trip
    - **Property 2: Token Encryption Round-Trip**
    - **Validates: Requirements 1.3, 10.1, 11.3**
  - [x] 5.3 Implement JWT creation and verification
    - Create create_jwt() with user payload and expiration
    - Create verify_jwt() with signature validation
    - _Requirements: 1.4, 11.1, 11.2_
  - [x] 5.4 Write property test for JWT round-trip
    - **Property 1: JWT Round-Trip Consistency**
    - **Validates: Requirements 1.4**
  - [x] 5.5 Implement Google OAuth flow helpers
    - Create get_google_auth_url() with required scopes
    - Create exchange_code() for token exchange
    - Create refresh_google_token() for token refresh
    - _Requirements: 1.1, 1.2, 1.5_
  - [x] 5.6 Implement get_current_user dependency
    - Create FastAPI dependency for JWT validation
    - Handle expired tokens with appropriate error
    - _Requirements: 11.1, 11.2_
  - [x] 5.7 Write property test for authentication enforcement
    - **Property 16: Authentication Enforcement**
    - **Validates: Requirements 11.1, 11.2**

- [x] 6. Implement Prediction Service
  - [x] 6.1 Create ML model loading with singleton pattern
    - Implement load_model() class method
    - Handle missing model file with descriptive error
    - _Requirements: 2.1, 2.5_
  - [x] 6.2 Implement single and batch prediction methods
    - Create predict_single() returning is_gambling and confidence
    - Create predict_batch() for multiple texts
    - Ensure confidence is float between 0.0 and 1.0
    - _Requirements: 2.2, 2.3, 2.4_
  - [x] 6.3 Write property test for prediction output format
    - **Property 3: Prediction Output Format and Bounds**
    - **Validates: Requirements 2.2, 2.3, 2.4**
  - [x] 6.4 Write property test for prediction serialization round-trip
    - **Property 4: Prediction Serialization Round-Trip**
    - **Validates: Requirements 2.6**

- [x] 7. Implement YouTube Service
  - [x] 7.1 Create YouTube API client initialization
    - Support both OAuth credentials and API key modes
    - Build youtube client using google-api-python-client
    - _Requirements: 4.1, 5.1_
  - [x] 7.2 Implement video fetching methods
    - Create get_my_videos() for authenticated user's videos
    - Create search_videos() for public video search
    - Create get_video_details() for single video info
    - Handle pagination with pageToken
    - _Requirements: 4.1, 4.2, 4.4, 5.1, 5.2_
  - [x] 7.3 Write property test for video response format
    - **Property 8: Video Response Required Fields**
    - **Validates: Requirements 4.2, 5.2**
  - [x] 7.4 Implement comment fetching methods
    - Create get_comments() with pagination
    - Create get_all_comments() that fetches all pages
    - _Requirements: 3.2_
  - [x] 7.5 Implement comment deletion methods
    - Create delete_comment() for single deletion
    - Create delete_comments_bulk() with rate limiting delays
    - _Requirements: 6.1, 6.2, 6.3, 12.4_
  - [x] 7.6 Write property test for bulk deletion sequential processing
    - **Property 9: Bulk Deletion Sequential Processing**
    - **Validates: Requirements 6.2, 12.4**

- [x] 8. Implement Export Service
  - [x] 8.1 Create CSV export functionality
    - Generate CSV with required columns (comment_id, text, author, is_gambling, confidence)
    - Include scan metadata header
    - _Requirements: 8.1, 8.3_
  - [x] 8.2 Create JSON export functionality
    - Generate JSON with complete scan results and metadata
    - Ensure valid JSON structure
    - _Requirements: 8.2, 8.3_
  - [x] 8.3 Write property test for export completeness and round-trip
    - **Property 13: Export Completeness and Round-Trip**
    - **Validates: Requirements 8.1, 8.2, 8.3, 8.4**

- [x] 9. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Phase 3: API Routers

- [x] 10. Implement Auth Router
  - [x] 10.1 Create GET /api/auth/google endpoint
    - Generate OAuth URL with state parameter
    - Redirect to Google consent screen
    - _Requirements: 1.1_
  - [x] 10.2 Create GET /api/auth/google/callback endpoint
    - Exchange authorization code for tokens
    - Create/update user in database
    - Return JWT token
    - _Requirements: 1.2, 1.3, 1.4_
  - [x] 10.3 Create POST /api/auth/refresh endpoint
    - Validate refresh token
    - Issue new access token
    - _Requirements: 1.5_
  - [x] 10.4 Create POST /api/auth/logout endpoint
    - Revoke OAuth tokens
    - Invalidate session
    - _Requirements: 1.6_
  - [x] 10.5 Create GET /api/auth/me endpoint
    - Return current user info
    - _Requirements: 1.4_

- [x] 11. Implement Prediction Router
  - [x] 11.1 Create POST /api/predict endpoint
    - Accept batch of texts
    - Support sync and async modes
    - Return predictions with task_id for async
    - _Requirements: 2.2, 2.3_
  - [x] 11.2 Create POST /api/predict/single endpoint
    - Accept single text
    - Return prediction result
    - _Requirements: 2.2_
  - [x] 11.3 Create GET /api/predict/task/{task_id} endpoint
    - Return async task status and results
    - _Requirements: 9.1_

- [x] 12. Implement Scan Router
  - [x] 12.1 Create POST /api/scan endpoint
    - Create scan record with pending status
    - Queue Celery task
    - Return scan_id and task_id
    - _Requirements: 3.1, 9.1_
  - [x] 12.2 Write property test for scan creation status
    - **Property 5: Scan Creation Status Invariant**
    - **Validates: Requirements 3.1, 9.1**
  - [x] 12.3 Create GET /api/scan/history endpoint
    - Return paginated scan list
    - Include summary statistics
    - _Requirements: 7.3_
  - [x] 12.4 Write property test for scan history pagination
    - **Property 12: Scan History Pagination**
    - **Validates: Requirements 7.3**
  - [x] 12.5 Create GET /api/scan/{scan_id} endpoint
    - Return scan details with all results
    - _Requirements: 7.4_
  - [x] 12.6 Create GET /api/scan/{scan_id}/status endpoint
    - Return current scan status for polling
    - _Requirements: 3.7_
  - [x] 12.7 Create DELETE /api/scan/{scan_id} endpoint
    - Delete scan and cascade to results
    - _Requirements: 10.3_

- [x] 13. Implement YouTube Router
  - [x] 13.1 Create GET /api/youtube/my-videos endpoint
    - Fetch authenticated user's videos
    - Support pagination
    - _Requirements: 4.1, 4.4_
  - [x] 13.2 Create GET /api/youtube/search endpoint
    - Search public videos
    - Return formatted results
    - _Requirements: 5.1, 5.2_
  - [x] 13.3 Create GET /api/youtube/videos/{video_id} endpoint
    - Get single video details
    - _Requirements: 4.2_
  - [x] 13.4 Create GET /api/youtube/videos/{video_id}/comments endpoint
    - Get video comments with pagination
    - _Requirements: 3.2_
  - [x] 13.5 Create DELETE /api/youtube/comments/{comment_id} endpoint
    - Delete single comment
    - Handle permission errors
    - _Requirements: 6.1, 6.3, 6.4_
  - [x] 13.6 Create DELETE /api/youtube/comments/bulk endpoint
    - Delete multiple comments with rate limiting
    - _Requirements: 6.2, 12.4_

- [x] 14. Implement Dashboard Router
  - [x] 14.1 Create GET /api/dashboard/stats endpoint
    - Calculate total scans, comments, detection rate
    - _Requirements: 7.1_
  - [x] 14.2 Write property test for dashboard stats calculation
    - **Property 10: Dashboard Stats Calculation**
    - **Validates: Requirements 7.1**
  - [x] 14.3 Create GET /api/dashboard/chart-data endpoint
    - Aggregate scan data for past 30 days
    - _Requirements: 7.2_
  - [x] 14.4 Write property test for chart data date range
    - **Property 11: Chart Data Date Range**
    - **Validates: Requirements 7.2**
  - [x] 14.5 Create GET /api/dashboard/export/{scan_id} endpoint
    - Support CSV and JSON formats
    - Include metadata
    - _Requirements: 8.1, 8.2, 8.3_

- [x] 15. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Phase 4: Background Workers

- [x] 16. Set up Celery configuration
  - [x] 16.1 Create Celery app configuration
    - Configure broker and backend (Redis)
    - Set up task queues (default, predictions, youtube)
    - Configure rate limits and retry policies
    - _Requirements: 9.1, 9.3, 12.1, 12.2_
  - [x] 16.2 Configure Celery Beat for scheduled tasks
    - Set up cleanup_old_results periodic task
    - _Requirements: 9.5_

- [x] 17. Implement Celery tasks
  - [x] 17.1 Create scan_video_comments task
    - Fetch all comments from YouTube
    - Run ML prediction on each comment
    - Store results in database
    - Update scan status progressively
    - Handle errors with retry logic
    - _Requirements: 3.2, 3.3, 3.4, 3.5, 9.2, 9.4_
  - [x] 17.2 Write property test for scan completion counts
    - **Property 7: Scan Completion Counts Consistency**
    - **Validates: Requirements 3.5**
  - [x] 17.3 Write property test for scan results foreign key
    - **Property 6: Scan Results Foreign Key Integrity**
    - **Validates: Requirements 3.4, 10.2**
  - [x] 17.4 Create batch_predict async task
    - Process batch predictions asynchronously
    - _Requirements: 2.3_
  - [x] 17.5 Create cleanup_old_results periodic task
    - Remove old scan results based on retention policy
    - _Requirements: 9.5_

- [x] 18. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Phase 5: Infrastructure

- [x] 19. Create Docker configuration
  - [x] 19.1 Create backend Dockerfile
    - Use Python 3.12 base image
    - Install dependencies
    - Configure uvicorn startup
    - _Requirements: Docker Compose Services_
  - [x] 19.2 Create docker-compose.yml
    - Configure postgres, redis, backend, celery_worker, celery_beat, flower services
    - Set up volumes and health checks
    - Configure environment variables
    - _Requirements: Docker Compose Services_
  - [x] 19.3 Create .env.example file
    - Document all required environment variables
    - _Requirements: Environment Variables_

- [x] 20. Create Makefile for common commands
  - [x] 20.1 Add development commands
    - make dev, make test, make lint, make migrate
    - _Requirements: Development workflow_

- [ ] 21. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Phase 6: Frontend Integration

- [ ] 22. Set up frontend API client
  - [ ] 22.1 Create API client utilities
    - Create lib/api.ts with axios/fetch configuration
    - Set up authentication header injection
    - Handle token refresh on 401
    - _Requirements: 11.1, 11.2_
  - [ ] 22.2 Create TypeScript types matching backend schemas
    - Define User, Scan, ScanResult, Video, Comment types
    - _Requirements: Type safety_

- [ ] 23. Implement authentication pages
  - [ ] 23.1 Create login page
    - Add Google OAuth login button
    - Handle OAuth callback
    - Store JWT in localStorage/cookies
    - _Requirements: 1.1, 1.2, 1.4_
  - [ ] 23.2 Create auth context/provider
    - Manage authentication state
    - Provide logout functionality
    - _Requirements: 1.6_

- [ ] 24. Implement dashboard page
  - [ ] 24.1 Create dashboard layout with Horizon UI components
    - Display stats cards (total scans, comments, detection rate)
    - Add chart component for scan history
    - _Requirements: 7.1, 7.2_
  - [ ] 24.2 Integrate with dashboard API endpoints
    - Fetch stats and chart data
    - Handle loading and error states
    - _Requirements: 7.1, 7.2_

- [ ] 25. Implement my-videos pages
  - [ ] 25.1 Create my-videos list page
    - Display user's YouTube videos
    - Add pagination
    - _Requirements: 4.1, 4.4_
  - [ ] 25.2 Create my-videos detail page
    - Show video info and comments
    - Add scan button
    - Display scan results with delete options
    - _Requirements: 4.2, 4.3, 6.1, 6.2_

- [ ] 26. Implement browse pages
  - [ ] 26.1 Create browse/search page
    - Add search input
    - Display search results
    - _Requirements: 5.1, 5.2_
  - [ ] 26.2 Create browse video detail page
    - Show video info and comments
    - Add scan button (no delete for public videos)
    - _Requirements: 5.3_

- [ ] 27. Implement scan pages
  - [ ] 27.1 Create scan progress component
    - Poll scan status
    - Show progress indicator
    - _Requirements: 3.7, 9.2_
  - [ ] 27.2 Create scan results page
    - Display gambling vs clean comments
    - Show confidence scores
    - Add export buttons
    - _Requirements: 7.4, 8.1, 8.2_

- [ ] 28. Implement history page
  - [ ] 28.1 Create scan history list
    - Display paginated scan history
    - Show summary for each scan
    - Link to scan details
    - _Requirements: 7.3_

- [ ] 29. Final Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
