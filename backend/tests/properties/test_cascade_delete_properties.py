"""
Property-based tests for cascade delete integrity.

**Feature: gambling-comment-detector, Property 14: Cascade Delete Integrity**
**Validates: Requirements 10.3**
"""

import asyncio
import uuid
from datetime import datetime, timezone

import pytest
from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.database import Base
from app.models import User, Scan, ScanResult


# Test database URL (SQLite for testing)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


async def create_test_session():
    """Create a fresh test database session."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    
    return engine, async_session_factory


async def cleanup_engine(engine):
    """Clean up the test database engine."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


class TestCascadeDeleteProperties:
    """
    **Feature: gambling-comment-detector, Property 14: Cascade Delete Integrity**
    **Validates: Requirements 10.3**
    
    For any user deletion, all associated scans and scan_results SHALL be deleted
    (no orphan records remain).
    """

    @given(
        num_scans=st.integers(min_value=1, max_value=5),
        num_results_per_scan=st.integers(min_value=1, max_value=10),
    )
    @settings(
        max_examples=100,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_user_deletion_cascades_to_scans_and_results(
        self,
        num_scans: int,
        num_results_per_scan: int,
    ):
        """
        Property: For any user with scans and results, deleting the user
        SHALL delete all associated scans and scan_results.
        """
        async def run_test():
            engine, session_factory = await create_test_session()
            
            try:
                async with session_factory() as session:
                    # Create a user
                    user = User(
                        id=uuid.uuid4(),
                        google_id=f"google_{uuid.uuid4().hex[:16]}",
                        email=f"test_{uuid.uuid4().hex[:8]}@example.com",
                        name="Test User",
                        created_at=datetime.now(timezone.utc),
                        updated_at=datetime.now(timezone.utc),
                    )
                    session.add(user)
                    await session.flush()

                    # Create scans for the user
                    scan_ids = []
                    for i in range(num_scans):
                        scan = Scan(
                            id=uuid.uuid4(),
                            user_id=user.id,
                            video_id=f"video_{uuid.uuid4().hex[:11]}",
                            video_title=f"Test Video {i}",
                            status="completed",
                            total_comments=num_results_per_scan,
                            gambling_count=num_results_per_scan // 2,
                            clean_count=num_results_per_scan - (num_results_per_scan // 2),
                            created_at=datetime.now(timezone.utc),
                        )
                        session.add(scan)
                        await session.flush()
                        scan_ids.append(scan.id)

                        # Create scan results for each scan
                        for j in range(num_results_per_scan):
                            result = ScanResult(
                                id=uuid.uuid4(),
                                scan_id=scan.id,
                                comment_id=f"comment_{uuid.uuid4().hex[:20]}",
                                comment_text=f"Test comment {j}",
                                author_name=f"Author {j}",
                                is_gambling=j % 2 == 0,
                                confidence=0.85,
                                created_at=datetime.now(timezone.utc),
                            )
                            session.add(result)

                    await session.commit()

                    # Verify data was created
                    user_count = await session.scalar(
                        select(func.count()).select_from(User).where(User.id == user.id)
                    )
                    assert user_count == 1

                    scan_count = await session.scalar(
                        select(func.count()).select_from(Scan).where(Scan.user_id == user.id)
                    )
                    assert scan_count == num_scans

                    result_count = await session.scalar(
                        select(func.count()).select_from(ScanResult).where(
                            ScanResult.scan_id.in_(scan_ids)
                        )
                    )
                    assert result_count == num_scans * num_results_per_scan

                    # Delete the user
                    await session.delete(user)
                    await session.commit()

                    # Verify cascade delete - no orphan records should remain
                    user_count_after = await session.scalar(
                        select(func.count()).select_from(User).where(User.id == user.id)
                    )
                    assert user_count_after == 0, "User should be deleted"

                    scan_count_after = await session.scalar(
                        select(func.count()).select_from(Scan).where(Scan.user_id == user.id)
                    )
                    assert scan_count_after == 0, "All scans should be cascade deleted"

                    result_count_after = await session.scalar(
                        select(func.count()).select_from(ScanResult).where(
                            ScanResult.scan_id.in_(scan_ids)
                        )
                    )
                    assert result_count_after == 0, "All scan results should be cascade deleted"
            finally:
                await cleanup_engine(engine)

        asyncio.get_event_loop().run_until_complete(run_test())

    @given(
        num_results=st.integers(min_value=1, max_value=10),
    )
    @settings(
        max_examples=100,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_scan_deletion_cascades_to_results(
        self,
        num_results: int,
    ):
        """
        Property: For any scan with results, deleting the scan
        SHALL delete all associated scan_results.
        """
        async def run_test():
            engine, session_factory = await create_test_session()
            
            try:
                async with session_factory() as session:
                    # Create a user
                    user = User(
                        id=uuid.uuid4(),
                        google_id=f"google_{uuid.uuid4().hex[:16]}",
                        email=f"test_{uuid.uuid4().hex[:8]}@example.com",
                        name="Test User",
                        created_at=datetime.now(timezone.utc),
                        updated_at=datetime.now(timezone.utc),
                    )
                    session.add(user)
                    await session.flush()

                    # Create a scan
                    scan = Scan(
                        id=uuid.uuid4(),
                        user_id=user.id,
                        video_id=f"video_{uuid.uuid4().hex[:11]}",
                        video_title="Test Video",
                        status="completed",
                        total_comments=num_results,
                        gambling_count=num_results // 2,
                        clean_count=num_results - (num_results // 2),
                        created_at=datetime.now(timezone.utc),
                    )
                    session.add(scan)
                    await session.flush()
                    scan_id = scan.id

                    # Create scan results
                    for j in range(num_results):
                        result = ScanResult(
                            id=uuid.uuid4(),
                            scan_id=scan.id,
                            comment_id=f"comment_{uuid.uuid4().hex[:20]}",
                            comment_text=f"Test comment {j}",
                            author_name=f"Author {j}",
                            is_gambling=j % 2 == 0,
                            confidence=0.85,
                            created_at=datetime.now(timezone.utc),
                        )
                        session.add(result)

                    await session.commit()

                    # Verify data was created
                    result_count = await session.scalar(
                        select(func.count()).select_from(ScanResult).where(
                            ScanResult.scan_id == scan_id
                        )
                    )
                    assert result_count == num_results

                    # Delete the scan (not the user)
                    await session.delete(scan)
                    await session.commit()

                    # Verify cascade delete - no orphan results should remain
                    result_count_after = await session.scalar(
                        select(func.count()).select_from(ScanResult).where(
                            ScanResult.scan_id == scan_id
                        )
                    )
                    assert result_count_after == 0, "All scan results should be cascade deleted"

                    # User should still exist
                    user_count = await session.scalar(
                        select(func.count()).select_from(User).where(User.id == user.id)
                    )
                    assert user_count == 1, "User should still exist after scan deletion"
            finally:
                await cleanup_engine(engine)

        asyncio.get_event_loop().run_until_complete(run_test())
