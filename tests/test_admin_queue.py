from datetime import datetime, timedelta, timezone

from helpers import login


def _login_admin(client, admin):
    response = login(client, "admin", "adminpass")
    assert response.status_code == 302


def test_queue_lists_requests_newest_first(client, admin, make_request):
    now = datetime.now(timezone.utc)
    make_request("OLD00001", customer_name="Older Customer", created_at=now - timedelta(hours=2))
    make_request("NEW00001", customer_name="Newer Customer", created_at=now - timedelta(hours=1))

    _login_admin(client, admin)
    response = client.get("/admin/queue")

    assert response.status_code == 200
    assert response.data.index(b"Newer Customer") < response.data.index(b"Older Customer")
    assert b"OLD00001" in response.data
    assert b"NEW00001" in response.data


def test_queue_filters_by_status(client, admin, make_request):
    make_request("NEW00002", customer_name="New Job", status="New")
    make_request("CMP00002", customer_name="Done Job", status="Completed")

    _login_admin(client, admin)
    response = client.get("/admin/queue?status=Completed")

    assert b"Done Job" in response.data
    assert b"New Job" not in response.data


def test_queue_filters_by_service_type(client, admin, make_request):
    make_request("PLB00003", customer_name="Plumbing Job", category="plumbing")
    make_request("ELE00003", customer_name="Electrical Job", category="electrical")

    _login_admin(client, admin)
    response = client.get("/admin/queue?category=electrical")

    assert b"Electrical Job" in response.data
    assert b"Plumbing Job" not in response.data


def test_queue_filters_by_status_and_service_type(client, admin, make_request):
    make_request("PLB00004", customer_name="New Plumbing", category="plumbing", status="New")
    make_request("PLB00005", customer_name="Done Plumbing", category="plumbing", status="Completed")
    make_request("ELE00004", customer_name="New Electrical", category="electrical", status="New")

    _login_admin(client, admin)
    response = client.get("/admin/queue?status=New&category=plumbing")

    assert b"New Plumbing" in response.data
    assert b"Done Plumbing" not in response.data
    assert b"New Electrical" not in response.data


def test_queue_searches_by_reference(client, admin, make_request):
    make_request("ABC12345", customer_name="Reference Match")
    make_request("XYZ98765", customer_name="Other Match")

    _login_admin(client, admin)
    response = client.get("/admin/queue?q=ABC123")

    assert b"Reference Match" in response.data
    assert b"Other Match" not in response.data


def test_queue_searches_customer_name_case_insensitively(client, admin, make_request):
    make_request("NAM00001", customer_name="Samira Khan")
    make_request("NAM00002", customer_name="Omar Siddiqui")

    _login_admin(client, admin)
    response = client.get("/admin/queue?q=samira")

    assert b"Samira Khan" in response.data
    assert b"Omar Siddiqui" not in response.data


def test_queue_shows_empty_state_when_no_requests_exist(client, admin):
    _login_admin(client, admin)
    response = client.get("/admin/queue")

    assert response.status_code == 200
    assert b"No requests yet." in response.data


def test_queue_shows_filter_empty_state_when_nothing_matches(client, admin, make_request):
    make_request("FLT00001", status="New", category="plumbing")

    _login_admin(client, admin)
    response = client.get("/admin/queue?status=Completed")

    assert b"No requests match these filters." in response.data


def test_queue_rejects_unknown_filter_values_without_error(client, admin, make_request):
    make_request("SAF00001", customer_name="Safe Request")

    _login_admin(client, admin)
    response = client.get("/admin/queue?status=Bogus&category=Bogus")

    assert response.status_code == 200
    assert b"Safe Request" in response.data
