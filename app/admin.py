from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from sqlalchemy import or_

from .auth import roles_required
from .constants import CATEGORY_LABELS, STATUSES
from .extensions import db
from .forms import AssignProviderForm, NoteForm
from .models import ServiceRequest, StatusEvent, User, utc_now


admin = Blueprint("admin", __name__, url_prefix="/admin")

ASSIGNABLE_STATUSES = ("New", "Assigned")


def providers():
    return User.query.filter_by(role="provider").order_by(User.display_name).all()


def assignment_form(provider_list, selected_id=None):
    form = AssignProviderForm()
    form.provider_id.choices = [(provider.id, provider.display_name) for provider in provider_list]
    if selected_id is not None:
        form.provider_id.data = selected_id
    return form


def get_request_or_404(request_id):
    service_request = db.session.get(ServiceRequest, request_id)
    if service_request is None:
        abort(404, description="Request not found.")
    return service_request


@admin.get("/")
def index():
    return redirect(url_for("admin.queue"))


@admin.get("/queue")
@roles_required("admin")
def queue():
    status = request.args.get("status", "").strip()
    category = request.args.get("category", "").strip()
    search = request.args.get("q", "").strip()

    query = ServiceRequest.query

    if status in STATUSES:
        query = query.filter(ServiceRequest.status == status)
    else:
        status = ""

    if category in CATEGORY_LABELS:
        query = query.filter(ServiceRequest.category == category)
    else:
        category = ""

    if search:
        pattern = f"%{search}%"
        query = query.filter(
            or_(
                ServiceRequest.reference.ilike(pattern),
                ServiceRequest.customer_name.ilike(pattern),
            )
        )

    requests = query.order_by(
        ServiceRequest.created_at.desc(),
        ServiceRequest.id.desc(),
    ).all()

    return render_template(
        "admin/queue.html",
        requests=requests,
        total_count=ServiceRequest.query.count(),
        statuses=STATUSES,
        categories=CATEGORY_LABELS,
        selected_status=status,
        selected_category=category,
        search=search,
        filters_active=bool(status or category or search),
    )


@admin.get("/requests/<int:request_id>")
@roles_required("admin")
def request_detail(request_id):
    service_request = get_request_or_404(request_id)
    provider_list = providers()

    return render_template(
        "requests/detail.html",
        service_request=service_request,
        providers=provider_list,
        assign_form=assignment_form(provider_list, service_request.assigned_provider_id),
        note_form=NoteForm(),
        can_assign=service_request.status in ASSIGNABLE_STATUSES,
        back_url=url_for("admin.queue"),
        back_label="Back to queue",
    )


@admin.post("/requests/<int:request_id>/assign")
@roles_required("admin")
def assign_provider(request_id):
    service_request = get_request_or_404(request_id)
    provider_list = providers()
    form = assignment_form(provider_list)

    if service_request.status not in ASSIGNABLE_STATUSES:
        flash("Provider can only be assigned to New or Assigned requests.", "error")
        return redirect(url_for("admin.request_detail", request_id=service_request.id))

    if not provider_list:
        flash("No providers registered.", "error")
        return redirect(url_for("admin.request_detail", request_id=service_request.id))

    if not form.validate_on_submit():
        flash("Select a valid provider.", "error")
        return redirect(url_for("admin.request_detail", request_id=service_request.id))

    provider = db.session.get(User, form.provider_id.data)
    if provider is None or provider.role != "provider":
        flash("Select a valid provider.", "error")
        return redirect(url_for("admin.request_detail", request_id=service_request.id))

    previous_provider = service_request.assigned_provider
    previous_status = service_request.status

    service_request.assigned_provider = provider
    service_request.status = "Assigned"
    service_request.assigned_at = utc_now()

    if previous_provider is None:
        message = f"Your request has been assigned to {provider.display_name}."
        flash(f"Request assigned to {provider.display_name}.", "success")
    elif previous_provider.id != provider.id:
        message = f"Your request has been reassigned to {provider.display_name}."
        flash(f"Request reassigned to {provider.display_name}.", "success")
    else:
        message = f"Your request remains assigned to {provider.display_name}."
        flash(f"Request is still assigned to {provider.display_name}.", "info")

    service_request.events.append(
        StatusEvent(
            previous_status=previous_status,
            new_status="Assigned",
            public_message=message,
            created_at=utc_now(),
        )
    )
    db.session.commit()

    return redirect(url_for("admin.request_detail", request_id=service_request.id))
