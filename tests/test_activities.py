"""Tests for the activities API endpoints."""
import pytest


class TestGetActivities:
    """Test the GET /activities endpoint."""

    def test_get_activities_returns_all_activities(self, client):
        """Test that all activities are returned."""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 9
        assert "Soccer Team" in data
        assert "Basketball Club" in data

    def test_get_activities_has_required_fields(self, client):
        """Test that each activity has required fields."""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)

    def test_get_activities_shows_initial_participants(self, client):
        """Test that initial participants are shown."""
        response = client.get("/activities")
        data = response.json()
        
        assert "alex@mergington.edu" in data["Soccer Team"]["participants"]
        assert "sarah@mergington.edu" in data["Soccer Team"]["participants"]
        assert len(data["Soccer Team"]["participants"]) == 2


class TestSignupForActivity:
    """Test the POST /activities/{activity_name}/signup endpoint."""

    def test_signup_new_participant_success(self, client):
        """Test successful signup for a new participant."""
        response = client.post(
            "/activities/Soccer Team/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "Signed up" in data["message"]
        assert "newstudent@mergington.edu" in data["message"]

    def test_signup_adds_participant_to_list(self, client):
        """Test that signup adds participant to the activity."""
        new_email = "newstudent@mergington.edu"
        
        # Signup
        response = client.post(
            f"/activities/Soccer Team/signup?email={new_email}"
        )
        assert response.status_code == 200
        
        # Verify participant was added
        response = client.get("/activities")
        data = response.json()
        assert new_email in data["Soccer Team"]["participants"]

    def test_signup_duplicate_participant_fails(self, client):
        """Test that signup fails for already registered participant."""
        response = client.post(
            "/activities/Soccer Team/signup?email=alex@mergington.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"].lower()

    def test_signup_nonexistent_activity_fails(self, client):
        """Test that signup fails for nonexistent activity."""
        response = client.post(
            "/activities/Nonexistent Activity/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()


class TestUnregisterFromActivity:
    """Test the DELETE /activities/{activity_name}/unregister endpoint."""

    def test_unregister_existing_participant_success(self, client):
        """Test successful unregistration."""
        response = client.delete(
            "/activities/Soccer Team/unregister?email=alex@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"]
        assert "alex@mergington.edu" in data["message"]

    def test_unregister_removes_participant_from_list(self, client):
        """Test that unregister removes participant from the activity."""
        email = "alex@mergington.edu"
        
        # Unregister
        response = client.delete(
            f"/activities/Soccer Team/unregister?email={email}"
        )
        assert response.status_code == 200
        
        # Verify participant was removed
        response = client.get("/activities")
        data = response.json()
        assert email not in data["Soccer Team"]["participants"]

    def test_unregister_nonexistent_participant_fails(self, client):
        """Test that unregister fails for non-registered participant."""
        response = client.delete(
            "/activities/Soccer Team/unregister?email=notregistered@mergington.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert "not registered" in data["detail"].lower()

    def test_unregister_nonexistent_activity_fails(self, client):
        """Test that unregister fails for nonexistent activity."""
        response = client.delete(
            "/activities/Nonexistent Activity/unregister?email=student@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()


class TestActivityIntegration:
    """Integration tests for activity workflows."""

    def test_signup_and_unregister_workflow(self, client):
        """Test complete signup and unregister workflow."""
        email = "workflow@mergington.edu"
        activity = "Basketball Club"
        
        # Verify participant not in activity initially
        response = client.get("/activities")
        assert email not in response.json()[activity]["participants"]
        
        # Sign up
        response = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        assert response.status_code == 200
        
        # Verify participant added
        response = client.get("/activities")
        assert email in response.json()[activity]["participants"]
        
        # Unregister
        response = client.delete(
            f"/activities/{activity}/unregister?email={email}"
        )
        assert response.status_code == 200
        
        # Verify participant removed
        response = client.get("/activities")
        assert email not in response.json()[activity]["participants"]

    def test_participant_count_accuracy(self, client):
        """Test that participant count is accurate after operations."""
        email = "count@mergington.edu"
        activity = "Art Studio"
        
        # Get initial count
        response = client.get("/activities")
        initial_count = len(response.json()[activity]["participants"])
        
        # Sign up
        client.post(f"/activities/{activity}/signup?email={email}")
        
        # Check count increased
        response = client.get("/activities")
        assert len(response.json()[activity]["participants"]) == initial_count + 1
        
        # Unregister
        client.delete(f"/activities/{activity}/unregister?email={email}")
        
        # Check count back to initial
        response = client.get("/activities")
        assert len(response.json()[activity]["participants"]) == initial_count
