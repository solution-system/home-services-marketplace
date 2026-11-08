from flask import Blueprint, render_template, request

from .extensions import db
from .forms import LookupForm, ServiceRequestForm
from .models import ServiceRequest, StatusEvent
from .references import new_reference


public = Blueprint("public", __name__)


@public.get("/")
def home():
    return render_template("home.html", form=ServiceRequestForm())


@public.get("/healthz")
def healthz():
    """Lightweight health check for Render.

    This intentionally does not query the database: health checks that touch
    Neon would keep the free database awake and burn through its compute hours.
    """
    return {"status": "ok"}


@public.route("/requests", methods=["GET", "POST"])
def create_request():
    form = ServiceRequestForm()
    if form.validate_on_submit():
        reference = new_reference()
        while db.session.query(ServiceRequest.id).filter_by(reference=reference).first():
            reference = new_reference()

        service_request = ServiceRequest(
            reference=reference,
            customer_name=form.customer_name.data.strip(),
            customer_email=form.customer_email.data.strip().lower(),
            customer_phone=form.customer_phone.data.strip(),
            category=form.category.data,
            requested_date=form.requested_date.data,
            service_area=form.service_area.data.strip(),
            description=form.description.data.strip(),
            status="New",
        )
        service_request.events.append(
            StatusEvent(
                previous_status=None,
                new_status="New",
                public_message="Your request has been received. Our team will review it.",
            )
        )
        db.session.add(service_request)
        db.session.commit()
        return render_template("confirmation.html", service_request=service_request)

    return render_template("home.html", form=form), 400


@public.route("/lookup", methods=["GET", "POST"])
def lookup():
    form = LookupForm()
    service_request = None
    not_found = False
    if form.validate_on_submit():
        reference = form.reference.data.strip().upper()
        email = form.email.data.strip().lower()
        service_request = ServiceRequest.query.filter_by(reference=reference, customer_email=email).first()
        not_found = service_request is None
    elif request.method == "POST":
        not_found = True

    return render_template("lookup.html", form=form, service_request=service_request, not_found=not_found)
