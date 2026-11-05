from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


@pytest.fixture
def client():
	original_activities = deepcopy(activities)
	try:
		with TestClient(app) as test_client:
			yield test_client
	finally:
		activities.clear()
		activities.update(original_activities)


def test_root_redirects_to_frontend(client):
	# Arrange
	expected_location = "/static/index.html"

	# Act
	response = client.get("/", follow_redirects=False)

	# Assert
	assert response.status_code == 307
	assert response.headers["location"] == expected_location


def test_get_activities_returns_seeded_activity_data(client):
	# Arrange
	expected_chess_activity = {
		"description": "Learn strategies and compete in chess tournaments",
		"schedule": "Fridays, 3:30 PM - 5:00 PM",
		"max_participants": 12,
		"participants": ["michael@mergington.edu", "daniel@mergington.edu"],
	}

	# Act
	response = client.get("/activities")

	# Assert
	assert response.status_code == 200
	assert response.json()["Chess Club"] == expected_chess_activity


def test_signup_adds_participant(client):
	# Arrange
	email = "new-student@example.com"
	activity_name = "Basketball Team"

	# Act
	response = client.post(
		"/activities/Basketball%20Team/signup", params={"email": email}
	)

	# Assert
	assert response.status_code == 200
	assert response.json() == {
		"message": f"Signed up {email} for {activity_name}"
	}
	assert email in activities[activity_name]["participants"]


def test_signup_rejects_duplicate_participant_without_changing_state(client):
	# Arrange
	activity_name = "Chess Club"
	email = "michael@mergington.edu"
	original_participants = activities[activity_name]["participants"][:]

	# Act
	response = client.post(
		"/activities/Chess%20Club/signup", params={"email": email}
	)

	# Assert
	assert response.status_code == 400
	assert response.json() == {
		"detail": "Student already signed up for this activity"
	}
	assert activities[activity_name]["participants"] == original_participants


def test_signup_returns_not_found_for_unknown_activity(client):
	# Arrange
	email = "new-student@example.com"

	# Act
	response = client.post(
		"/activities/Unknown%20Activity/signup", params={"email": email}
	)

	# Assert
	assert response.status_code == 404
	assert response.json() == {"detail": "Activity not found"}


def test_unregister_removes_participant_and_duplicate_legacy_entries(client):
	# Arrange
	activity_name = "Basketball Team"
	email = "legacy-student@example.com"
	activities[activity_name]["participants"].extend([email, email])

	# Act
	response = client.delete(
		"/activities/Basketball%20Team/signup", params={"email": email}
	)

	# Assert
	assert response.status_code == 200
	assert response.json() == {
		"message": f"Unregistered {email} from {activity_name}"
	}
	assert email not in activities[activity_name]["participants"]


def test_unregister_returns_not_found_for_unregistered_participant(client):
	# Arrange
	email = "not-signed-up@example.com"

	# Act
	response = client.delete(
		"/activities/Basketball%20Team/signup", params={"email": email}
	)

	# Assert
	assert response.status_code == 404
	assert response.json() == {
		"detail": "Student is not signed up for this activity"
	}


def test_unregister_returns_not_found_for_unknown_activity(client):
	# Arrange
	email = "student@example.com"

	# Act
	response = client.delete(
		"/activities/Unknown%20Activity/signup", params={"email": email}
	)

	# Assert
	assert response.status_code == 404
	assert response.json() == {"detail": "Activity not found"}
