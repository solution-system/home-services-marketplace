"""One-time demo data for local use and portfolio screenshots.

The passwords below are demo defaults. Override them with
SEED_ADMIN_PASSWORD and SEED_PROVIDER_PASSWORD before sharing a live demo.
"""

import os
from datetime import date, timedelta

from .extensions import db
from .models import Note, ServiceRequest, StatusEvent, User, utc_now
from .references import new_reference


DEMO_ADMIN = ("admin", "Amina Admin")
DEMO_PROVIDERS = (
    ("bilal", "Bilal Plumbing"),
    ("chloe", "Chloe Cleaning"),
)


def _next_reference():
    reference = new_reference()
    while ServiceRequest.query.filter_by(reference=reference).first():
        reference = new_reference()
    return reference


def _add_event(service_request, previous_status, new_status, message, created_at):
    service_request.events.append(
        StatusEvent(
            previous_status=previous_status,
            new_status=new_status,
            public_message=message,
            created_at=created_at,
        )
    )


def seed_demo_data(reset=False):
    admin_password = os.environ.get("SEED_ADMIN_PASSWORD", "admin1234")
    provider_password = os.environ.get("SEED_PROVIDER_PASSWORD", "provider1234")

    if reset:
        StatusEvent.query.delete()
        ServiceRequest.query.delete()
        User.query.delete()
        db.session.commit()
    elif User.query.filter_by(username=DEMO_ADMIN[0]).first() is not None:
        return "Demo data already exists. Run with --reset to rebuild it."

    admin = User(
        username=DEMO_ADMIN[0],
        display_name=DEMO_ADMIN[1],
        role="admin",
    )
    admin.set_password(admin_password)

    providers = []
    for username, display_name in DEMO_PROVIDERS:
        user = User(username=username, display_name=display_name, role="provider")
        user.set_password(provider_password)
        providers.append(user)

    db.session.add(admin)
    db.session.add_all(providers)
    db.session.flush()

    now = utc_now()
    samples = [
        {
            "hours_ago": 2,
            "name": "Nadia Rahman",
            "email": "nadia@example.com",
            "phone": "03001234567",
            "category": "plumbing",
            "area": "Gulberg",
            "description": "Kitchen sink is leaking under the cabinet and needs a check.",
            "status": "New",
            "provider": None,
            "days_ahead": 2,
            "notes": [
                (
                    admin,
                    "Customer asked for a call before the visit. Best reached after 5pm.",
                    False,
                    1,
                ),
            ],
        },
        {
            "hours_ago": 8,
            "name": "Omar Siddiqui",
            "email": "omar@example.com",
            "phone": "03007654321",
            "category": "electrical",
            "area": "Model Town",
            "description": "Two hallway lights stopped working after a power cut.",
            "status": "Assigned",
            "provider": providers[0],
            "days_ahead": 1,
            "notes": [
                (
                    admin,
                    "Building access is from the side gate. Ask for the caretaker.",
                    False,
                    2,
                ),
            ],
        },
        {
            "hours_ago": 26,
            "name": "Hira Malik",
            "email": "hira@example.com",
            "phone": "03211234000",
            "category": "cleaning",
            "area": "DHA Phase 5",
            "description": "Deep clean for a three-bedroom house before guests arrive.",
            "status": "In Progress",
            "provider": providers[1],
            "days_ahead": 0,
            "notes": [
                (
                    providers[1],
                    "Heavy grease behind the oven. Bringing a second cleaning kit tomorrow.",
                    False,
                    4,
                ),
            ],
        },
        {
            "hours_ago": 50,
            "name": "Faisal Ahmed",
            "email": "faisal@example.com",
            "phone": "03335550123",
            "category": "plumbing",
            "area": "Johar Town",
            "description": "Replace the bathroom tap and check water pressure.",
            "status": "Completed",
            "provider": providers[0],
            "days_ahead": -1,
            "notes": [
                (
                    providers[0],
                    "Replaced the tap washer and tested pressure. Customer confirmed no leak.",
                    True,
                    6,
                ),
            ],
        },
        {
            "hours_ago": 72,
            "name": "Sana Iqbal",
            "email": "sana@example.com",
            "phone": "03457778888",
            "category": "electrical",
            "area": "Cantt",
            "description": "Install two ceiling fans in the living room.",
            "status": "Cancelled",
            "provider": None,
            "days_ahead": 3,
        },
        {
            "hours_ago": 96,
            "name": "Zainab Ali",
            "email": "zainab@example.com",
            "phone": "03119990000",
            "category": "cleaning",
            "area": "Garden Town",
            "description": "Weekly cleaning for apartment common areas and stairs.",
            "status": "Completed",
            "provider": providers[1],
            "days_ahead": -2,
        },
    ]

    for sample in samples:
        created_at = now - timedelta(hours=sample["hours_ago"])
        service_request = ServiceRequest(
            reference=_next_reference(),
            customer_name=sample["name"],
            customer_email=sample["email"],
            customer_phone=sample["phone"],
            category=sample["category"],
            requested_date=date.today() + timedelta(days=sample["days_ahead"]),
            service_area=sample["area"],
            description=sample["description"],
            status=sample["status"],
            created_at=created_at,
            updated_at=created_at,
        )

        _add_event(
            service_request,
            None,
            "New",
            "Your request has been received. Our team will review it.",
            created_at,
        )

        if sample["provider"] is not None:
            assigned_at = created_at + timedelta(hours=1)
            service_request.assigned_provider = sample["provider"]
            service_request.assigned_at = assigned_at
            _add_event(
                service_request,
                "New",
                "Assigned",
                f"Your request has been assigned to {sample['provider'].display_name}.",
                assigned_at,
            )

        if sample["status"] in ("In Progress", "Completed"):
            started_at = created_at + timedelta(hours=3)
            service_request.started_at = started_at
            _add_event(
                service_request,
                "Assigned",
                "In Progress",
                "The service provider has started work on your request.",
                started_at,
            )

        if sample["status"] == "Completed":
            completed_at = created_at + timedelta(hours=5)
            service_request.completed_at = completed_at
            _add_event(
                service_request,
                "In Progress",
                "Completed",
                "The work is complete. Thank you for choosing Goodhand.",
                completed_at,
            )

        if sample["status"] == "Cancelled":
            _add_event(
                service_request,
                "New",
                "Cancelled",
                "This request was cancelled by our team.",
                created_at + timedelta(hours=2),
            )

        for author, body, is_customer_visible, hours_after in sample.get("notes", []):
            service_request.notes.append(
                Note(
                    author=author,
                    body=body,
                    is_customer_visible=is_customer_visible,
                    created_at=created_at + timedelta(hours=hours_after),
                )
            )

        db.session.add(service_request)

    db.session.commit()

    if os.environ.get("RENDER", "").lower() == "true":
        # Render stores deploy logs. Never print passwords there.
        return "Demo data created. Demo credentials are documented in the README."

    return (
        "Demo data created.\n"
        f"  Admin:    {DEMO_ADMIN[0]} / {admin_password}\n"
        f"  Provider: {DEMO_PROVIDERS[0][0]} / {provider_password}\n"
        f"  Provider: {DEMO_PROVIDERS[1][0]} / {provider_password}\n"
        "Change these passwords before any public deployment."
    )
