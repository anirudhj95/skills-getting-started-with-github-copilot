"""
Test suite for the Mergington High School activity API.

These tests follow the Arrange-Act-Assert pattern and use a real
FastAPI test client to verify endpoint behavior end to end.
"""

from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset the in-memory activity data before each test."""
    original = deepcopy(activities)
    activities.clear()
    activities.update(deepcopy(original))

    yield

    activities.clear()
    activities.update(deepcopy(original))


client = TestClient(app)


class TestRootEndpoint:
    def test_root_redirects_to_static_index(self):
        # Arrange
        expected_redirect = "/static/index.html"

        # Act
        response = client.get("/", follow_redirects=False)

        # Assert
        assert response.status_code == 307
        assert response.headers["location"] == expected_redirect


class TestGetActivitiesEndpoint:
    def test_get_activities_returns_all_activities(self):
        # Arrange
        expected_activity_count = 9

        # Act
        response = client.get("/activities")
        data = response.json()

        # Assert
        assert response.status_code == 200
        assert len(data) == expected_activity_count
        assert "Chess Club" in data
        assert "Programming Class" in data

    def test_get_activities_returns_expected_fields(self):
        # Arrange
        required_fields = {"description", "schedule", "max_participants", "participants"}

        # Act
        response = client.get("/activities")
        data = response.json()

        # Assert
        assert response.status_code == 200
        for activity in data.values():
            assert set(activity.keys()) == required_fields
            assert isinstance(activity["participants"], list)


class TestSignupEndpoint:
    def test_signup_adds_new_student_to_activity(self):
        # Arrange
        activity_name = "Chess Club"
        email = "newstudent@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email},
        )
        data = response.json()

        # Assert
        assert response.status_code == 200
        assert data["message"] == f"Signed up {email} for {activity_name}"
        assert email in activities[activity_name]["participants"]

    def test_signup_returns_404_for_unknown_activity(self):
        # Arrange
        activity_name = "Unknown Club"
        email = "student@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email},
        )
        data = response.json()

        # Assert
        assert response.status_code == 404
        assert data["detail"] == "Activity not found"

    def test_signup_returns_400_for_existing_participant(self):
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email},
        )
        data = response.json()

        # Assert
        assert response.status_code == 400
        assert data["detail"] == "Student is already signed up for this activity"


class TestUnregisterEndpoint:
    def test_unregister_removes_student_from_activity(self):
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": email},
        )
        data = response.json()

        # Assert
        assert response.status_code == 200
        assert data["message"] == f"Removed {email} from {activity_name}"
        assert email not in activities[activity_name]["participants"]

    def test_unregister_returns_404_for_unknown_activity(self):
        # Arrange
        activity_name = "Unknown Club"
        email = "student@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": email},
        )
        data = response.json()

        # Assert
        assert response.status_code == 404
        assert data["detail"] == "Activity not found"

    def test_unregister_returns_400_when_student_not_registered(self):
        # Arrange
        activity_name = "Chess Club"
        email = "notregistered@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": email},
        )
        data = response.json()

        # Assert
        assert response.status_code == 400
        assert data["detail"] == "Student is not signed up for this activity"


class TestSignupAndUnregisterFlow:
    def test_signup_then_unregister_keeps_state_consistent(self):
        # Arrange
        activity_name = "Science Club"
        email = "student@mergington.edu"

        # Act - sign up
        signup_response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email},
        )

        # Act - unregister
        unregister_response = client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": email},
        )

        # Assert
        assert signup_response.status_code == 200
        assert unregister_response.status_code == 200
        assert email not in activities[activity_name]["participants"]
