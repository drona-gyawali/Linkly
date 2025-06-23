import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException
from datetime import datetime, timezone

from app.services.shortner import (
    shorten_url,
    resolves_url,
    url_analytics,
    get_url_analytics,
)

class AsyncContextManagerMock:
    def __init__(self, db):
        self.db = db
    async def __aenter__(self):
        return self.db
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return False

@pytest.fixture
def mock_db():
    db = MagicMock()
    db.urls = MagicMock()
    db.url_analytics = MagicMock()
    return db

@pytest.fixture
def mock_db_cm(mock_db):
    return AsyncContextManagerMock(mock_db)

@pytest.fixture
def mock_request():
    request = MagicMock()
    request.headers = {"user-agent": "pytest-agent"}
    client = MagicMock()
    client.host = "127.0.0.1"
    request.client = client
    return request

@pytest.mark.asyncio
async def test_shorten_url_success(mock_db_cm, mock_db):
    mock_db.urls.insert_one = AsyncMock(return_value=None)

    short_url = await shorten_url("https://example.com", db_cm=mock_db_cm)
    assert short_url.startswith("http://localhost:8000/") or short_url.startswith("https://localhost:8000/")

    # insert_one called with correct data
    mock_db.urls.insert_one.assert_called_once()
    args = mock_db.urls.insert_one.call_args[0][0]
    assert args["original_url"] == "https://example.com"
    assert args["short_url"] == short_url

@pytest.mark.asyncio
async def test_shorten_url_failure(mock_db_cm, mock_db):
    mock_db.urls.insert_one = AsyncMock(side_effect=Exception("insert error"))

    with pytest.raises(HTTPException) as exc_info:
        await shorten_url("https://example.com", db_cm=mock_db_cm)
    assert exc_info.value.status_code == 400
    assert "insert error" in exc_info.value.detail

@pytest.mark.asyncio
async def test_resolves_url_found(mock_db_cm, mock_db):
    mock_db.urls.find_one = AsyncMock(return_value={"original_url": "https://example.com"})

    result = await resolves_url("http://localhost:8000/abc123", db_cm=mock_db_cm)
    assert result == "https://example.com"

@pytest.mark.asyncio
async def test_resolves_url_not_found(mock_db_cm, mock_db):
    mock_db.urls.find_one = AsyncMock(return_value=None)

    with pytest.raises(HTTPException) as exc_info:
        await resolves_url("http://localhost:8000/missing", db_cm=mock_db_cm)
    assert exc_info.value.status_code == 400

@pytest.mark.asyncio
@patch("app.services.shortner.httpx.AsyncClient.get")
async def test_url_analytics_updates(mock_httpx_get, mock_db_cm, mock_db, mock_request):
    # Setup HTTPX mock response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"city": "Kathmandu", "country": "Nepal"}
    mock_httpx_get.return_value = mock_response

    mock_db.url_analytics.update_one = AsyncMock(return_value=None)

    await url_analytics("http://localhost:8000/abc123", mock_request, mock_db_cm)

    mock_httpx_get.assert_called_once()
    mock_db.url_analytics.update_one.assert_called_once()

    # Check update_one called with expected structure
    args = mock_db.url_analytics.update_one.call_args[0]
    filter_ = args[0]
    update = args[1]

    assert filter_ == {"short_id": "http://localhost:8000/abc123"}
    assert "$inc" in update and update["$inc"]["clicks"] == 1
    assert "$push" in update
    click_info = update["$push"]["click_details"]
    assert click_info["ip"] == "8.8.8.8"  # ip replaced from 127.0.0.1 in service code
    assert click_info["location"] == "Kathmandu, Nepal"
    assert "user_agent" in click_info
    assert isinstance(click_info["timestamp"], datetime)

@pytest.mark.asyncio
async def test_url_analytics_ip_api_failure(mock_db_cm, mock_db, mock_request):
    # Simulate httpx raising exception (e.g., network failure)
    with patch("app.services.shortner.httpx.AsyncClient.get", side_effect=Exception("fail")):
        mock_db.url_analytics.update_one = AsyncMock(return_value=None)
        await url_analytics("http://localhost:8000/abc123", mock_request, mock_db_cm)
        mock_db.url_analytics.update_one.assert_called_once()

@pytest.mark.asyncio
async def test_get_url_analytics_found(mock_db_cm, mock_db):
    fake_doc = {
        "_id": "someid",
        "short_id": "http://localhost:8000/abc123",
        "click_details": [
            {
                "user_agent": "pytest-agent",
                "ip": "8.8.8.8",
                "timestamp": datetime(2025, 6, 23, 12, 0, tzinfo=timezone.utc),
                "location": "Kathmandu, Nepal",
            }
        ],
        "clicks": 5,
    }
    mock_db.url_analytics.find_one = AsyncMock(return_value=fake_doc)

    response = await get_url_analytics("http://localhost:8000/abc123", mock_db_cm)

    assert response["_id"] == "someid"
    assert response["clicks"] == 5
    assert isinstance(response["click_details"][0]["timestamp"], str)  # isoformat string
    assert response["click_details"][0]["location"] == "Kathmandu, Nepal"

@pytest.mark.asyncio
async def test_get_url_analytics_not_found(mock_db_cm, mock_db):
    mock_db.url_analytics.find_one = AsyncMock(return_value=None)
    with pytest.raises(HTTPException) as exc_info:
        await get_url_analytics("http://localhost:8000/missing", mock_db_cm)
    assert exc_info.value.status_code == 404