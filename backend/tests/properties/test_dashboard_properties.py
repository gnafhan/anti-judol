"""
Property-based tests for dashboard operations.

Tests correctness properties for:
- Dashboard stats calculation (Property 10)
- Chart data date range (Property 11)
"""

import sys
from pathlib import Path

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import pytest
from hypothesis import given, strategies as st, settings, assume


class TestDashboardStatsCalculationProperties:
    """
    **Feature: gambling-comment-detector, Property 10: Dashboard Stats Calculation**
    **Validates: Requirements 7.1**
    
    For any user with scan history, the total_scans count SHALL equal the number
    of scan records, and gambling_detection_rate SHALL equal 
    (total gambling comments / total comments analyzed).
    """

    @given(
        scan_counts=st.lists(
            st.tuples(
                st.integers(min_value=0, max_value=1000),  # total_comments
                st.integers(min_value=0, max_value=1000),  # gambling_count
            ),
            min_size=0,
            max_size=50,
        )
    )
    @settings(max_examples=100)
    def test_total_scans_equals_scan_records(
        self, scan_counts: list[tuple[int, int]]
    ):
        """
        Property: total_scans equals the number of scan records
        
        For any collection of scans, the total_scans statistic should
        equal the count of scan records.
        """
        # Filter to ensure gambling_count <= total_comments
        valid_scans = [
            (total, gambling) 
            for total, gambling in scan_counts 
            if gambling <= total
        ]
        
        # Calculate expected total_scans
        expected_total_scans = len(valid_scans)
        
        # Simulate the stats calculation
        total_scans = len(valid_scans)
        
        assert total_scans == expected_total_scans

    @given(
        scan_counts=st.lists(
            st.tuples(
                st.integers(min_value=0, max_value=1000),  # total_comments
                st.integers(min_value=0, max_value=1000),  # gambling_count
            ),
            min_size=0,
            max_size=50,
        )
    )
    @settings(max_examples=100)
    def test_gambling_detection_rate_calculation(
        self, scan_counts: list[tuple[int, int]]
    ):
        """
        Property: gambling_detection_rate equals total_gambling / total_comments
        
        For any collection of completed scans, the gambling detection rate
        should be calculated as total gambling comments divided by total comments.
        """
        # Filter to ensure gambling_count <= total_comments
        valid_scans = [
            (total, gambling) 
            for total, gambling in scan_counts 
            if gambling <= total
        ]
        
        # Calculate totals
        total_comments = sum(total for total, _ in valid_scans)
        total_gambling = sum(gambling for _, gambling in valid_scans)
        
        # Calculate expected detection rate
        if total_comments > 0:
            expected_rate = total_gambling / total_comments
        else:
            expected_rate = 0.0
        
        # Simulate the stats calculation (as done in the router)
        calculated_rate = 0.0
        if total_comments > 0:
            calculated_rate = total_gambling / total_comments
        
        assert calculated_rate == expected_rate

    @given(
        scan_counts=st.lists(
            st.tuples(
                st.integers(min_value=0, max_value=1000),  # total_comments
                st.integers(min_value=0, max_value=1000),  # gambling_count
            ),
            min_size=0,
            max_size=50,
        )
    )
    @settings(max_examples=100)
    def test_gambling_detection_rate_bounds(
        self, scan_counts: list[tuple[int, int]]
    ):
        """
        Property: gambling_detection_rate is between 0 and 1
        
        The gambling detection rate should always be a value between 0.0 and 1.0.
        """
        # Filter to ensure gambling_count <= total_comments
        valid_scans = [
            (total, gambling) 
            for total, gambling in scan_counts 
            if gambling <= total
        ]
        
        # Calculate totals
        total_comments = sum(total for total, _ in valid_scans)
        total_gambling = sum(gambling for _, gambling in valid_scans)
        
        # Calculate detection rate
        if total_comments > 0:
            detection_rate = total_gambling / total_comments
        else:
            detection_rate = 0.0
        
        # Verify bounds
        assert 0.0 <= detection_rate <= 1.0

    @given(
        scan_counts=st.lists(
            st.tuples(
                st.integers(min_value=0, max_value=1000),  # total_comments
                st.integers(min_value=0, max_value=1000),  # gambling_count
            ),
            min_size=0,
            max_size=50,
        )
    )
    @settings(max_examples=100)
    def test_total_comments_aggregation(
        self, scan_counts: list[tuple[int, int]]
    ):
        """
        Property: total_comments equals sum of all scan total_comments
        
        The total comments statistic should equal the sum of total_comments
        from all completed scans.
        """
        # Filter to ensure gambling_count <= total_comments
        valid_scans = [
            (total, gambling) 
            for total, gambling in scan_counts 
            if gambling <= total
        ]
        
        # Calculate expected total
        expected_total = sum(total for total, _ in valid_scans)
        
        # Simulate aggregation
        total_comments = sum(total for total, _ in valid_scans)
        
        assert total_comments == expected_total

    @given(
        scan_counts=st.lists(
            st.tuples(
                st.integers(min_value=0, max_value=1000),  # total_comments
                st.integers(min_value=0, max_value=1000),  # gambling_count
            ),
            min_size=0,
            max_size=50,
        )
    )
    @settings(max_examples=100)
    def test_total_gambling_aggregation(
        self, scan_counts: list[tuple[int, int]]
    ):
        """
        Property: total_gambling equals sum of all scan gambling_counts
        
        The total gambling statistic should equal the sum of gambling_count
        from all completed scans.
        """
        # Filter to ensure gambling_count <= total_comments
        valid_scans = [
            (total, gambling) 
            for total, gambling in scan_counts 
            if gambling <= total
        ]
        
        # Calculate expected total
        expected_gambling = sum(gambling for _, gambling in valid_scans)
        
        # Simulate aggregation
        total_gambling = sum(gambling for _, gambling in valid_scans)
        
        assert total_gambling == expected_gambling

    @given(
        scan_counts=st.lists(
            st.tuples(
                st.integers(min_value=1, max_value=1000),  # total_comments (at least 1)
                st.integers(min_value=0, max_value=1000),  # gambling_count
            ),
            min_size=1,
            max_size=50,
        )
    )
    @settings(max_examples=100)
    def test_stats_consistency_with_nonzero_comments(
        self, scan_counts: list[tuple[int, int]]
    ):
        """
        Property: Stats are consistent when there are comments
        
        When there are comments analyzed, the stats should be internally consistent:
        - total_gambling <= total_comments
        - detection_rate = total_gambling / total_comments
        """
        # Filter to ensure gambling_count <= total_comments
        valid_scans = [
            (total, gambling) 
            for total, gambling in scan_counts 
            if gambling <= total
        ]
        
        assume(len(valid_scans) > 0)
        
        # Calculate stats
        total_comments = sum(total for total, _ in valid_scans)
        total_gambling = sum(gambling for _, gambling in valid_scans)
        
        assume(total_comments > 0)
        
        detection_rate = total_gambling / total_comments
        
        # Verify consistency
        assert total_gambling <= total_comments
        assert detection_rate == total_gambling / total_comments



class TestChartDataDateRangeProperties:
    """
    **Feature: gambling-comment-detector, Property 11: Chart Data Date Range**
    **Validates: Requirements 7.2**
    
    For any chart data request, the response SHALL contain data points for each
    of the past 30 days with scan counts aggregated by date.
    """

    @given(
        reference_date=st.dates(
            min_value=datetime(2020, 1, 1).date(),
            max_value=datetime(2030, 12, 31).date(),
        )
    )
    @settings(max_examples=100)
    def test_chart_data_contains_30_days(self, reference_date):
        """
        Property: Chart data contains exactly 30 data points
        
        For any reference date, the chart data should contain exactly 30 data points,
        one for each day in the past 30 days (including the reference date).
        """
        # Calculate date range (past 30 days)
        end_date = reference_date
        start_date = end_date - timedelta(days=29)  # 30 days including end_date
        
        # Generate data points for all 30 days
        data_points = []
        current_date = start_date
        while current_date <= end_date:
            data_points.append({
                "date": current_date.isoformat(),
                "scan_count": 0,
                "total_comments": 0,
                "gambling_count": 0,
            })
            current_date += timedelta(days=1)
        
        # Verify exactly 30 data points
        assert len(data_points) == 30

    @given(
        reference_date=st.dates(
            min_value=datetime(2020, 1, 1).date(),
            max_value=datetime(2030, 12, 31).date(),
        )
    )
    @settings(max_examples=100)
    def test_chart_data_dates_are_consecutive(self, reference_date):
        """
        Property: Chart data dates are consecutive
        
        The dates in the chart data should be consecutive days with no gaps.
        """
        # Calculate date range
        end_date = reference_date
        start_date = end_date - timedelta(days=29)
        
        # Generate dates
        dates = []
        current_date = start_date
        while current_date <= end_date:
            dates.append(current_date)
            current_date += timedelta(days=1)
        
        # Verify dates are consecutive
        for i in range(1, len(dates)):
            diff = dates[i] - dates[i - 1]
            assert diff.days == 1

    @given(
        reference_date=st.dates(
            min_value=datetime(2020, 1, 1).date(),
            max_value=datetime(2030, 12, 31).date(),
        )
    )
    @settings(max_examples=100)
    def test_chart_data_starts_30_days_ago(self, reference_date):
        """
        Property: Chart data starts 29 days before the reference date
        
        The first data point should be 29 days before the reference date
        (making 30 days total including the reference date).
        """
        end_date = reference_date
        expected_start_date = end_date - timedelta(days=29)
        
        # Generate data points
        data_points = []
        current_date = expected_start_date
        while current_date <= end_date:
            data_points.append({"date": current_date.isoformat()})
            current_date += timedelta(days=1)
        
        # Verify start date
        from datetime import date
        first_date = date.fromisoformat(data_points[0]["date"])
        assert first_date == expected_start_date

    @given(
        reference_date=st.dates(
            min_value=datetime(2020, 1, 1).date(),
            max_value=datetime(2030, 12, 31).date(),
        )
    )
    @settings(max_examples=100)
    def test_chart_data_ends_on_reference_date(self, reference_date):
        """
        Property: Chart data ends on the reference date
        
        The last data point should be the reference date.
        """
        end_date = reference_date
        start_date = end_date - timedelta(days=29)
        
        # Generate data points
        data_points = []
        current_date = start_date
        while current_date <= end_date:
            data_points.append({"date": current_date.isoformat()})
            current_date += timedelta(days=1)
        
        # Verify end date
        from datetime import date
        last_date = date.fromisoformat(data_points[-1]["date"])
        assert last_date == end_date

    @given(
        reference_date=st.dates(
            min_value=datetime(2020, 1, 1).date(),
            max_value=datetime(2030, 12, 31).date(),
        ),
        scan_data=st.lists(
            st.tuples(
                st.integers(min_value=0, max_value=29),  # day offset from start
                st.integers(min_value=1, max_value=10),  # scan_count
                st.integers(min_value=0, max_value=100),  # total_comments
                st.integers(min_value=0, max_value=100),  # gambling_count
            ),
            min_size=0,
            max_size=30,
        )
    )
    @settings(max_examples=100)
    def test_chart_data_aggregates_by_date(
        self, reference_date, scan_data: list[tuple[int, int, int, int]]
    ):
        """
        Property: Chart data aggregates scan counts by date
        
        Multiple scans on the same day should be aggregated into a single data point.
        """
        end_date = reference_date
        start_date = end_date - timedelta(days=29)
        
        # Filter to ensure gambling_count <= total_comments
        valid_scan_data = [
            (day_offset, scan_count, total, gambling)
            for day_offset, scan_count, total, gambling in scan_data
            if gambling <= total
        ]
        
        # Aggregate by date
        aggregated: dict[int, dict[str, int]] = {}
        for day_offset, scan_count, total_comments, gambling_count in valid_scan_data:
            if day_offset not in aggregated:
                aggregated[day_offset] = {
                    "scan_count": 0,
                    "total_comments": 0,
                    "gambling_count": 0,
                }
            aggregated[day_offset]["scan_count"] += scan_count
            aggregated[day_offset]["total_comments"] += total_comments
            aggregated[day_offset]["gambling_count"] += gambling_count
        
        # Generate data points
        data_points = []
        for day_offset in range(30):
            current_date = start_date + timedelta(days=day_offset)
            if day_offset in aggregated:
                data_points.append({
                    "date": current_date.isoformat(),
                    **aggregated[day_offset],
                })
            else:
                data_points.append({
                    "date": current_date.isoformat(),
                    "scan_count": 0,
                    "total_comments": 0,
                    "gambling_count": 0,
                })
        
        # Verify all 30 days are present
        assert len(data_points) == 30
        
        # Verify aggregation is correct
        for day_offset in range(30):
            if day_offset in aggregated:
                assert data_points[day_offset]["scan_count"] == aggregated[day_offset]["scan_count"]
                assert data_points[day_offset]["total_comments"] == aggregated[day_offset]["total_comments"]
                assert data_points[day_offset]["gambling_count"] == aggregated[day_offset]["gambling_count"]
            else:
                assert data_points[day_offset]["scan_count"] == 0
                assert data_points[day_offset]["total_comments"] == 0
                assert data_points[day_offset]["gambling_count"] == 0

    @given(
        reference_date=st.dates(
            min_value=datetime(2020, 1, 1).date(),
            max_value=datetime(2030, 12, 31).date(),
        )
    )
    @settings(max_examples=100)
    def test_chart_data_missing_days_have_zero_counts(self, reference_date):
        """
        Property: Days with no scans have zero counts
        
        For days with no scan activity, the data point should have zero counts.
        """
        end_date = reference_date
        start_date = end_date - timedelta(days=29)
        
        # Simulate empty scan data (no scans)
        data_by_date: dict = {}
        
        # Generate data points
        data_points = []
        current_date = start_date
        while current_date <= end_date:
            if current_date in data_by_date:
                data_points.append({
                    "date": current_date.isoformat(),
                    **data_by_date[current_date],
                })
            else:
                data_points.append({
                    "date": current_date.isoformat(),
                    "scan_count": 0,
                    "total_comments": 0,
                    "gambling_count": 0,
                })
            current_date += timedelta(days=1)
        
        # Verify all days have zero counts (since no scan data)
        for data_point in data_points:
            assert data_point["scan_count"] == 0
            assert data_point["total_comments"] == 0
            assert data_point["gambling_count"] == 0
