"""
Shared test fixtures and mock data for AGNITE backend tests.
"""

from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import create_app


# ── Sample NASA FIRMS CSV ─────────────────────────────────────────────
# Realistic subset matching the public download format.
SAMPLE_FIRMS_CSV = """\
latitude,longitude,brightness,scan,track,acq_date,acq_time,satellite,confidence,version,bright_ti4,bright_ti5,frp,daynight,type
21.1466,79.0889,338.5,0.39,0.36,2026-09-13,1230,N20,nominal,2.0NRT,313.2,289.1,45.2,D,0
22.3456,78.1234,342.1,0.39,0.36,2026-09-13,1230,N20,high,2.0NRT,315.0,290.3,67.8,D,0
19.8765,73.5432,310.0,0.39,0.36,2026-09-13,0630,N20,low,2.0NRT,300.1,285.5,12.3,N,0
28.6100,77.2300,350.0,0.39,0.36,2026-09-13,0830,N20,nominal,2.0NRT,320.5,295.0,88.1,D,0
"""

# CSV with MODIS-style brightness column
SAMPLE_MODIS_CSV = """\
latitude,longitude,brightness,scan,track,acq_date,acq_time,satellite,confidence,version,frp,daynight,type
25.5000,85.0000,320.0,1.0,1.0,2026-09-13,0500,Terra,80,6.1NRT,30.5,D,0
"""

# Empty but valid CSV (header only)
EMPTY_FIRMS_CSV = """\
latitude,longitude,brightness,scan,track,acq_date,acq_time,satellite,confidence,version,bright_ti4,bright_ti5,frp,daynight,type
"""

# Invalid CSV (missing required columns)
INVALID_HEADER_CSV = """\
lat,lon,temp,date
21.0,79.0,300,2026-09-13
"""


@pytest.fixture(scope="session", autouse=True)
def clean_test_db_session():
    """Ensure database tables exist and are clean for test session."""
    import app.db.models  # noqa: F401
    from app.db.base import Base
    from app.db.session import engine
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


@pytest.fixture
def app():
    """Create a fresh FastAPI app for testing."""
    return create_app()


@pytest_asyncio.fixture
async def client(app):
    """
    Async HTTP test client that triggers the FastAPI lifespan,
    so app.state is properly initialized.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, base_url="http://test"
    ) as ac:
        # Manually trigger the lifespan startup
        # ASGITransport handles lifespan events when we send requests,
        # but we need to ensure the app state is initialized.
        # The simplest approach: use the lifespan context directly.
        pass

    # Use the app's lifespan properly
    from contextlib import asynccontextmanager
    from app.core.config import get_settings
    from app.services.firms_service import FirmsService
    import httpx as _httpx

    # Initialize app state manually for tests
    settings = get_settings()
    app.state.settings = settings
    http_client = _httpx.AsyncClient(follow_redirects=False, timeout=30.0)
    app.state.firms_service = FirmsService(
        http_client=http_client, cache_ttl_seconds=settings.nasa_cache_ttl_seconds
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    await http_client.aclose()
