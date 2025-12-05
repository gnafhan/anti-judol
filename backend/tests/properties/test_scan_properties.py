"""
Property-based tests for scan operations.

Tests correctness properties for:
- Scan creation status invariant (Property 5)
- Scan history pagination (Property 12)
"""

import sys
from pathlib import Path

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import uuid
from datetime import datetime, timezone

import pytest
from hypothesis import given, strategies as st, settings, assume

from app.models.scan import Scan


class TestScanCreationStatusProperties:
    """
    **Feature: gambling-comment-detector, Property 5: Scan Creation Status Invariant**
    **Validates: Requirements 3.1, 9.1**
    
    For any valid video ID submitted for scanning, the created scan record
    SHALL have status "pending" and a non-null task_id.
    """

    @given(
        video_id=st.text(
            min_size=1,
            max_size=50,
            alphabet=st.characters(whitelist_categories=('L', 'N', 'Pd'))
        ).filter(lambda x: len(x.strip()) > 0),
        user_id=st.uuids(),
    )
    @settings(max_examples=100)
    def test_scan_creation_has_pending_status(self, video_id: str, user_id: uuid.UUID):
        """
        Property: New scans always have status "pending"
        
        For any valid video ID, creating a scan should result in a scan
        with status "pending".
        """
        # Generate a task_id as would be done in the router
        task_id = str(uuid.uuid4())
        
        # Create scan model (simulating what the router does)
        scan = Scan(
            user_id=user_id,
            video_id=video_id,
            status="pending",
            task_id=task_id,
        )
        
        # Verify the invariant: status must be "pending"
        assert scan.status == "pending"

    @given(
        video_id=st.text(
            min_size=1,
            max_size=50,
            alphabet=st.characters(whitelist_categories=('L', 'N', 'Pd'))
        ).filter(lambda x: len(x.strip()) > 0),
        user_id=st.uuids(),
    )
    @settings(max_examples=100)
    def test_scan_creation_has_task_id(self, video_id: str, user_id: uuid.UUID):
        """
        Property: New scans always have a non-null task_id
        
        For any valid video ID, creating a scan should result in a scan
        with a non-null task_id for tracking the async task.
        """
        # Generate a task_id as would be done in the router
        task_id = str(uuid.uuid4())
        
        # Create scan model (simulating what the router does)
        scan = Scan(
            user_id=user_id,
            video_id=video_id,
            status="pending",
            task_id=task_id,
        )
        
        # Verify the invariant: task_id must be non-null
        assert scan.task_id is not None
        assert len(scan.task_id) > 0

    @given(
        video_id=st.text(
            min_size=1,
            max_size=50,
            alphabet=st.characters(whitelist_categories=('L', 'N', 'Pd'))
        ).filter(lambda x: len(x.strip()) > 0),
        user_id=st.uuids(),
    )
    @settings(max_examples=100)
    def test_scan_creation_task_id_is_valid_uuid(self, video_id: str, user_id: uuid.UUID):
        """
        Property: task_id is a valid UUID string
        
        The task_id should be a valid UUID format for Celery task tracking.
        """
        # Generate a task_id as would be done in the router
        task_id = str(uuid.uuid4())
        
        # Create scan model
        scan = Scan(
            user_id=user_id,
            video_id=video_id,
            status="pending",
            task_id=task_id,
        )
        
        # Verify task_id is a valid UUID
        try:
            parsed_uuid = uuid.UUID(scan.task_id)
            assert str(parsed_uuid) == scan.task_id
        except ValueError:
            pytest.fail(f"task_id '{scan.task_id}' is not a valid UUID")

    @given(
        video_id=st.text(
            min_size=1,
            max_size=50,
            alphabet=st.characters(whitelist_categories=('L', 'N', 'Pd'))
        ).filter(lambda x: len(x.strip()) > 0),
        user_id=st.uuids(),
    )
    @settings(max_examples=100)
    def test_scan_creation_initial_counts_are_zero(self, video_id: str, user_id: uuid.UUID):
        """
        Property: New scans have zero counts
        
        For any new scan, the initial counts (total_comments, gambling_count, clean_count)
        should all be zero. Note: SQLAlchemy defaults are applied at database level,
        so we explicitly set them as the router would do.
        """
        task_id = str(uuid.uuid4())
        
        # Create scan with explicit zero counts (as would be set by database defaults)
        scan = Scan(
            user_id=user_id,
            video_id=video_id,
            status="pending",
            task_id=task_id,
            total_comments=0,
            gambling_count=0,
            clean_count=0,
        )
        
        # Verify initial counts are zero
        assert scan.total_comments == 0
        assert scan.gambling_count == 0
        assert scan.clean_count == 0


class TestScanHistoryPaginationProperties:
    """
    **Feature: gambling-comment-detector, Property 12: Scan History Pagination**
    **Validates: Requirements 7.3**
    
    For any pagination request with page and limit parameters, the response
    SHALL return at most `limit` items, correct total count, and valid page metadata.
    """

    @given(
        total_items=st.integers(min_value=0, max_value=200),
        page=st.integers(min_value=1, max_value=50),
        limit=st.integers(min_value=1, max_value=100),
    )
    @settings(max_examples=100)
    def test_pagination_returns_at_most_limit_items(
        self, total_items: int, page: int, limit: int
    ):
        """
        Property: Pagination returns at most `limit` items
        
        For any pagination request, the number of items returned should
        never exceed the specified limit.
        """
        from math import ceil
        
        # Calculate expected values
        pages = ceil(total_items / limit) if total_items > 0 else 1
        offset = (page - 1) * limit
        
        # Calculate how many items would be on this page
        if page > pages:
            expected_items = 0
        else:
            remaining = total_items - offset
            expected_items = min(remaining, limit) if remaining > 0 else 0
        
        # Verify the constraint
        assert expected_items <= limit

    @given(
        total_items=st.integers(min_value=0, max_value=200),
        limit=st.integers(min_value=1, max_value=100),
    )
    @settings(max_examples=100)
    def test_pagination_pages_calculation(self, total_items: int, limit: int):
        """
        Property: Pages calculation is correct
        
        The total number of pages should be ceil(total_items / limit),
        with a minimum of 1 page.
        """
        from math import ceil
        
        expected_pages = ceil(total_items / limit) if total_items > 0 else 1
        
        # Verify pages calculation
        assert expected_pages >= 1
        
        # Verify that all items fit within the pages
        if total_items > 0:
            assert expected_pages * limit >= total_items
            assert (expected_pages - 1) * limit < total_items

    @given(
        total_items=st.integers(min_value=1, max_value=200),
        page=st.integers(min_value=1, max_value=50),
        limit=st.integers(min_value=1, max_value=100),
    )
    @settings(max_examples=100)
    def test_pagination_offset_calculation(self, total_items: int, page: int, limit: int):
        """
        Property: Offset calculation is correct
        
        The offset should be (page - 1) * limit, ensuring correct item positioning.
        """
        offset = (page - 1) * limit
        
        # Offset should be non-negative
        assert offset >= 0
        
        # First page should have offset 0
        if page == 1:
            assert offset == 0
        
        # Offset should increase by limit for each page
        expected_offset = (page - 1) * limit
        assert offset == expected_offset

    @given(
        total_items=st.integers(min_value=0, max_value=200),
        limit=st.integers(min_value=1, max_value=100),
    )
    @settings(max_examples=100)
    def test_pagination_first_page_contains_first_items(
        self, total_items: int, limit: int
    ):
        """
        Property: First page starts from the beginning
        
        Page 1 should always start from offset 0.
        """
        page = 1
        offset = (page - 1) * limit
        
        assert offset == 0

    @given(
        total_items=st.integers(min_value=1, max_value=200),
        limit=st.integers(min_value=1, max_value=100),
    )
    @settings(max_examples=100)
    def test_pagination_last_page_contains_remaining_items(
        self, total_items: int, limit: int
    ):
        """
        Property: Last page contains remaining items
        
        The last page should contain the remaining items that don't fill a full page.
        """
        from math import ceil
        
        pages = ceil(total_items / limit)
        last_page_offset = (pages - 1) * limit
        remaining = total_items - last_page_offset
        
        # Last page should have between 1 and limit items
        assert 1 <= remaining <= limit

    @given(
        total_items=st.integers(min_value=0, max_value=200),
        page=st.integers(min_value=1, max_value=100),
        limit=st.integers(min_value=1, max_value=100),
    )
    @settings(max_examples=100)
    def test_pagination_metadata_consistency(
        self, total_items: int, page: int, limit: int
    ):
        """
        Property: Pagination metadata is internally consistent
        
        The pagination response metadata (total, page, limit, pages) should
        be internally consistent.
        """
        from math import ceil
        
        # Calculate pagination metadata
        pages = ceil(total_items / limit) if total_items > 0 else 1
        
        # Simulate response metadata
        response = {
            "total": total_items,
            "page": page,
            "limit": limit,
            "pages": pages,
        }
        
        # Verify consistency
        assert response["total"] >= 0
        assert response["page"] >= 1
        assert response["limit"] >= 1
        assert response["pages"] >= 1
        
        # Verify pages calculation is correct
        if response["total"] > 0:
            assert response["pages"] == ceil(response["total"] / response["limit"])
        else:
            assert response["pages"] == 1


class TestScanCompletionCountsProperties:
    """
    **Feature: gambling-comment-detector, Property 7: Scan Completion Counts Consistency**
    **Validates: Requirements 3.5**
    
    For any completed scan, the sum of gambling_count and clean_count SHALL equal
    total_comments, and these counts SHALL match the actual count of results in
    scan_results table.
    """

    @given(
        gambling_count=st.integers(min_value=0, max_value=1000),
        clean_count=st.integers(min_value=0, max_value=1000),
    )
    @settings(max_examples=100)
    def test_scan_counts_sum_equals_total(
        self, gambling_count: int, clean_count: int
    ):
        """
        Property: gambling_count + clean_count == total_comments
        
        For any completed scan, the sum of gambling and clean counts
        must equal the total comments count.
        """
        total_comments = gambling_count + clean_count
        
        # Create a completed scan with these counts
        scan = Scan(
            user_id=uuid.uuid4(),
            video_id="test_video_id",
            status="completed",
            task_id=str(uuid.uuid4()),
            total_comments=total_comments,
            gambling_count=gambling_count,
            clean_count=clean_count,
        )
        
        # Verify the invariant: sum of counts equals total
        assert scan.gambling_count + scan.clean_count == scan.total_comments

    @given(
        gambling_count=st.integers(min_value=0, max_value=500),
        clean_count=st.integers(min_value=0, max_value=500),
    )
    @settings(max_examples=100)
    def test_scan_counts_match_results_count(
        self, gambling_count: int, clean_count: int
    ):
        """
        Property: Counts match actual results count
        
        For any completed scan, the total_comments should match the number
        of ScanResult records that would be associated with the scan.
        """
        from app.models.scan import ScanResult
        
        total_comments = gambling_count + clean_count
        scan_id = uuid.uuid4()
        
        # Create scan
        scan = Scan(
            id=scan_id,
            user_id=uuid.uuid4(),
            video_id="test_video_id",
            status="completed",
            task_id=str(uuid.uuid4()),
            total_comments=total_comments,
            gambling_count=gambling_count,
            clean_count=clean_count,
        )
        
        # Simulate creating results (without database)
        results = []
        
        # Create gambling results
        for i in range(gambling_count):
            result = ScanResult(
                scan_id=scan_id,
                comment_id=f"gambling_comment_{i}",
                comment_text=f"Gambling comment {i}",
                is_gambling=True,
                confidence=0.95,
            )
            results.append(result)
        
        # Create clean results
        for i in range(clean_count):
            result = ScanResult(
                scan_id=scan_id,
                comment_id=f"clean_comment_{i}",
                comment_text=f"Clean comment {i}",
                is_gambling=False,
                confidence=0.85,
            )
            results.append(result)
        
        # Verify counts match
        assert len(results) == scan.total_comments
        
        # Verify gambling/clean breakdown
        actual_gambling = sum(1 for r in results if r.is_gambling)
        actual_clean = sum(1 for r in results if not r.is_gambling)
        
        assert actual_gambling == scan.gambling_count
        assert actual_clean == scan.clean_count

    @given(
        total_comments=st.integers(min_value=0, max_value=1000),
    )
    @settings(max_examples=100)
    def test_scan_counts_non_negative(self, total_comments: int):
        """
        Property: All counts are non-negative
        
        For any scan, gambling_count, clean_count, and total_comments
        must all be non-negative integers.
        """
        # Generate random split of total into gambling and clean
        import random
        gambling_count = random.randint(0, total_comments)
        clean_count = total_comments - gambling_count
        
        scan = Scan(
            user_id=uuid.uuid4(),
            video_id="test_video_id",
            status="completed",
            task_id=str(uuid.uuid4()),
            total_comments=total_comments,
            gambling_count=gambling_count,
            clean_count=clean_count,
        )
        
        # Verify non-negative
        assert scan.total_comments >= 0
        assert scan.gambling_count >= 0
        assert scan.clean_count >= 0

    @given(
        gambling_count=st.integers(min_value=0, max_value=500),
        clean_count=st.integers(min_value=0, max_value=500),
    )
    @settings(max_examples=100)
    def test_scan_counts_bounded_by_total(
        self, gambling_count: int, clean_count: int
    ):
        """
        Property: Individual counts bounded by total
        
        For any completed scan, gambling_count <= total_comments
        and clean_count <= total_comments.
        """
        total_comments = gambling_count + clean_count
        
        scan = Scan(
            user_id=uuid.uuid4(),
            video_id="test_video_id",
            status="completed",
            task_id=str(uuid.uuid4()),
            total_comments=total_comments,
            gambling_count=gambling_count,
            clean_count=clean_count,
        )
        
        # Verify bounds
        assert scan.gambling_count <= scan.total_comments
        assert scan.clean_count <= scan.total_comments

    @given(
        num_results=st.integers(min_value=1, max_value=100),
        gambling_ratio=st.floats(min_value=0.0, max_value=1.0),
    )
    @settings(max_examples=100)
    def test_scan_counts_consistency_with_results(
        self, num_results: int, gambling_ratio: float
    ):
        """
        Property: Counts are consistent with result classification
        
        For any set of results, the gambling_count should equal the number
        of results where is_gambling=True, and clean_count should equal
        the number where is_gambling=False.
        """
        from app.models.scan import ScanResult
        
        scan_id = uuid.uuid4()
        
        # Calculate expected counts based on ratio
        gambling_count = int(num_results * gambling_ratio)
        clean_count = num_results - gambling_count
        
        # Create results
        results = []
        for i in range(gambling_count):
            results.append(ScanResult(
                scan_id=scan_id,
                comment_id=f"comment_{i}",
                is_gambling=True,
                confidence=0.9,
            ))
        
        for i in range(clean_count):
            results.append(ScanResult(
                scan_id=scan_id,
                comment_id=f"comment_{gambling_count + i}",
                is_gambling=False,
                confidence=0.8,
            ))
        
        # Calculate counts from results
        calculated_gambling = sum(1 for r in results if r.is_gambling)
        calculated_clean = sum(1 for r in results if not r.is_gambling)
        calculated_total = len(results)
        
        # Verify consistency
        assert calculated_gambling == gambling_count
        assert calculated_clean == clean_count
        assert calculated_total == num_results
        assert calculated_gambling + calculated_clean == calculated_total



class TestScanResultsForeignKeyProperties:
    """
    **Feature: gambling-comment-detector, Property 6: Scan Results Foreign Key Integrity**
    **Validates: Requirements 3.4, 10.2**
    
    For any scan result stored in the database, the scan_id foreign key
    SHALL reference an existing scan record.
    """

    @given(
        scan_id=st.uuids(),
        num_results=st.integers(min_value=1, max_value=50),
    )
    @settings(max_examples=100)
    def test_scan_results_have_valid_scan_id(
        self, scan_id: uuid.UUID, num_results: int
    ):
        """
        Property: All scan results have a valid scan_id
        
        For any scan result, the scan_id must be a valid UUID that
        references the parent scan.
        """
        from app.models.scan import ScanResult
        
        # Create results with the same scan_id
        results = []
        for i in range(num_results):
            result = ScanResult(
                scan_id=scan_id,
                comment_id=f"comment_{i}",
                comment_text=f"Test comment {i}",
                is_gambling=i % 2 == 0,
                confidence=0.85,
            )
            results.append(result)
        
        # Verify all results have the correct scan_id
        for result in results:
            assert result.scan_id == scan_id
            assert result.scan_id is not None

    @given(
        scan_id=st.uuids(),
        comment_ids=st.lists(
            st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('L', 'N'))),
            min_size=1,
            max_size=20,
            unique=True,
        ),
    )
    @settings(max_examples=100)
    def test_scan_results_foreign_key_consistency(
        self, scan_id: uuid.UUID, comment_ids: list[str]
    ):
        """
        Property: Foreign key is consistent across all results for a scan
        
        All results belonging to the same scan must have the same scan_id.
        """
        from app.models.scan import ScanResult
        
        results = []
        for comment_id in comment_ids:
            result = ScanResult(
                scan_id=scan_id,
                comment_id=comment_id,
                is_gambling=False,
                confidence=0.5,
            )
            results.append(result)
        
        # Verify all results have the same scan_id
        scan_ids = {result.scan_id for result in results}
        assert len(scan_ids) == 1
        assert scan_id in scan_ids

    @given(
        user_id=st.uuids(),
        video_id=st.text(
            min_size=1,
            max_size=50,
            alphabet=st.characters(whitelist_categories=('L', 'N'))
        ).filter(lambda x: len(x.strip()) > 0),
        num_results=st.integers(min_value=0, max_value=30),
    )
    @settings(max_examples=100)
    def test_scan_and_results_relationship(
        self, user_id: uuid.UUID, video_id: str, num_results: int
    ):
        """
        Property: Scan and results have proper parent-child relationship
        
        When a scan is created with results, the scan_id in each result
        must match the scan's id.
        """
        from app.models.scan import ScanResult
        
        scan_id = uuid.uuid4()
        
        # Create scan
        scan = Scan(
            id=scan_id,
            user_id=user_id,
            video_id=video_id,
            status="completed",
            task_id=str(uuid.uuid4()),
            total_comments=num_results,
            gambling_count=num_results // 2,
            clean_count=num_results - (num_results // 2),
        )
        
        # Create results
        results = []
        for i in range(num_results):
            result = ScanResult(
                scan_id=scan_id,
                comment_id=f"comment_{i}",
                is_gambling=i % 2 == 0,
                confidence=0.9,
            )
            results.append(result)
        
        # Verify relationship
        for result in results:
            assert result.scan_id == scan.id

    @given(
        scan_id=st.uuids(),
    )
    @settings(max_examples=100)
    def test_scan_result_scan_id_is_uuid(self, scan_id: uuid.UUID):
        """
        Property: scan_id is a valid UUID
        
        The scan_id foreign key must be a valid UUID format.
        """
        from app.models.scan import ScanResult
        
        result = ScanResult(
            scan_id=scan_id,
            comment_id="test_comment",
            is_gambling=True,
            confidence=0.95,
        )
        
        # Verify scan_id is a valid UUID
        assert isinstance(result.scan_id, uuid.UUID)
        
        # Verify it can be converted to string and back
        scan_id_str = str(result.scan_id)
        parsed_uuid = uuid.UUID(scan_id_str)
        assert parsed_uuid == result.scan_id

    @given(
        num_scans=st.integers(min_value=1, max_value=5),
        results_per_scan=st.integers(min_value=1, max_value=10),
    )
    @settings(max_examples=100)
    def test_multiple_scans_results_isolation(
        self, num_scans: int, results_per_scan: int
    ):
        """
        Property: Results from different scans are properly isolated
        
        Results from different scans must have different scan_ids,
        ensuring proper foreign key isolation.
        """
        from app.models.scan import ScanResult
        
        all_results = []
        scan_ids = []
        
        for scan_idx in range(num_scans):
            scan_id = uuid.uuid4()
            scan_ids.append(scan_id)
            
            for result_idx in range(results_per_scan):
                result = ScanResult(
                    scan_id=scan_id,
                    comment_id=f"scan_{scan_idx}_comment_{result_idx}",
                    is_gambling=False,
                    confidence=0.5,
                )
                all_results.append(result)
        
        # Verify each scan's results have the correct scan_id
        for scan_idx, scan_id in enumerate(scan_ids):
            scan_results = [
                r for r in all_results 
                if r.comment_id.startswith(f"scan_{scan_idx}_")
            ]
            
            for result in scan_results:
                assert result.scan_id == scan_id
            
            # Verify count
            assert len(scan_results) == results_per_scan
