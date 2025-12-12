/**
 * Confidence utility functions
 * Requirements: 3.1 - Highlight comments with confidence below 70%
 */

/** Low confidence threshold (70%) */
export const LOW_CONFIDENCE_THRESHOLD = 0.7;

/**
 * Check if a result has low confidence
 * Requirements: 3.1 - Highlight comments with confidence below 70%
 * **Feature: auto-ml-retraining, Property 2: Low Confidence Highlighting**
 */
export function isLowConfidenceResult(confidence: number): boolean {
  return confidence < LOW_CONFIDENCE_THRESHOLD;
}
