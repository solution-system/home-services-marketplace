from app.extensions import db
from app.models import ServiceRequest, StatusEvent

from helpers import login


def test_admin_assigns_provider_to_new_request(client, admin, provider, make_request):
    service_request = make_request("ASG00001", status="New")

    login(client, "admin", "adminpass")
    response = client.post(
        f"/admin/requests/{service_request.id}/assign",
        data={"provider_id": provider.id},
    )

    assert response.status_code == 302

    updated = db.session.get(ServiceRequest, service_request.id)
    assert updated.status == "Assigned"
    assert updated.assigned_provider_id == provider.id
    assert updated.assigned_at is not None

    events = StatusEvent.query.filter_by(request_id=service_request.id).all()
    assert len(events) == 1
    assert events[0].previous_status == "New"
    assert events[0].new_status == "Assigned"
    assert provider.display_name in events[0].public_message


def test_admin_reassigns_provider_before_work_starts(
    client, admin, provider, other_provider, make_request
):
    service_request = make_request(
        "ASG00002",
        status="Assigned",
        assigned_provider_id=other_provider.id,
    )

    login(client, "admin", "adminpass")
    response = client.post(
        f"/admin/requests/{service_request.id}/assign",
        data={"provider_id": provider.id},
    )

    assert response.status_code == 302

    updated = db.session.get(ServiceRequest, service_request.id)
    assert updated.status == "Assigned"
    assert updated.assigned_provider_id == provider.id

    event = StatusEvent.query.filter_by(request_id=service_request.id).one()
    assert event.previous_status == "Assigned"
    assert event.new_status == "Assigned"
    assert "reassigned" in event.public_message


def test_assignment_is_blocked_when_work_has_started(
    client, admin, provider, other_provider, make_request
):
    service_request = make_request(
        "ASG00003",
        status="In Progress",
        assigned_provider_id=provider.id,
    )

    login(client, "admin", "adminpass")
    response = client.post(
        f"/admin/requests/{service_request.id}/assign",
        data={"provider_id": other_provider.id},
        follow_redirects=True,
    )

    assert b"Provider can only be assigned to New or Assigned requests." in response.data

    updated = db.session.get(ServiceRequest, service_request.id)
    assert updated.status == "In Progress"
    assert updated.assigned_provider_id == provider.id


def test_assignment_is_blocked_when_completed(client, admin, provider, make_request):
    service_request = make_request(
        "ASG00004",
        status="Completed",
        assigned_provider_id=provider.id,
    )

    login(client, "admin", "adminpass")
    response = client.post(
        f"/admin/requests/{service_request.id}/assign",
        data={"provider_id": provider.id},
        follow_redirects=True,
    )

    assert b"Provider can only be assigned to New or Assigned requests." in response.data

    updated = db.session.get(ServiceRequest, service_request.id)
    assert updated.status == "Completed"


def test_provider_cannot_assign_a_request(client, provider, other_provider, make_request):
    service_request = make_request("ASG00005", status="New")

    login(client, "provider", "providerpass")
    response = client.post(
        f"/admin/requests/{service_request.id}/assign",
        data={"provider_id": other_provider.id},
    )

    assert response.status_code == 403

    updated = db.session.get(ServiceRequest, service_request.id)
    assert updated.status == "New"
    assert updated.assigned_provider_id is None


def test_invalid_provider_choice_is_rejected(client, admin, provider, make_request):
    service_request = make_request("ASG00006", status="New")

    login(client, "admin", "adminpass")
    response = client.post(
        f"/admin/requests/{service_request.id}/assign",
        data={"provider_id": 99999},
        follow_redirects=True,
    )

    assert b"Select a valid provider." in response.data

    updated = db.session.get(ServiceRequest, service_request.id)
    assert updated.status == "New"
    assert updated.assigned_provider_id is None


def test_assignment_without_registered_providers_shows_message(client, admin, make_request):
    service_request = make_request("ASG00007", status="New")

    login(client, "admin", "adminpass")
    detail = client.get(f"/admin/requests/{service_request.id}")
    assert b"No providers registered." in detail.data

    response = client.post(
        f"/admin/requests/{service_request.id}/assign",
        data={"provider_id": 1},
        follow_redirects=True,
    )

    assert b"No providers registered." in response.data

    updated = db.session.get(ServiceRequest, service_request.id)
    assert updated.status == "New"


def test_detail_page_shows_assignment_form_for_eligible_request(
    client, admin, provider, make_request
):
    service_request = make_request("ASG00008", status="New")

    login(client, "admin", "adminpass")
    response = client.get(f"/admin/requests/{service_request.id}")

    assert b"Save assignment" in response.data
    assert provider.display_name.encode() in response.data


def test_detail_page_hides_assignment_form_after_work_starts(
    client, admin, provider, make_request
):
    service_request = make_request(
        "ASG00009",
        status="In Progress",
        assigned_provider_id=provider.id,
    )

    login(client, "admin", "adminpass")
    response = client.get(f"/admin/requests/{service_request.id}")

    assert b"Save assignment" not in response.data
    assert b"cannot be reassigned" in response.data
