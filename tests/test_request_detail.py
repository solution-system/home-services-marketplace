from helpers import login


def test_admin_can_view_any_request(client, admin, make_request):
    request = make_request(
        "DET00001",
        customer_name="Detail Customer",
        customer_email="detail@example.com",
        customer_phone="03001112222",
        description="The kitchen tap is dripping constantly.",
    )

    login(client, "admin", "adminpass")
    response = client.get(f"/admin/requests/{request.id}")

    assert response.status_code == 200
    assert b"Detail Customer" in response.data
    assert b"detail@example.com" in response.data
    assert b"The kitchen tap is dripping constantly." in response.data
    assert b"DET00001" in response.data


def test_provider_can_view_their_own_job(client, provider, make_request):
    request = make_request(
        "DET00002",
        customer_name="Assigned Customer",
        assigned_provider_id=provider.id,
        status="Assigned",
    )

    login(client, "provider", "providerpass")
    response = client.get(f"/provider/jobs/{request.id}")

    assert response.status_code == 200
    assert b"Assigned Customer" in response.data
    assert b"DET00002" in response.data


def test_provider_cannot_view_another_providers_job(client, provider, other_provider, make_request):
    request = make_request(
        "DET00003",
        assigned_provider_id=other_provider.id,
        status="Assigned",
    )

    login(client, "provider", "providerpass")
    response = client.get(f"/provider/jobs/{request.id}")

    assert response.status_code == 403
    assert b"You do not have permission to view this request." in response.data


def test_provider_cannot_view_an_unassigned_job(client, provider, make_request):
    request = make_request("DET00004", status="New")

    login(client, "provider", "providerpass")
    response = client.get(f"/provider/jobs/{request.id}")

    assert response.status_code == 403
    assert b"You do not have permission to view this request." in response.data


def test_missing_request_shows_request_not_found(client, admin):
    login(client, "admin", "adminpass")
    response = client.get("/admin/requests/99999")

    assert response.status_code == 404
    assert b"Request not found." in response.data


def test_anonymous_user_cannot_view_request_details(client, make_request):
    request = make_request("DET00005")

    response = client.get(f"/admin/requests/{request.id}")

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]
