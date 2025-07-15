"""
Robust URL Analytics Tests - Fixed for CI/CD consistency
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

# ==================== FIXTURES ====================


@pytest.fixture
def mock_db_cm():
    """Mock database connection manager"""
    mock_db = MagicMock()
    mock_db.url_analytics = MagicMock()
    return mock_db


@pytest.fixture
def mock_request():
    """Mock FastAPI request object"""
    request = MagicMock()
    request.headers = {"user-agent": "pytest-agent"}
    request.query_params = MagicMock()
    request.query_params.get = MagicMock(return_value=None)
    client = MagicMock()
    client.host = "127.0.0.1"  # localhost - will be replaced with 8.8.8.8
    request.client = client
    return request


@pytest.fixture
def mock_request_with_utm():
    """Mock FastAPI request object with UTM parameters"""
    request = MagicMock()
    request.headers = {"user-agent": "pytest-agent"}
    request.query_params = MagicMock()

    # Mock UTM parameters
    def mock_get(param, default=None):
        utm_params = {
            "utm_source": "google",
            "utm_medium": "cpc",
            "utm_campaign": "summer2024",
        }
        return utm_params.get(param, default)

    request.query_params.get = mock_get
    client = MagicMock()
    client.host = "192.168.1.100"
    request.client = client
    return request


# ==================== ROBUST URL ANALYTICS TESTS ====================


@pytest.mark.asyncio
async def test_url_analytics_new_url_first_click_robust(mock_db_cm, mock_request):
    """Test analytics for first click on new URL - Robust version"""
    # Setup mocks
    mock_db_cm.url_analytics.find_one = AsyncMock(return_value=None)
    mock_db_cm.url_analytics.insert_one = AsyncMock(return_value=None)

    # Mock the entire httpx interaction more robustly
    with patch("linkly.services.shortner.httpx.AsyncClient") as MockAsyncClient:
        # Create a mock client instance
        mock_client_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"city": "Kathmandu", "country": "Nepal"}

        # Setup the async context manager properly
        mock_client_instance.get = AsyncMock(return_value=mock_response)

        # Create async context manager mock
        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_context_manager.__aexit__ = AsyncMock(return_value=None)

        MockAsyncClient.return_value = mock_context_manager

        # Import and call the function
        from linkly.services.shortner import url_analytics

        await url_analytics("http://localhost:8000/abc123", mock_request, mock_db_cm)

    # Verify find_one was called
    mock_db_cm.url_analytics.find_one.assert_called_once_with(
        {"short_id": "http://localhost:8000/abc123"}
    )

    # Verify insert_one was called
    mock_db_cm.url_analytics.insert_one.assert_called_once()

    # Verify the inserted document structure
    insert_args = mock_db_cm.url_analytics.insert_one.call_args[0][0]
    assert insert_args["short_id"] == "http://localhost:8000/abc123"
    assert insert_args["clicks"] == 1
    assert len(insert_args["finger_print"]) == 1
    assert len(insert_args["click_details"]) == 1

    # Verify click details structure
    click_detail = insert_args["click_details"][0]
    assert click_detail["location"] == "Kathmandu, Nepal"
    assert click_detail["ip"] == "8.8.8.8"  # localhost replaced with 8.8.8.8
    assert click_detail["user_agent"] == "pytest-agent"
    assert isinstance(click_detail["timestamp"], datetime)
    assert click_detail["utm_source"] is None
    assert click_detail["utm_medium"] is None
    assert click_detail["utm_campaign"] is None


@pytest.mark.asyncio
async def test_url_analytics_existing_url_new_fingerprint_robust(
    mock_db_cm, mock_request
):
    """Test analytics for existing URL with new fingerprint - Robust version"""
    # Setup existing document
    existing_doc = {
        "short_id": "http://localhost:8000/abc123",
        "clicks": 5,
        "finger_print": ["different_fingerprint"],
        "click_details": [
            {
                "user_agent": "old-agent",
                "ip": "192.168.1.100",
                "timestamp": datetime.now(timezone.utc),
                "location": "Old Location",
                "utm_source": None,
                "utm_medium": None,
                "utm_campaign": None,
            }
        ],
    }

    mock_db_cm.url_analytics.find_one = AsyncMock(return_value=existing_doc)
    mock_db_cm.url_analytics.update_one = AsyncMock(return_value=None)

    # Mock httpx with proper async context management
    with patch("linkly.services.shortner.httpx.AsyncClient") as MockAsyncClient:
        mock_client_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"city": "Tokyo", "country": "Japan"}

        mock_client_instance.get = AsyncMock(return_value=mock_response)

        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_context_manager.__aexit__ = AsyncMock(return_value=None)

        MockAsyncClient.return_value = mock_context_manager

        from linkly.services.shortner import url_analytics

        await url_analytics("http://localhost:8000/abc123", mock_request, mock_db_cm)

    # Verify find_one was called
    mock_db_cm.url_analytics.find_one.assert_called_once_with(
        {"short_id": "http://localhost:8000/abc123"}
    )

    # Verify update_one was called
    mock_db_cm.url_analytics.update_one.assert_called_once()

    # Verify the update operation
    update_args = mock_db_cm.url_analytics.update_one.call_args[0]
    filter_doc = update_args[0]
    update_doc = update_args[1]

    assert filter_doc == {"short_id": "http://localhost:8000/abc123"}
    assert update_doc["$inc"]["clicks"] == 1
    assert "$addToSet" in update_doc
    assert "$push" in update_doc

    # Verify the pushed click details
    pushed_click = update_doc["$push"]["click_details"]
    assert pushed_click["location"] == "Tokyo, Japan"
    assert pushed_click["ip"] == "8.8.8.8"
    assert pushed_click["user_agent"] == "pytest-agent"
    assert isinstance(pushed_click["timestamp"], datetime)


@pytest.mark.asyncio
async def test_url_analytics_location_api_failure_robust(mock_db_cm, mock_request):
    """Test analytics when IP geolocation API fails - Robust version"""
    mock_db_cm.url_analytics.find_one = AsyncMock(return_value=None)
    mock_db_cm.url_analytics.insert_one = AsyncMock(return_value=None)

    # Mock httpx to raise an exception
    with patch("linkly.services.shortner.httpx.AsyncClient") as MockAsyncClient:
        mock_client_instance = MagicMock()
        mock_client_instance.get = AsyncMock(side_effect=Exception("API failed"))

        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_context_manager.__aexit__ = AsyncMock(return_value=None)

        MockAsyncClient.return_value = mock_context_manager

        from linkly.services.shortner import url_analytics

        await url_analytics("http://localhost:8000/abc123", mock_request, mock_db_cm)

    # Verify the document was inserted with location=None
    mock_db_cm.url_analytics.insert_one.assert_called_once()
    insert_args = mock_db_cm.url_analytics.insert_one.call_args[0][0]
    assert insert_args["click_details"][0]["location"] is None


@pytest.mark.asyncio
async def test_url_analytics_api_non_200_response_robust(mock_db_cm, mock_request):
    """Test analytics when IP geolocation API returns non-200 status - Robust version"""
    mock_db_cm.url_analytics.find_one = AsyncMock(return_value=None)
    mock_db_cm.url_analytics.insert_one = AsyncMock(return_value=None)

    # Mock httpx to return non-200 status
    with patch("linkly.services.shortner.httpx.AsyncClient") as MockAsyncClient:
        mock_client_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_client_instance.get = AsyncMock(return_value=mock_response)

        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_context_manager.__aexit__ = AsyncMock(return_value=None)

        MockAsyncClient.return_value = mock_context_manager

        from linkly.services.shortner import url_analytics

        await url_analytics("http://localhost:8000/abc123", mock_request, mock_db_cm)

    # Verify the document was inserted with location=None
    mock_db_cm.url_analytics.insert_one.assert_called_once()
    insert_args = mock_db_cm.url_analytics.insert_one.call_args[0][0]
    assert insert_args["click_details"][0]["location"] is None


@pytest.mark.asyncio
async def test_url_analytics_with_utm_parameters_robust(
    mock_db_cm, mock_request_with_utm
):
    """Test analytics with UTM parameters - Robust version"""
    mock_db_cm.url_analytics.find_one = AsyncMock(return_value=None)
    mock_db_cm.url_analytics.insert_one = AsyncMock(return_value=None)

    # Mock successful API response
    with patch("linkly.services.shortner.httpx.AsyncClient") as MockAsyncClient:
        mock_client_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"city": "Mumbai", "country": "India"}
        mock_client_instance.get = AsyncMock(return_value=mock_response)

        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_context_manager.__aexit__ = AsyncMock(return_value=None)

        MockAsyncClient.return_value = mock_context_manager

        from linkly.services.shortner import url_analytics

        await url_analytics(
            "http://localhost:8000/abc123", mock_request_with_utm, mock_db_cm
        )

    # Verify UTM parameters were captured
    mock_db_cm.url_analytics.insert_one.assert_called_once()
    insert_args = mock_db_cm.url_analytics.insert_one.call_args[0][0]
    click_detail = insert_args["click_details"][0]

    assert click_detail["utm_source"] == "google"
    assert click_detail["utm_medium"] == "cpc"
    assert click_detail["utm_campaign"] == "summer2024"
    assert click_detail["location"] == "Mumbai, India"


@pytest.mark.asyncio
async def test_url_analytics_empty_location_data_robust(mock_db_cm, mock_request):
    """Test analytics when location data is empty - Robust version"""
    mock_db_cm.url_analytics.find_one = AsyncMock(return_value=None)
    mock_db_cm.url_analytics.insert_one = AsyncMock(return_value=None)

    # Mock API response with empty location data
    with patch("linkly.services.shortner.httpx.AsyncClient") as MockAsyncClient:
        mock_client_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"city": "", "country": ""}
        mock_client_instance.get = AsyncMock(return_value=mock_response)

        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_context_manager.__aexit__ = AsyncMock(return_value=None)

        MockAsyncClient.return_value = mock_context_manager

        from linkly.services.shortner import url_analytics

        await url_analytics("http://localhost:8000/abc123", mock_request, mock_db_cm)

    # Verify location is None when empty
    mock_db_cm.url_analytics.insert_one.assert_called_once()
    insert_args = mock_db_cm.url_analytics.insert_one.call_args[0][0]
    assert insert_args["click_details"][0]["location"] is None


@pytest.mark.asyncio
async def test_url_analytics_fingerprint_generation_robust(mock_db_cm):
    """Test fingerprint generation is consistent - Robust version"""
    # Create a request with specific IP and user agent
    request = MagicMock()
    request.headers = {"user-agent": "TestBrowser/1.0"}
    request.query_params = MagicMock()
    request.query_params.get = MagicMock(return_value=None)
    client = MagicMock()
    client.host = "192.168.1.100"
    request.client = client

    mock_db_cm.url_analytics.find_one = AsyncMock(return_value=None)
    mock_db_cm.url_analytics.insert_one = AsyncMock(return_value=None)

    # Mock successful API response
    with patch("linkly.services.shortner.httpx.AsyncClient") as MockAsyncClient:
        mock_client_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"city": "TestCity", "country": "TestCountry"}
        mock_client_instance.get = AsyncMock(return_value=mock_response)

        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_context_manager.__aexit__ = AsyncMock(return_value=None)

        MockAsyncClient.return_value = mock_context_manager

        from linkly.services.shortner import url_analytics

        await url_analytics("http://localhost:8000/abc123", request, mock_db_cm)

    # Verify fingerprint is generated correctly (IP + user-agent, lowercase)
    mock_db_cm.url_analytics.insert_one.assert_called_once()
    insert_args = mock_db_cm.url_analytics.insert_one.call_args[0][0]
    expected_fingerprint = "192.168.1.100testbrowser/1.0"
    assert insert_args["finger_print"][0] == expected_fingerprint


@pytest.mark.asyncio
async def test_url_analytics_localhost_ip_replacement_robust(mock_db_cm):
    """Test localhost IP replacement works correctly - Robust version"""
    # Create request with localhost IP
    request = MagicMock()
    request.headers = {"user-agent": "TestAgent"}
    request.query_params = MagicMock()
    request.query_params.get = MagicMock(return_value=None)
    client = MagicMock()
    client.host = "127.0.0.1"  # localhost
    request.client = client

    mock_db_cm.url_analytics.find_one = AsyncMock(return_value=None)
    mock_db_cm.url_analytics.insert_one = AsyncMock(return_value=None)

    # Mock successful API response
    with patch("linkly.services.shortner.httpx.AsyncClient") as MockAsyncClient:
        mock_client_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"city": "Mountain View", "country": "USA"}
        mock_client_instance.get = AsyncMock(return_value=mock_response)

        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_context_manager.__aexit__ = AsyncMock(return_value=None)

        MockAsyncClient.return_value = mock_context_manager

        from linkly.services.shortner import url_analytics

        await url_analytics("http://localhost:8000/abc123", request, mock_db_cm)

    # Verify localhost IP was replaced with 8.8.8.8
    mock_db_cm.url_analytics.insert_one.assert_called_once()
    insert_args = mock_db_cm.url_analytics.insert_one.call_args[0][0]
    assert insert_args["click_details"][0]["ip"] == "8.8.8.8"

    # Verify the API was called with the replaced IP
    mock_client_instance.get.assert_called_once()
    api_call_args = mock_client_instance.get.call_args[0][0]
    assert "8.8.8.8" in api_call_args


@pytest.mark.asyncio
async def test_url_analytics_missing_user_agent_robust(mock_db_cm):
    """Test analytics with missing user agent header - Robust version"""
    # Create request without user-agent header
    request = MagicMock()
    request.headers = {}  # No user-agent header
    request.query_params = MagicMock()
    request.query_params.get = MagicMock(return_value=None)
    client = MagicMock()
    client.host = "192.168.1.1"
    request.client = client

    mock_db_cm.url_analytics.find_one = AsyncMock(return_value=None)
    mock_db_cm.url_analytics.insert_one = AsyncMock(return_value=None)

    # Mock successful API response
    with patch("linkly.services.shortner.httpx.AsyncClient") as MockAsyncClient:
        mock_client_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"city": "Paris", "country": "France"}
        mock_client_instance.get = AsyncMock(return_value=mock_response)

        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_context_manager.__aexit__ = AsyncMock(return_value=None)

        MockAsyncClient.return_value = mock_context_manager

        from linkly.services.shortner import url_analytics

        await url_analytics("http://localhost:8000/abc123", request, mock_db_cm)

    # Verify user_agent defaults to "unknown"
    mock_db_cm.url_analytics.insert_one.assert_called_once()
    insert_args = mock_db_cm.url_analytics.insert_one.call_args[0][0]
    assert insert_args["click_details"][0]["user_agent"] == "unknown"
