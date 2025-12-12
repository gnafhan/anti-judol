# Requirements Document

## Introduction

Fitur Auto ML Retraining memungkinkan sistem untuk secara otomatis melatih ulang model machine learning berdasarkan feedback validasi dari pengguna. Pengguna dapat memvalidasi hasil prediksi komentar (gambling/clean) melalui UI yang intuitif, dan sistem akan mengumpulkan data validasi tersebut untuk meningkatkan akurasi model secara berkelanjutan. Fokus utama adalah memberikan pengalaman pengguna (UX) yang seamless dan tidak mengganggu workflow utama.

## Glossary

- **Auto ML System**: Sistem yang mengelola proses retraining model secara otomatis berdasarkan threshold validasi
- **Validation Feedback**: Koreksi dari pengguna terhadap hasil prediksi model (benar/salah)
- **Retraining Threshold**: Jumlah minimum data validasi yang diperlukan sebelum model di-retrain
- **Confidence Score**: Tingkat keyakinan model terhadap prediksi (0-100%)
- **Training Dataset**: Kumpulan data komentar dengan label yang digunakan untuk melatih model
- **Model Pipeline**: Pipeline ML yang mencakup hybrid_all_features vectorizer dan Logistic Regression classifier
- **Hybrid All Features**: Kombinasi word-level TF-IDF dan character-level TF-IDF untuk feature extraction
- **Inline Validation**: Validasi yang dilakukan langsung pada item tanpa navigasi ke halaman lain
- **Batch Validation**: Validasi multiple items sekaligus dalam satu aksi
- **Quick Action**: Aksi cepat yang dapat dilakukan dengan minimal klik

## Requirements

### Requirement 1

**User Story:** As a user, I want to validate prediction results inline without leaving the scan results page, so that I can quickly provide feedback while reviewing comments.

#### Acceptance Criteria

1. WHEN a user views a scan result comment THEN the system SHALL display a subtle validation toggle/checkbox next to each comment prediction
2. WHEN a user clicks the validation toggle on a correctly predicted comment THEN the system SHALL mark the prediction as "confirmed correct" with visual feedback
3. WHEN a user clicks the validation toggle on an incorrectly predicted comment THEN the system SHALL display a quick correction option (gambling ↔ clean)
4. WHEN a validation is submitted THEN the system SHALL show a brief toast notification confirming the action without blocking the UI
5. WHILE a user is scrolling through comments THEN the system SHALL keep validation controls accessible but non-intrusive

### Requirement 2

**User Story:** As a user, I want to perform batch validation on multiple comments at once, so that I can efficiently validate large numbers of predictions.

#### Acceptance Criteria

1. WHEN a user enables batch mode THEN the system SHALL display checkboxes for selecting multiple comments
2. WHEN a user selects multiple comments and clicks "Validate Selected" THEN the system SHALL display a modal with bulk action options (confirm all correct, mark all as gambling, mark all as clean)
3. WHEN a user completes batch validation THEN the system SHALL update all selected items and show a summary of changes made
4. WHEN batch validation is in progress THEN the system SHALL display a progress indicator showing completion status

### Requirement 3

**User Story:** As a user, I want to see which comments have low confidence scores, so that I can prioritize validating uncertain predictions.

#### Acceptance Criteria

1. WHEN displaying scan results THEN the system SHALL visually highlight comments with confidence scores below 70% using a distinct indicator
2. WHEN a user applies the "Low Confidence" filter THEN the system SHALL display only comments with confidence below the threshold
3. WHEN a user hovers over a confidence indicator THEN the system SHALL display a tooltip explaining the confidence level and suggesting validation

### Requirement 4

**User Story:** As a user, I want to see my validation progress and contribution to model improvement, so that I feel motivated to continue validating.

#### Acceptance Criteria

1. WHEN a user views the scan results page THEN the system SHALL display a validation progress bar showing validated vs unvalidated comments
2. WHEN a user completes validations THEN the system SHALL show cumulative statistics (total validated, corrections made)
3. WHEN the validation count approaches the retraining threshold THEN the system SHALL display a motivational message indicating progress toward model improvement

### Requirement 5

**User Story:** As a system administrator, I want the model to automatically retrain when sufficient validated data is collected, so that the model continuously improves without manual intervention.

#### Acceptance Criteria

1. WHEN the number of new validated samples reaches the configured threshold (default: 100) THEN the system SHALL trigger an automatic model retraining job
2. WHEN a retraining job starts THEN the system SHALL log the event and continue serving predictions using the current model
3. WHEN a retraining job completes successfully THEN the system SHALL swap to the new model and archive the previous version
4. IF a retraining job fails THEN the system SHALL continue using the current model and notify administrators via logs

### Requirement 6

**User Story:** As a system administrator, I want to configure retraining parameters, so that I can control when and how the model is retrained.

#### Acceptance Criteria

1. WHEN configuring the system THEN the administrator SHALL be able to set the minimum validation threshold for retraining via environment variables
2. WHEN configuring the system THEN the administrator SHALL be able to set ML hyperparameters for Logistic Regression classifier (C: 10, solver: lbfgs) and hybrid_all_features vectorizer (char_tfidf ngram_range: (2,4), word_tfidf ngram_range: (1,2))
3. WHEN a new model is trained THEN the system SHALL use the combined dataset of original training data and validated user feedback

### Requirement 7

**User Story:** As a user, I want to undo my validation within a short time window, so that I can correct mistakes without hassle.

#### Acceptance Criteria

1. WHEN a user submits a validation THEN the system SHALL display an "Undo" option in the toast notification for 5 seconds
2. WHEN a user clicks "Undo" within the time window THEN the system SHALL revert the validation and restore the previous state
3. WHEN the undo window expires THEN the system SHALL persist the validation to the database

### Requirement 8

**User Story:** As a user, I want keyboard shortcuts for quick validation, so that I can validate comments efficiently without using the mouse.

#### Acceptance Criteria

1. WHEN a comment is focused/selected THEN the system SHALL accept keyboard shortcuts (V for validate correct, X for mark incorrect, Enter to confirm)
2. WHEN a user presses arrow keys THEN the system SHALL navigate between comments in the list
3. WHEN keyboard shortcuts are available THEN the system SHALL display a help tooltip showing available shortcuts

### Requirement 9

**User Story:** As a system, I want to store validated data persistently, so that it can be used for model retraining.

#### Acceptance Criteria

1. WHEN a validation is confirmed THEN the system SHALL store the comment text, corrected label, original prediction, confidence score, and timestamp
2. WHEN storing validated data THEN the system SHALL associate it with the user who provided the validation
3. WHEN retrieving training data THEN the system SHALL combine original dataset (df_all.csv) with validated feedback data

### Requirement 10

**User Story:** As a user, I want to see the model's improvement over time, so that I understand the impact of my validations.

#### Acceptance Criteria

1. WHEN viewing the dashboard THEN the system SHALL display model accuracy metrics before and after retraining
2. WHEN a new model is deployed THEN the system SHALL show a notification indicating model improvement percentage
3. WHEN viewing validation history THEN the system SHALL display how many of the user's validations contributed to model improvements
