from flask import Blueprint, abort, flash, redirect, url_for
from flask_login import current_user, login_required

from .extensions import db
from .forms import NoteForm
from .models import Note, ServiceRequest


notes = Blueprint("notes", __name__)


def detail_url(service_request):
    if current_user.is_admin:
        return url_for("admin.request_detail", request_id=service_request.id)
    return url_for("provider.job_detail", request_id=service_request.id)


@notes.post("/requests/<int:request_id>/notes")
@login_required
def add_note(request_id):
    service_request = db.session.get(ServiceRequest, request_id)
    if service_request is None:
        abort(404, description="Request not found.")

    is_admin = current_user.is_admin
    is_assigned_provider = (
        current_user.is_provider
        and service_request.assigned_provider_id == current_user.id
    )
    if not (is_admin or is_assigned_provider):
        abort(403, description="You do not have permission to add a note to this request.")

    form = NoteForm()
    if not form.validate_on_submit():
        message = form.body.errors[0] if form.body.errors else "Note could not be saved."
        flash(message, "error")
        return redirect(detail_url(service_request))

    body = form.body.data.strip()
    if not body:
        flash("Note cannot be empty.", "error")
        return redirect(detail_url(service_request))

    db.session.add(
        Note(
            request_id=service_request.id,
            author_id=current_user.id,
            body=body,
            is_customer_visible=form.is_customer_visible.data,
        )
    )
    db.session.commit()

    flash("Note added.", "success")
    return redirect(detail_url(service_request))
