from datetime import datetime, timedelta, timezone

from helpers import login


def test_provider_sees_only_their_own_jobs(client, provider, other_provider, make_request):
    make_request("OWN00001", customer_name="My Customer", assigned_provider_id=provider.id)
    make_request("OTH00001", customer_name="Someone Else", assigned_provider_id=other_provider.id)
    make_request("NEW00009", customer_name="Unassigned Job")

    login(client, "provider", "providerpass")
    response = client.get("/provider/jobs")

    assert response.status_code == 200
    assert b"My Customer" in response.data
    assert b"Someone Else" not in response.data
    assert b"Unassigned Job" not in response.data


def test_provider_jobs_are_newest_first(client, provider, make_request):
    now = datetime.now(timezone.utc)
    make_request(
        "JOB00001",
        customer_name="Older Job",
        assigned_provider_id=provider.id,
        created_at=now - timedelta(days=2),
    )
    make_request(
        "JOB00002",
        customer_name="Newer Job",
        assigned_provider_id=provider.id,
        created_at=now - timedelta(days=1),
    )

    login(client, "provider", "providerpass")
    response = client.get("/provider/jobs")

    assert response.data.index(b"Newer Job") < response.data.index(b"Older Job")


def test_provider_can_filter_jobs_by_status(client, provider, make_request):
    make_request(
        "JOB00003",
        customer_name="Assigned Job",
        status="Assigned",
        assigned_provider_id=provider.id,
    )
    make_request(
        "JOB00004",
        customer_name="Completed Job",
        status="Completed",
        assigned_provider_id=provider.id,
    )

    login(client, "provider", "providerpass")
    response = client.get("/provider/jobs?status=Completed")

    assert b"Completed Job" in response.data
    assert b"Assigned Job" not in response.data


def test_provider_sees_empty_state_with_no_jobs(client, provider):
    login(client, "provider", "providerpass")
    response = client.get("/provider/jobs")

    assert response.status_code == 200
    assert b"No jobs assigned to you yet." in response.data
