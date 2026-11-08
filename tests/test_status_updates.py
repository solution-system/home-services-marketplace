from datetime import datetime, timezone

from app.extensions import db
from app.models import ServiceRequest, StatusEvent

from helpers import login


def test_provider_starts_an_assigned_job(client, provider, make_request):
    service_request = make_request(
        "UPD00001",
        status="Assigned",
        assigned_provider_id=provider.id,
    )

    login(client, "provider", "providerpass")
    response = client.post(
        f"/provider/jobs/{service_request.id}/status",
        data={"new_status": "In Progress"},
    )

    assert response.status_code == 302

    updated = db.session.get(ServiceRequest, service_request.id)
    assert updated.status == "In Progress"
    assert updated.started_at is not None
    assert updated.completed_at is None

    event = StatusEvent.query.filter_by(request_id=service_request.id).one()
    assert event.previous_status == "Assigned"
    assert event.new_status == "In Progress"


def test_provider_completes_an_in_progress_job(client, provider, make_request):
    service_request = make_request(
        "UPD00002",
        status="In Progress",
        assigned_provider_id=provider.id,
    )

    login(client, "provider", "providerpass")
    response = client.post(
        f"/provider/jobs/{service_request.id}/status",
        data={"new_status": "Completed"},
    )

    assert response.status_code == 302

    updated = db.session.get(ServiceRequest, service_request.id)
    assert updated.status == "Completed"
    assert updated.completed_at is not None

    event = StatusEvent.query.filter_by(request_id=service_request.id).one()
    assert event.previous_status == "In Progress"
    assert event.new_status == "Completed"


def test_provider_cannot_skip_a_step(client, provider, make_request):
    service_request = make_request(
        "UPD00003",
        status="Assigned",
        assigned_provider_id=provider.id,
    )

    login(client, "provider", "providerpass")
    response = client.post(
        f"/provider/jobs/{service_request.id}/status",
        data={"new_status": "Completed"},
        follow_redirects=True,
    )

    assert b"This status change is not allowed." in response.data

    updated = db.session.get(ServiceRequest, service_request.id)
    assert updated.status == "Assigned"
    assert updated.started_at is None
    assert updated.completed_at is None


def test_provider_cannot_move_a_job_backwards(client, provider, make_request):
    service_request = make_request(
        "UPD00004",
        status="In Progress",
        assigned_provider_id=provider.id,
    )

    login(client, "provider", "providerpass")
    response = client.post(
        f"/provider/jobs/{service_request.id}/status",
        data={"new_status": "Assigned"},
        follow_redirects=True,
    )

    assert b"This status change is not allowed." in response.data

    updated = db.session.get(ServiceRequest, service_request.id)
    assert updated.status == "In Progress"


def test_completed_job_cannot_change_status(client, provider, make_request):
    completed_at = datetime.now(timezone.utc)
    service_request = make_request(
        "UPD00005",
        status="Completed",
        assigned_provider_id=provider.id,
        completed_at=completed_at,
    )

    login(client, "provider", "providerpass")
    response = client.post(
        f"/provider/jobs/{service_request.id}/status",
        data={"new_status": "In Progress"},
        follow_redirects=True,
    )

    assert b"This job is already completed." in response.data

    updated = db.session.get(ServiceRequest, service_request.id)
    assert updated.status == "Completed"
    assert updated.completed_at is not None


def test_non_assigned_provider_cannot_update_status(
    client, other_provider, provider, make_request
):
    service_request = make_request(
        "UPD00006",
        status="Assigned",
        assigned_provider_id=provider.id,
    )

    login(client, "other", "otherpass")
    response = client.post(
        f"/provider/jobs/{service_request.id}/status",
        data={"new_status": "In Progress"},
    )

    assert response.status_code == 403
    assert b"You are not assigned to this request." in response.data

    updated = db.session.get(ServiceRequest, service_request.id)
    assert updated.status == "Assigned"


def test_admin_cannot_update_job_status(client, admin, provider, make_request):
    service_request = make_request(
        "UPD00007",
        status="Assigned",
        assigned_provider_id=provider.id,
    )

    login(client, "admin", "adminpass")
    response = client.post(
        f"/provider/jobs/{service_request.id}/status",
        data={"new_status": "In Progress"},
    )

    assert response.status_code == 403

    updated = db.session.get(ServiceRequest, service_request.id)
    assert updated.status == "Assigned"


def test_cancelled_job_cannot_be_updated(client, provider, make_request):
    service_request = make_request(
        "UPD00008",
        status="Cancelled",
        assigned_provider_id=provider.id,
    )

    login(client, "provider", "providerpass")
    response = client.post(
        f"/provider/jobs/{service_request.id}/status",
        data={"new_status": "In Progress"},
        follow_redirects=True,
    )

    assert b"This status change is not allowed." in response.data

    updated = db.session.get(ServiceRequest, service_request.id)
    assert updated.status == "Cancelled"


def test_detail_page_shows_start_action_for_assigned_job(client, provider, make_request):
    service_request = make_request(
        "UPD00009",
        status="Assigned",
        assigned_provider_id=provider.id,
    )

    login(client, "provider", "providerpass")
    response = client.get(f"/provider/jobs/{service_request.id}")

    assert b"Start work" in response.data
    assert b'name="new_status"' in response.data
    assert b'value="In Progress"' in response.data


def test_detail_page_shows_complete_action_for_in_progress_job(
    client, provider, make_request
):
    service_request = make_request(
        "UPD00010",
        status="In Progress",
        assigned_provider_id=provider.id,
    )

    login(client, "provider", "providerpass")
    response = client.get(f"/provider/jobs/{service_request.id}")

    assert b"Mark completed" in response.data
    assert b'value="Completed"' in response.data


def test_detail_page_shows_completed_message(client, provider, make_request):
    service_request = make_request(
        "UPD00011",
        status="Completed",
        assigned_provider_id=provider.id,
    )

    login(client, "provider", "providerpass")
    response = client.get(f"/provider/jobs/{service_request.id}")

    assert b"This job is already completed." in response.data
