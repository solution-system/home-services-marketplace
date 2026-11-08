from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user

from .auth import roles_required
from .constants import CATEGORY_LABELS, STATUSES
from .extensions import db
from .forms import NoteForm, UpdateStatusForm
from .models import ServiceRequest, StatusEvent, utc_now
from .workflow import (
    PROVIDER_ACTION_LABELS,
    PROVIDER_TRANSITION_MESSAGES,
    next_provider_status,
)


provider = Blueprint("provider", __name__, url_prefix="/provider")


@provider.get("/")
def index():
    return redirect(url_for("provider.jobs"))


@provider.get("/jobs")
@roles_required("provider")
def jobs():
    status = request.args.get("status", "").strip()

    query = ServiceRequest.query.filter(
        ServiceRequest.assigned_provider_id == current_user.id
    )
    if status in STATUSES:
        query = query.filter(ServiceRequest.status == status)
    else:
        status = ""

    requests = query.order_by(
        ServiceRequest.created_at.desc(),
        ServiceRequest.id.desc(),
    ).all()

    return render_template(
        "provider/jobs.html",
        requests=requests,
        total_assigned=ServiceRequest.query.filter(
            ServiceRequest.assigned_provider_id == current_user.id
        ).count(),
        statuses=STATUSES,
        categories=CATEGORY_LABELS,
        selected_status=status,
    )


@provider.get("/jobs/<int:request_id>")
@roles_required("provider")
def job_detail(request_id):
    service_request = db.session.get(ServiceRequest, request_id)
    if service_request is None:
        abort(404, description="Request not found.")

    if service_request.assigned_provider_id != current_user.id:
        abort(403, description="You do not have permission to view this request.")

    next_status = next_provider_status(service_request.status)
    status_form = UpdateStatusForm()
    if next_status is not None:
        status_form.new_status.data = next_status

    return render_template(
        "requests/detail.html",
        service_request=service_request,
        providers=[],
        assign_form=None,
        can_assign=False,
        status_form=status_form,
        next_status=next_status,
        action_label=PROVIDER_ACTION_LABELS.get(next_status),
        note_form=NoteForm(),
        back_url=url_for("provider.jobs"),
        back_label="Back to my jobs",
    )


@provider.post("/jobs/<int:request_id>/status")
@roles_required("provider")
def update_status(request_id):
    service_request = db.session.get(ServiceRequest, request_id)
    if service_request is None:
        abort(404, description="Request not found.")

    if service_request.assigned_provider_id != current_user.id:
        abort(403, description="You are not assigned to this request.")

    form = UpdateStatusForm()
    if not form.validate_on_submit():
        flash("This status change is not allowed.", "error")
        return redirect(url_for("provider.job_detail", request_id=service_request.id))

    current_status = service_request.status
    new_status = form.new_status.data.strip()

    if current_status == "Completed":
        flash("This job is already completed.", "error")
        return redirect(url_for("provider.job_detail", request_id=service_request.id))

    expected_status = next_provider_status(current_status)
    if expected_status is None or new_status != expected_status:
        flash("This status change is not allowed.", "error")
        return redirect(url_for("provider.job_detail", request_id=service_request.id))

    now = utc_now()
    service_request.status = new_status
    if new_status == "In Progress":
        service_request.started_at = now
    elif new_status == "Completed":
        service_request.completed_at = now

    service_request.events.append(
        StatusEvent(
            previous_status=current_status,
            new_status=new_status,
            public_message=PROVIDER_TRANSITION_MESSAGES[new_status],
            created_at=now,
        )
    )
    db.session.commit()

    flash(f"Job marked as {new_status.lower()}.", "success")
    return redirect(url_for("provider.job_detail", request_id=service_request.id))
