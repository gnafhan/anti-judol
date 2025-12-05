"""
Property-based tests for the Export Service.

Tests correctness properties for CSV and JSON export functionality.
"""

import uuid
from datetime import datetime, timezone

import pytest
from hypothesis import given, strategies as st, settings

from app.services.export_service import ExportService


# Strategy for safe text without newlines (for CSV metadata fields)
safe_metadata_text_strategy = st.text(
    min_size=1, 
    max_size=100,
    alphabet=st.characters(
        whitelist_categories=('L', 'N', 'P', 'S', 'Z'),
        blacklist_characters='\r\n'  # Avoid newlines in CSV metadata
    )
)

# Strategies for generating test data
scan_metadata_strategy = st.fixed_dictionaries({
    "id": st.uuids(),
    "video_id": st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Nd', 'Lu', 'Ll'))),
    "video_title": st.one_of(st.none(), safe_metadata_text_strategy),
    "channel_name": st.one_of(st.none(), safe_metadata_text_strategy),
    "total_comments": st.integers(min_value=0, max_value=10000),
    "gambling_count": st.integers(min_value=0, max_value=10000),
    "clean_count": st.integers(min_value=0, max_value=10000),
    "status": st.sampled_from(["pending", "processing", "completed", "failed"]),
    "scanned_at": st.one_of(st.none(), st.datetimes(timezones=st.just(timezone.utc))),
    "created_at": st.datetimes(timezones=st.just(timezone.utc)),
})

# Strategy for scan results - avoid problematic characters for CSV
safe_text_strategy = st.text(
    min_size=0, 
    max_size=200,
    alphabet=st.characters(
        whitelist_categories=('L', 'N', 'P', 'S', 'Z'),
        blacklist_characters='\r\n'  # Avoid newlines in CSV fields
    )
)

scan_result_strategy = st.fixed_dictionaries({
    "comment_id": st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Nd', 'Lu', 'Ll'))),
    "comment_text": st.one_of(st.none(), safe_text_strategy),
    "author_name": st.one_of(st.none(), st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('L', 'N')))),
    "is_gambling": st.booleans(),
    "confidence": st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
})


class MockScan:
    """Mock Scan object for testing export service."""
    
    def __init__(self, metadata: dict):
        self.id = metadata["id"]
        self.video_id = metadata["video_id"]
        self.video_title = metadata["video_title"]
        self.channel_name = metadata["channel_name"]
        self.total_comments = metadata["total_comments"]
        self.gambling_count = metadata["gambling_count"]
        self.clean_count = metadata["clean_count"]
        self.status = metadata["status"]
        self.scanned_at = metadata["scanned_at"]
        self.created_at = metadata["created_at"]


class MockScanResult:
    """Mock ScanResult object for testing export service."""
    
    def __init__(self, data: dict):
        self.comment_id = data["comment_id"]
        self.comment_text = data["comment_text"]
        self.author_name = data["author_name"]
        self.is_gambling = data["is_gambling"]
        self.confidence = data["confidence"]


class TestExportCompletenessAndRoundTrip:
    """
    **Feature: gambling-comment-detector, Property 13: Export Completeness and Round-Trip**
    **Validates: Requirements 8.1, 8.2, 8.3, 8.4**
    
    For any scan with results:
    - CSV export SHALL contain all scan_results with columns (comment_id, text, author, is_gambling, confidence) plus metadata
    - JSON export SHALL be parseable back to equivalent data structures
    """
    
    @given(
        metadata=scan_metadata_strategy,
        results_data=st.lists(scan_result_strategy, min_size=0, max_size=20)
    )
    @settings(max_examples=100)
    def test_csv_export_contains_all_results(self, metadata: dict, results_data: list[dict]):
        """CSV export contains all scan results with required columns."""
        service = ExportService()
        scan = MockScan(metadata)
        results = [MockScanResult(r) for r in results_data]
        
        # Export to CSV
        csv_content = service.export_csv(scan, results)
        
        # Verify CSV is not empty
        assert csv_content, "CSV export should not be empty"
        
        # Verify metadata is included in header
        assert f"# scan_id: {scan.id}" in csv_content, "CSV should contain scan_id in metadata"
        assert f"# video_id: {scan.video_id}" in csv_content, "CSV should contain video_id in metadata"
        
        # Verify column headers are present
        assert "comment_id,text,author,is_gambling,confidence" in csv_content, \
            "CSV should contain required column headers"
        
        # Verify all results are present (count data rows)
        lines = csv_content.strip().split("\n")
        data_lines = [l for l in lines if not l.startswith("#") and l.strip()]
        # Subtract 1 for header row
        data_row_count = len(data_lines) - 1 if data_lines else 0
        assert data_row_count == len(results), \
            f"CSV should contain {len(results)} data rows, got {data_row_count}"
    
    @given(
        metadata=scan_metadata_strategy,
        results_data=st.lists(scan_result_strategy, min_size=0, max_size=20)
    )
    @settings(max_examples=100)
    def test_json_export_contains_all_results(self, metadata: dict, results_data: list[dict]):
        """JSON export contains all scan results with metadata."""
        service = ExportService()
        scan = MockScan(metadata)
        results = [MockScanResult(r) for r in results_data]
        
        # Export to JSON
        json_content = service.export_json(scan, results)
        
        # Verify JSON is valid and parseable
        parsed_metadata, parsed_results = service.parse_json(json_content)
        
        # Verify metadata fields
        assert parsed_metadata["scan_id"] == str(scan.id), "JSON should contain correct scan_id"
        assert parsed_metadata["video_id"] == scan.video_id, "JSON should contain correct video_id"
        assert parsed_metadata["total_comments"] == scan.total_comments, "JSON should contain correct total_comments"
        assert parsed_metadata["gambling_count"] == scan.gambling_count, "JSON should contain correct gambling_count"
        assert parsed_metadata["clean_count"] == scan.clean_count, "JSON should contain correct clean_count"
        
        # Verify all results are present
        assert len(parsed_results) == len(results), \
            f"JSON should contain {len(results)} results, got {len(parsed_results)}"
    
    @given(
        metadata=scan_metadata_strategy,
        results_data=st.lists(scan_result_strategy, min_size=0, max_size=20)
    )
    @settings(max_examples=100)
    def test_json_export_roundtrip(self, metadata: dict, results_data: list[dict]):
        """JSON export can be parsed back to equivalent data structures."""
        service = ExportService()
        scan = MockScan(metadata)
        results = [MockScanResult(r) for r in results_data]
        
        # Export to JSON
        json_content = service.export_json(scan, results)
        
        # Parse back
        parsed_metadata, parsed_results = service.parse_json(json_content)
        
        # Verify round-trip consistency for results
        for i, (original, parsed) in enumerate(zip(results_data, parsed_results)):
            assert parsed["comment_id"] == original["comment_id"], \
                f"Result {i}: comment_id should match after round-trip"
            assert parsed["text"] == original["comment_text"], \
                f"Result {i}: text should match after round-trip"
            assert parsed["author"] == original["author_name"], \
                f"Result {i}: author should match after round-trip"
            assert parsed["is_gambling"] == original["is_gambling"], \
                f"Result {i}: is_gambling should match after round-trip"
            assert abs(parsed["confidence"] - original["confidence"]) < 1e-10, \
                f"Result {i}: confidence should match after round-trip"
    
    @given(
        metadata=scan_metadata_strategy,
        results_data=st.lists(scan_result_strategy, min_size=0, max_size=20)
    )
    @settings(max_examples=100)
    def test_csv_export_roundtrip(self, metadata: dict, results_data: list[dict]):
        """CSV export can be parsed back to equivalent data structures."""
        service = ExportService()
        scan = MockScan(metadata)
        results = [MockScanResult(r) for r in results_data]
        
        # Export to CSV
        csv_content = service.export_csv(scan, results)
        
        # Parse back
        parsed_metadata, parsed_results = service.parse_csv(csv_content)
        
        # Verify round-trip consistency for metadata
        assert parsed_metadata["scan_id"] == str(scan.id), "scan_id should match after round-trip"
        assert parsed_metadata["video_id"] == scan.video_id, "video_id should match after round-trip"
        
        # Verify round-trip consistency for results
        assert len(parsed_results) == len(results_data), \
            f"Should have {len(results_data)} results after round-trip, got {len(parsed_results)}"
        
        for i, (original, parsed) in enumerate(zip(results_data, parsed_results)):
            assert parsed["comment_id"] == original["comment_id"], \
                f"Result {i}: comment_id should match after round-trip"
            # Handle empty string vs None for text
            expected_text = original["comment_text"] if original["comment_text"] else None
            parsed_text = parsed["text"] if parsed["text"] else None
            assert parsed_text == expected_text or (parsed_text == "" and expected_text is None) or (parsed_text is None and expected_text == ""), \
                f"Result {i}: text should match after round-trip (expected: {expected_text}, got: {parsed_text})"
            # Handle empty string vs None for author
            expected_author = original["author_name"] if original["author_name"] else None
            parsed_author = parsed["author"] if parsed["author"] else None
            assert parsed_author == expected_author or (parsed_author == "" and expected_author is None) or (parsed_author is None and expected_author == ""), \
                f"Result {i}: author should match after round-trip"
            assert parsed["is_gambling"] == original["is_gambling"], \
                f"Result {i}: is_gambling should match after round-trip"
            assert abs(parsed["confidence"] - original["confidence"]) < 1e-10, \
                f"Result {i}: confidence should match after round-trip"
    
    def test_empty_results_export(self):
        """Export with no results produces valid output."""
        service = ExportService()
        scan = MockScan({
            "id": uuid.uuid4(),
            "video_id": "test123",
            "video_title": "Test Video",
            "channel_name": "Test Channel",
            "total_comments": 0,
            "gambling_count": 0,
            "clean_count": 0,
            "status": "completed",
            "scanned_at": datetime.now(timezone.utc),
            "created_at": datetime.now(timezone.utc),
        })
        results = []
        
        # CSV export
        csv_content = service.export_csv(scan, results)
        assert csv_content, "CSV export should not be empty even with no results"
        assert "comment_id,text,author,is_gambling,confidence" in csv_content
        
        # JSON export
        json_content = service.export_json(scan, results)
        parsed_metadata, parsed_results = service.parse_json(json_content)
        assert parsed_results == [], "JSON should have empty results list"
        assert parsed_metadata["video_id"] == "test123"
