from app.models import Note

from helpers import login


def test_admin_adds_a_note_with_author_and_timestamp(client, admin, make_request):
    service_request = make_request("NOTE0001")

    login(client, "admin", "adminpass")
    response = client.post(
        f"/requests/{service_request.id}/notes",
        data={"body": "Call the customer before visiting.", "is_customer_visible": "y"},
    )

    assert response.status_code == 302

    note = Note.query.filter_by(request_id=service_request.id).one()
    assert note.body == "Call the customer before visiting."
    assert note.author.username == "admin"
    assert note.is_customer_visible is True
    assert note.created_at is not None


def test_note_appears_on_request_detail_page(client, admin, make_request):
    service_request = make_request("NOTE0002")

    login(client, "admin", "adminpass")
    client.post(
        f"/requests/{service_request.id}/notes",
        data={"body": "Bring a spare washer."},
    )
    response = client.get(f"/admin/requests/{service_request.id}")

    assert b"Bring a spare washer." in response.data
    assert b"Admin User" in response.data


def test_provider_adds_a_note_to_an_assigned_job(client, provider, make_request):
    service_request = make_request(
        "NOTE0003",
        status="Assigned",
        assigned_provider_id=provider.id,
    )

    login(client, "provider", "providerpass")
    response = client.post(
        f"/requests/{service_request.id}/notes",
        data={"body": "Customer confirmed access after 2pm."},
    )

    assert response.status_code == 302

    note = Note.query.filter_by(request_id=service_request.id).one()
    assert note.body == "Customer confirmed access after 2pm."
    assert note.author.username == "provider"


def test_provider_cannot_note_another_providers_job(
    client, provider, other_provider, make_request
):
    service_request = make_request(
        "NOTE0004",
        status="Assigned",
        assigned_provider_id=other_provider.id,
    )

    login(client, "provider", "providerpass")
    response = client.post(
        f"/requests/{service_request.id}/notes",
        data={"body": "Trying to add a note."},
    )

    assert response.status_code == 403
    assert b"You do not have permission to add a note to this request." in response.data
    assert Note.query.count() == 0


def test_empty_note_is_rejected(client, admin, make_request):
    service_request = make_request("NOTE0005")

    login(client, "admin", "adminpass")
    response = client.post(
        f"/requests/{service_request.id}/notes",
        data={"body": ""},
        follow_redirects=True,
    )

    assert b"Note cannot be empty." in response.data
    assert Note.query.count() == 0


def test_whitespace_only_note_is_rejected(client, admin, make_request):
    service_request = make_request("NOTE0006")

    login(client, "admin", "adminpass")
    response = client.post(
        f"/requests/{service_request.id}/notes",
        data={"body": "     "},
        follow_redirects=True,
    )

    assert b"Note cannot be empty." in response.data
    assert Note.query.count() == 0


def test_over_limit_note_is_rejected(client, admin, make_request):
    service_request = make_request("NOTE0007")

    login(client, "admin", "adminpass")
    response = client.post(
        f"/requests/{service_request.id}/notes",
        data={"body": "x" * 501},
        follow_redirects=True,
    )

    assert b"Note must be 500 characters or fewer." in response.data
    assert Note.query.count() == 0


def test_note_body_is_trimmed_before_saving(client, admin, make_request):
    service_request = make_request("NOTE0008")

    login(client, "admin", "adminpass")
    client.post(
        f"/requests/{service_request.id}/notes",
        data={"body": "   Trimmed note   "},
    )

    note = Note.query.filter_by(request_id=service_request.id).one()
    assert note.body == "Trimmed note"


def test_customer_visible_defaults_to_false(client, admin, make_request):
    service_request = make_request("NOTE0009")

    login(client, "admin", "adminpass")
    client.post(
        f"/requests/{service_request.id}/notes",
        data={"body": "Internal only."},
    )

    note = Note.query.filter_by(request_id=service_request.id).one()
    assert note.is_customer_visible is False


def test_anonymous_user_cannot_add_a_note(client, make_request):
    service_request = make_request("NOTE0010")

    response = client.post(
        f"/requests/{service_request.id}/notes",
        data={"body": "Anonymous note."},
    )

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]
    assert Note.query.count() == 0


def test_note_on_missing_request_returns_404(client, admin):
    login(client, "admin", "adminpass")
    response = client.post(
        "/requests/99999/notes",
        data={"body": "Note for a missing request."},
    )

    assert response.status_code == 404
    assert b"Request not found." in response.data
