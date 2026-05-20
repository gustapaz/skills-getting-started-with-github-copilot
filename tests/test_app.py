import copy
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app

client = TestClient(app)
ORIGINAL_ACTIVITIES = copy.deepcopy(activities)


@pytest.fixture(autouse=True)
def restore_activities():
    activities.clear()
    activities.update(copy.deepcopy(ORIGINAL_ACTIVITIES))
    yield
    activities.clear()
    activities.update(copy.deepcopy(ORIGINAL_ACTIVITIES))


def activity_url(activity_name: str) -> str:
    return f"/activities/{quote(activity_name, safe='')}"


def test_root_redirect():
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activities():
    response = client.get("/activities")

    assert response.status_code == 200
    payload = response.json()
    assert "Chess Club" in payload
    assert payload["Chess Club"]["description"] == "Learn strategies and compete in chess tournaments"


def test_signup_for_activity():
    activity_name = "Book Club"
    email = "new_student@example.com"

    response = client.post(f"{activity_url(activity_name)}/signup", params={"email": email})

    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity_name}"}
    assert email in activities[activity_name]["participants"]


def test_signup_unknown_activity_returns_404():
    response = client.post("/activities/Unknown%20Activity/signup", params={"email": "student@example.com"})

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_duplicate_student_returns_400():
    activity_name = "Chess Club"
    existing_email = ORIGINAL_ACTIVITIES[activity_name]["participants"][0]

    response = client.post(f"{activity_url(activity_name)}/signup", params={"email": existing_email})

    assert response.status_code == 400
    assert response.json()["detail"] == "Student is already signed up for this activity"


def test_remove_participant():
    activity_name = "Chess Club"
    email = ORIGINAL_ACTIVITIES[activity_name]["participants"][0]

    response = client.delete(f"{activity_url(activity_name)}/participants", params={"email": email})

    assert response.status_code == 200
    assert response.json() == {"message": f"Removed {email} from {activity_name}"}
    assert email not in activities[activity_name]["participants"]


def test_remove_unknown_activity_returns_404():
    response = client.delete("/activities/Unknown%20Activity/participants", params={"email": "student@example.com"})

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_remove_missing_participant_returns_404():
    activity_name = "Chess Club"
    email = "not_registered@example.com"

    response = client.delete(f"{activity_url(activity_name)}/participants", params={"email": email})

    assert response.status_code == 404
    assert response.json()["detail"] == "Participant not found"
