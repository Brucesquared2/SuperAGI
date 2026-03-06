from unittest.mock import patch, MagicMock
import pytest
from fastapi.testclient import TestClient

from main import app
from superagi.helper.auth import get_user_organisation
from superagi.models.organisation import Organisation
from superagi.models.resource import Resource
from superagi.models.agent import Agent

client = TestClient(app)


@pytest.fixture
def mock_organisation():
    return Organisation(id=1, name="Test Org")


@pytest.fixture
def mock_resource():
    resource = Resource()
    resource.id = 1
    resource.name = "test_file.pdf"
    resource.path = "/tmp/test_file.pdf"
    resource.storage_type = "FILE"
    resource.agent_id = 1
    return resource


@pytest.fixture
def mock_agent():
    agent = MagicMock(spec=Agent)
    agent.id = 1
    agent.project_id = 1
    return agent


@patch('superagi.controllers.resources.db')
def test_download_file_resource_not_found(mock_db, mock_organisation):
    app.dependency_overrides[get_user_organisation] = lambda: mock_organisation
    try:
        mock_db.session.query.return_value.filter.return_value.first.return_value = None

        response = client.get("/resources/get/999")

        assert response.status_code == 400
        assert response.json()["detail"] == "Resource Not found!"
    finally:
        app.dependency_overrides.pop(get_user_organisation, None)


@patch('superagi.controllers.resources.db')
def test_download_file_agent_not_found(mock_db, mock_resource, mock_organisation):
    app.dependency_overrides[get_user_organisation] = lambda: mock_organisation
    try:
        mock_db.session.query.return_value.filter.return_value.first.side_effect = [
            mock_resource,
            None,
        ]

        response = client.get("/resources/get/1")

        assert response.status_code == 400
        assert response.json()["detail"] == "Associated agent not found!"
    finally:
        app.dependency_overrides.pop(get_user_organisation, None)


@patch('superagi.controllers.resources.db')
def test_download_file_forbidden_different_organisation(mock_db, mock_resource, mock_agent, mock_organisation):
    app.dependency_overrides[get_user_organisation] = lambda: mock_organisation
    try:
        mock_db.session.query.return_value.filter.return_value.first.side_effect = [
            mock_resource,
            mock_agent,
        ]
        # Agent belongs to a different organisation
        different_org = Organisation(id=2, name="Other Org")
        mock_agent.get_agent_organisation.return_value = different_org

        response = client.get("/resources/get/1")

        assert response.status_code == 403
        assert response.json()["detail"] == "You don't have permission to access this resource"
    finally:
        app.dependency_overrides.pop(get_user_organisation, None)


@patch('superagi.controllers.resources.db')
def test_download_file_file_not_found_on_disk(mock_db, mock_resource, mock_agent, mock_organisation):
    app.dependency_overrides[get_user_organisation] = lambda: mock_organisation
    try:
        mock_db.session.query.return_value.filter.return_value.first.side_effect = [
            mock_resource,
            mock_agent,
        ]
        mock_agent.get_agent_organisation.return_value = mock_organisation

        # Path points to a file that does not exist
        mock_resource.path = "/nonexistent/path/file.pdf"

        response = client.get("/resources/get/1")

        assert response.status_code == 404
        assert response.json()["detail"] == "File not found"
    finally:
        app.dependency_overrides.pop(get_user_organisation, None)


@patch('superagi.controllers.resources.db')
def test_download_file_success(mock_db, mock_resource, mock_agent, mock_organisation, tmp_path):
    app.dependency_overrides[get_user_organisation] = lambda: mock_organisation
    try:
        mock_db.session.query.return_value.filter.return_value.first.side_effect = [
            mock_resource,
            mock_agent,
        ]
        mock_agent.get_agent_organisation.return_value = mock_organisation

        # Create a real temporary file
        test_file = tmp_path / "test_file.pdf"
        test_file.write_bytes(b"PDF content")
        mock_resource.path = str(test_file)
        mock_resource.name = "test_file.pdf"

        response = client.get("/resources/get/1")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/octet-stream"
        assert "test_file.pdf" in response.headers["content-disposition"]
    finally:
        app.dependency_overrides.pop(get_user_organisation, None)
