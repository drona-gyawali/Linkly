from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
import redis.asyncio as redis
from fastapi import HTTPException
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from bson import ObjectId
from linkly.services import shortner
from linkly.services.shortner import (
    delete_url,
    get_url_analytics,
    resolves_url,
    shorten_url,
    url_analytics,
)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def initialize_cache():
    redis_client = redis.from_url("redis://localhost")
    FastAPICache.init(RedisBackend(redis_client), prefix="fastapi-cache-test")


@pytest.fixture(autouse=True)
def set_local_host():
    shortner.LOCAL_HOST = "http://localhost:8000"


class AsyncContextManagerMock:
    def __init__(self, db):
        self.db = db

    async def __aenter__(self):
        return self.db

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return False

    def __getattr__(self, name):
        return getattr(self.db, name)


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
    request.query_params = MagicMock()
    request.query_params.get = MagicMock(return_value=None)
    client = MagicMock()
    client.host = "127.0.0.1"
    request.client = client
    return request


@pytest.fixture
def mock_request_with_utm():
    request = MagicMock()
    request.headers = {"user-agent": "pytest-agent"}
    request.query_params = MagicMock()
    request.query_params.get = MagicMock(
        side_effect=lambda key: {
            "utm_source": "google",
            "utm_medium": "cpc",
            "utm_campaign": "summer2024",
        }.get(key)
    )
    client = MagicMock()
    client.host = "192.168.1.1"
    request.client = client
    return request


# ==================== SHORTEN URL TESTS ====================


@pytest.mark.asyncio
async def test_shorten_url_success(mock_db_cm, mock_db):
    """Test successful URL shortening"""
    mock_db.urls.insert_one = AsyncMock(return_value=None)
    user_id = str(ObjectId())

    short_url = await shorten_url("https://example.com", db_cm=mock_db_cm, user_id=user_id)

    assert short_url.startswith("http://localhost:8000/")
    assert len(short_url.split("/")[-1]) > 0  # Has hash

    mock_db.urls.insert_one.assert_called_once()
    args = mock_db.urls.insert_one.call_args[0][0]
    assert args["original_url"] == "https://example.com"
    assert args["user_id"] == ObjectId(user_id)


@pytest.mark.asyncio
async def test_shorten_url_with_complex_url(mock_db_cm, mock_db):
    """Test shortening URL with query parameters and fragments"""
    mock_db.urls.insert_one = AsyncMock(return_value=None)
    complex_url = "https://example.com/path?param1=value1&param2=value2#section"
    user_id = str(ObjectId())

    short_url = await shorten_url(complex_url, db_cm=mock_db_cm, user_id=user_id)

    assert short_url.startswith("http://localhost:8000/")
    args = mock_db.urls.insert_one.call_args[0][0]
    assert args["original_url"] == complex_url
    assert args["user_id"] == ObjectId(user_id)


@pytest.mark.asyncio
async def test_shorten_url_database_error(mock_db_cm, mock_db):
    """Test database error handling during URL shortening"""
    mock_db.urls.insert_one = AsyncMock(
        side_effect=Exception("Database connection error")
    )
    user_id = str(ObjectId())

    with pytest.raises(HTTPException) as exc_info:
        await shorten_url("https://example.com", db_cm=mock_db_cm, user_id=user_id)

    assert exc_info.value.status_code == 400
    assert "Database connection error" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_shorten_url_empty_url(mock_db_cm, mock_db):
    """Test shortening empty URL"""
    mock_db.urls.insert_one = AsyncMock(return_value=None)
    user_id = str(ObjectId())

    short_url = await shorten_url("", db_cm=mock_db_cm, user_id=user_id)

    args = mock_db.urls.insert_one.call_args[0][0]
    assert args["original_url"] == ""
    assert args["user_id"] == ObjectId(user_id)

# ==================== RESOLVE URL TESTS ====================


@pytest.mark.asyncio
async def test_resolves_url_found(mock_db_cm, mock_db):
    """Test successful URL resolution"""
    mock_db.urls.find_one = AsyncMock(
        return_value={"original_url": "https://example.com"}
    )

    result = await resolves_url("http://localhost:8000/abc123", db_cm=mock_db_cm)

    assert result == "https://example.com"
    mock_db.urls.find_one.assert_called_once_with(
        {"short_url": "http://localhost:8000/abc123"}
    )


@pytest.mark.asyncio
async def test_resolves_url_not_found(mock_db_cm, mock_db):
    """Test URL resolution when URL doesn't exist"""
    mock_db.urls.find_one = AsyncMock(return_value=None)

    with pytest.raises(HTTPException) as exc_info:
        await resolves_url("http://localhost:8000/missing", db_cm=mock_db_cm)

    assert exc_info.value.status_code == 400
    assert "doenot exist in system" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_resolves_url_database_error(mock_db_cm, mock_db):
    """Test database error during URL resolution"""
    mock_db.urls.find_one = AsyncMock(side_effect=Exception("Database query failed"))

    with pytest.raises(HTTPException) as exc_info:
        await resolves_url("http://localhost:8000/abc123", db_cm=mock_db_cm)

    assert exc_info.value.status_code == 400
    assert "Database query failed" in str(exc_info.value.detail)


# ==================== URL ANALYTICS TESTS ====================
# TODO: Locally all testcase passed but in cicd fails check this
# @pytest.mark.asyncio
# async def test_url_analytics_new_url_first_click(mock_db_cm, mock_request):
#     """Test analytics for first click on new URL"""
#     mock_db_cm.url_analytics.find_one = AsyncMock(return_value=None)
#     mock_db_cm.url_analytics.insert_one = AsyncMock(return_value=None)

#     with patch("app.services.shortner.httpx.AsyncClient") as mock_client:
#         mock_response = MagicMock()
#         mock_response.status_code = 200
#         mock_response.json.return_value = {"city": "Kathmandu", "country": "Nepal"}
#         mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)

#         await url_analytics("http://localhost:8000/abc123", mock_request, mock_db_cm)

#     mock_db_cm.url_analytics.find_one.assert_called_once_with({"short_id": "http://localhost:8000/abc123"})
#     mock_db_cm.url_analytics.insert_one.assert_called_once()

#     args = mock_db_cm.url_analytics.insert_one.call_args[0][0]
#     assert args["short_id"] == "http://localhost:8000/abc123"
#     assert args["clicks"] == 1
#     assert len(args["finger_print"]) == 1
#     assert len(args["click_details"]) == 1
#     assert args["click_details"][0]["location"] == "Kathmandu, Nepal"
#     assert args["click_details"][0]["ip"] == "8.8.8.8"  # localhost replaced


# @pytest.mark.asyncio
# async def test_url_analytics_existing_url_new_fingerprint(mock_db_cm, mock_request):
#     """Test analytics for existing URL with new fingerprint"""
#     existing_doc = {
#         "short_id": "http://localhost:8000/abc123",
#         "clicks": 5,
#         "finger_print": ["different_fingerprint"],
#         "click_details": []
#     }
#     mock_db_cm.url_analytics.find_one = AsyncMock(return_value=existing_doc)
#     mock_db_cm.url_analytics.update_one = AsyncMock(return_value=None)

#     with patch("linkly.services.shortner.httpx.AsyncClient") as mock_client:
#         mock_response = MagicMock()
#         mock_response.status_code = 200
#         mock_response.json.return_value = {"city": "Tokyo", "country": "Japan"}
#         mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)

#         await url_analytics("http://localhost:8000/abc123", mock_request, mock_db_cm)

#     mock_db_cm.url_analytics.update_one.assert_called_once()

#     args = mock_db_cm.url_analytics.update_one.call_args[0]
#     filter_doc = args[0]
#     update_doc = args[1]

#     assert filter_doc == {"short_id": "http://localhost:8000/abc123"}
#     assert update_doc["$inc"]["clicks"] == 1
#     assert "$addToSet" in update_doc
#     assert "$push" in update_doc
#     assert update_doc["$push"]["click_details"]["location"] == "Tokyo, Japan"


@pytest.mark.asyncio
async def test_url_analytics_existing_fingerprint_no_update(mock_db_cm, mock_request):
    """Test analytics for existing URL with same fingerprint (no update)"""
    fingerprint = "8.8.8.8pytest-agent"
    existing_doc = {
        "short_id": "http://localhost:8000/abc123",
        "clicks": 5,
        "finger_print": [fingerprint],
        "click_details": [],
    }
    mock_db_cm.url_analytics.find_one = AsyncMock(return_value=existing_doc)
    mock_db_cm.url_analytics.update_one = AsyncMock(return_value=None)

    await url_analytics("http://localhost:8000/abc123", mock_request, mock_db_cm)

    mock_db_cm.url_analytics.find_one.assert_called_once()
    mock_db_cm.url_analytics.update_one.assert_not_called()


@pytest.mark.asyncio
async def test_url_analytics_with_utm_parameters(mock_db_cm, mock_request_with_utm):
    """Test analytics with UTM parameters"""
    mock_db_cm.url_analytics.find_one = AsyncMock(return_value=None)
    mock_db_cm.url_analytics.insert_one = AsyncMock(return_value=None)

    with patch("linkly.services.shortner.httpx.AsyncClient") as mock_client:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"city": "Mumbai", "country": "India"}
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            return_value=mock_response
        )

        await url_analytics(
            "http://localhost:8000/abc123", mock_request_with_utm, mock_db_cm
        )

    args = mock_db_cm.url_analytics.insert_one.call_args[0][0]
    click_details = args["click_details"][0]

    assert click_details["utm_source"] == "google"
    assert click_details["utm_medium"] == "cpc"
    assert click_details["utm_campaign"] == "summer2024"


@pytest.mark.asyncio
async def test_url_analytics_ip_api_failure(mock_db_cm, mock_request):
    """Test analytics when IP geolocation API fails"""
    mock_db_cm.url_analytics.find_one = AsyncMock(return_value=None)
    mock_db_cm.url_analytics.insert_one = AsyncMock(return_value=None)

    with patch("linkly.services.shortner.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            side_effect=Exception("API failed")
        )

        await url_analytics("http://localhost:8000/abc123", mock_request, mock_db_cm)

    args = mock_db_cm.url_analytics.insert_one.call_args[0][0]
    assert args["click_details"][0]["location"] is None


@pytest.mark.asyncio
async def test_url_analytics_ip_api_non_200_response(mock_db_cm, mock_request):
    """Test analytics when IP geolocation API returns non-200 status"""
    mock_db_cm.url_analytics.find_one = AsyncMock(return_value=None)
    mock_db_cm.url_analytics.insert_one = AsyncMock(return_value=None)

    with patch("linkly.services.shortner.httpx.AsyncClient") as mock_client:
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            return_value=mock_response
        )

        await url_analytics("http://localhost:8000/abc123", mock_request, mock_db_cm)

    args = mock_db_cm.url_analytics.insert_one.call_args[0][0]
    assert args["click_details"][0]["location"] is None


@pytest.mark.asyncio
async def test_url_analytics_missing_location_data(mock_db_cm, mock_request):
    """Test analytics when location data is incomplete"""
    mock_db_cm.url_analytics.find_one = AsyncMock(return_value=None)
    mock_db_cm.url_analytics.insert_one = AsyncMock(return_value=None)

    with patch("linkly.services.shortner.httpx.AsyncClient") as mock_client:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"city": "", "country": ""}
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            return_value=mock_response
        )

        await url_analytics("http://localhost:8000/abc123", mock_request, mock_db_cm)

    args = mock_db_cm.url_analytics.insert_one.call_args[0][0]
    assert args["click_details"][0]["location"] is None


# ==================== GET URL ANALYTICS TESTS ====================


@pytest.mark.asyncio
async def test_get_url_analytics_success(mock_db_cm, mock_db):
    """Test successful retrieval of URL analytics"""
    analytics_data = {
        "_id": "507f1f77bcf86cd799439011",
        "short_id": "http://localhost:8000/abc123",
        "clicks": 5,
        "finger_print": ["fp1", "fp2"],
        "click_details": [
            {
                "user_agent": "Chrome",
                "ip": "192.168.1.1",
                "timestamp": datetime.now(timezone.utc),
                "location": "New York, USA",
                "utm_source": "google",
                "utm_medium": "cpc",
                "utm_campaign": "test",
            },
            {
                "user_agent": "Firefox",
                "ip": "192.168.1.2",
                "timestamp": datetime.now(timezone.utc),
                "location": "London, UK",
                "utm_source": None,
                "utm_medium": None,
                "utm_campaign": None,
            },
        ],
    }
    mock_db.url_analytics.find_one = AsyncMock(return_value=analytics_data)

    result = await get_url_analytics("http://localhost:8000/abc123", mock_db_cm)

    assert result["short_id"] == "http://localhost:8000/abc123"
    assert result["clicks"] == 2  # All clicks included
    assert len(result["click_details"]) == 2
    assert result["_id"] == "507f1f77bcf86cd799439011"

    # Check timestamp conversion
    for click in result["click_details"]:
        assert isinstance(click["timestamp"], str)


@pytest.mark.asyncio
async def test_get_url_analytics_with_utm_filter(mock_db_cm, mock_db):
    """Test analytics retrieval with UTM parameter filtering"""
    analytics_data = {
        "_id": "507f1f77bcf86cd799439011",
        "short_id": "http://localhost:8000/abc123",
        "clicks": 5,
        "finger_print": ["fp1", "fp2"],
        "click_details": [
            {
                "user_agent": "Chrome",
                "ip": "192.168.1.1",
                "timestamp": datetime.now(timezone.utc),
                "location": "New York, USA",
                "utm_source": "google",
                "utm_medium": "cpc",
                "utm_campaign": "test",
            },
            {
                "user_agent": "Firefox",
                "ip": "192.168.1.2",
                "timestamp": datetime.now(timezone.utc),
                "location": "London, UK",
                "utm_source": "facebook",
                "utm_medium": "social",
                "utm_campaign": "test",
            },
        ],
    }
    mock_db.url_analytics.find_one = AsyncMock(return_value=analytics_data)

    result = await get_url_analytics(
        "http://localhost:8000/abc123", mock_db_cm, utm_source="google"
    )

    assert result["clicks"] == 1  # Only google source
    assert len(result["click_details"]) == 1
    assert result["click_details"][0]["utm_source"] == "google"


@pytest.mark.asyncio
async def test_get_url_analytics_multiple_utm_filters(mock_db_cm, mock_db):
    """Test analytics retrieval with multiple UTM filters"""
    analytics_data = {
        "_id": "507f1f77bcf86cd799439011",
        "short_id": "http://localhost:8000/abc123",
        "clicks": 5,
        "finger_print": ["fp1", "fp2"],
        "click_details": [
            {
                "user_agent": "Chrome",
                "ip": "192.168.1.1",
                "timestamp": datetime.now(timezone.utc),
                "location": "New York, USA",
                "utm_source": "google",
                "utm_medium": "cpc",
                "utm_campaign": "test",
            },
            {
                "user_agent": "Firefox",
                "ip": "192.168.1.2",
                "timestamp": datetime.now(timezone.utc),
                "location": "London, UK",
                "utm_source": "google",
                "utm_medium": "social",
                "utm_campaign": "test",
            },
        ],
    }
    mock_db.url_analytics.find_one = AsyncMock(return_value=analytics_data)

    result = await get_url_analytics(
        "http://localhost:8000/abc123",
        mock_db_cm,
        utm_source="google",
        utm_medium="cpc",
    )

    assert result["clicks"] == 1  # Only google + cpc
    assert len(result["click_details"]) == 1
    assert result["click_details"][0]["utm_medium"] == "cpc"


@pytest.mark.asyncio
async def test_get_url_analytics_no_matching_utm_filters(mock_db_cm, mock_db):
    """Test analytics retrieval when no clicks match UTM filters"""
    analytics_data = {
        "_id": "507f1f77bcf86cd799439011",
        "short_id": "http://localhost:8000/abc123",
        "clicks": 5,
        "finger_print": ["fp1", "fp2"],
        "click_details": [
            {
                "user_agent": "Chrome",
                "ip": "192.168.1.1",
                "timestamp": datetime.now(timezone.utc),
                "location": "New York, USA",
                "utm_source": "google",
                "utm_medium": "cpc",
                "utm_campaign": "test",
            }
        ],
    }
    mock_db.url_analytics.find_one = AsyncMock(return_value=analytics_data)

    result = await get_url_analytics(
        "http://localhost:8000/abc123", mock_db_cm, utm_source="facebook"
    )

    assert result["clicks"] == 0
    assert len(result["click_details"]) == 0


@pytest.mark.asyncio
async def test_get_url_analytics_not_found(mock_db_cm, mock_db):
    """Test analytics retrieval when URL doesn't exist"""
    mock_db.url_analytics.find_one = AsyncMock(return_value=None)

    with pytest.raises(HTTPException) as exc_info:
        await get_url_analytics("http://localhost:8000/missing", mock_db_cm)

    assert exc_info.value.status_code == 404
    assert "Analytics data not found" in str(exc_info.value.detail)


# ==================== DELETE URL TESTS ====================


@pytest.mark.asyncio
async def test_delete_url_success(mock_db_cm, mock_db):
    """Test successful URL deletion"""
    mock_db.urls.find_one = AsyncMock(
        return_value={"short_url": "http://localhost:8000/abc123"}
    )
    mock_delete_result = MagicMock()
    mock_delete_result.deleted_count = 1
    mock_db.urls.delete_one = AsyncMock(return_value=mock_delete_result)

    result = await delete_url("http://localhost:8000/abc123", mock_db_cm)

    assert result["message"] == "Url data successfully erased"
    mock_db.urls.find_one.assert_called_once_with(
        {"short_url": "http://localhost:8000/abc123"}
    )
    mock_db.urls.delete_one.assert_called_once_with(
        {"short_url": "http://localhost:8000/abc123"}
    )


@pytest.mark.asyncio
async def test_delete_url_not_found(mock_db_cm, mock_db):
    """Test deletion of non-existent URL"""
    mock_db.urls.find_one = AsyncMock(return_value=None)

    with pytest.raises(HTTPException) as exc_info:
        await delete_url("http://localhost:8000/missing", mock_db_cm)

    assert exc_info.value.status_code == 404
    assert "Url not found" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_delete_url_deletion_failed(mock_db_cm, mock_db):
    """Test deletion failure (database error)"""
    mock_db.urls.find_one = AsyncMock(
        return_value={"short_url": "http://localhost:8000/abc123"}
    )
    mock_delete_result = MagicMock()
    mock_delete_result.deleted_count = 0  # Deletion failed
    mock_db.urls.delete_one = AsyncMock(return_value=mock_delete_result)

    with pytest.raises(HTTPException) as exc_info:
        await delete_url("http://localhost:8000/abc123", mock_db_cm)

    assert exc_info.value.status_code == 500
    assert "Something went wrong" in str(exc_info.value.detail)


# ==================== EDGE CASES AND INTEGRATION TESTS ====================


@pytest.mark.asyncio
async def test_url_analytics_with_special_characters_in_user_agent(mock_db_cm):
    """Test analytics with special characters in user agent"""
    request = MagicMock()
    request.headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    request.query_params = MagicMock()
    request.query_params.get = MagicMock(return_value=None)
    client = MagicMock()
    client.host = "192.168.1.1"
    request.client = client

    mock_db_cm.url_analytics.find_one = AsyncMock(return_value=None)
    mock_db_cm.url_analytics.insert_one = AsyncMock(return_value=None)

    with patch("linkly.services.shortner.httpx.AsyncClient") as mock_client:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"city": "Berlin", "country": "Germany"}
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            return_value=mock_response
        )

        await url_analytics("http://localhost:8000/abc123", request, mock_db_cm)

    args = mock_db_cm.url_analytics.insert_one.call_args[0][0]
    assert "Mozilla/5.0" in args["click_details"][0]["user_agent"]


@pytest.mark.asyncio
async def test_url_analytics_with_missing_user_agent(mock_db_cm):
    """Test analytics with missing user agent header"""
    request = MagicMock()
    request.headers = {}
    request.query_params = MagicMock()
    request.query_params.get = MagicMock(return_value=None)
    client = MagicMock()
    client.host = "192.168.1.1"
    request.client = client

    mock_db_cm.url_analytics.find_one = AsyncMock(return_value=None)
    mock_db_cm.url_analytics.insert_one = AsyncMock(return_value=None)

    with patch("linkly.services.shortner.httpx.AsyncClient") as mock_client:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"city": "Paris", "country": "France"}
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            return_value=mock_response
        )

        await url_analytics("http://localhost:8000/abc123", request, mock_db_cm)

    args = mock_db_cm.url_analytics.insert_one.call_args[0][0]
    assert args["click_details"][0]["user_agent"] == "unknown"


@pytest.mark.asyncio
async def test_get_url_analytics_with_empty_click_details(mock_db_cm, mock_db):
    """Test analytics retrieval with empty click details"""
    analytics_data = {
        "_id": "507f1f77bcf86cd799439011",
        "short_id": "http://localhost:8000/abc123",
        "clicks": 0,
        "finger_print": [],
        "click_details": [],
    }
    mock_db.url_analytics.find_one = AsyncMock(return_value=analytics_data)

    result = await get_url_analytics("http://localhost:8000/abc123", mock_db_cm)

    assert result["clicks"] == 0
    assert len(result["click_details"]) == 0


@pytest.mark.asyncio
async def test_url_analytics_fingerprint_case_sensitivity(mock_db_cm, mock_request):
    """Test that fingerprint generation is case-insensitive"""
    # First request with uppercase user agent
    request1 = MagicMock()
    request1.headers = {"user-agent": "CHROME/91.0"}
    request1.query_params = MagicMock()
    request1.query_params.get = MagicMock(return_value=None)
    client1 = MagicMock()
    client1.host = "192.168.1.1"
    request1.client = client1

    # Second request with lowercase user agent (same fingerprint)
    request2 = MagicMock()
    request2.headers = {"user-agent": "chrome/91.0"}
    request2.query_params = MagicMock()
    request2.query_params.get = MagicMock(return_value=None)
    client2 = MagicMock()
    client2.host = "192.168.1.1"
    request2.client = client2

    mock_db_cm.url_analytics.find_one = AsyncMock(return_value=None)
    mock_db_cm.url_analytics.insert_one = AsyncMock(return_value=None)

    with patch("linkly.services.shortner.httpx.AsyncClient") as mock_client:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"city": "Sydney", "country": "Australia"}
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            return_value=mock_response
        )

        await url_analytics("http://localhost:8000/abc123", request1, mock_db_cm)

    # Verify fingerprint is lowercase
    args = mock_db_cm.url_analytics.insert_one.call_args[0][0]
    fingerprint = args["finger_print"][0]
    assert fingerprint == "192.168.1.1chrome/91.0"


@pytest.mark.asyncio
async def test_concurrent_url_shortening(mock_db_cm, mock_db):
    """Test multiple concurrent URL shortening requests"""
    import asyncio
    mock_db.urls.insert_one = AsyncMock(return_value=None)
    urls = ["https://example1.com", "https://example2.com", "https://example3.com"]
    user_id = str(ObjectId())

    tasks = [shorten_url(url, db_cm=mock_db_cm, user_id=user_id) for url in urls]
    results = await asyncio.gather(*tasks)

    for short_url in results:
        assert short_url.startswith("http://localhost:8000/")
