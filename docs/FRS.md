# Home Services Marketplace — Functional Requirements

**Status:** Working draft based on the course brief  
**Version:** 0.1  
**Traceability:** PRD `docs/PRD.md`

## Roles

- **Public customer:** can submit a request and look it up using its reference plus matching email.
- **Administrator:** can view and filter all requests, assign an active provider, and review history.
- **Provider:** can view only assigned requests and make permitted status updates.

Staff accounts are created by an administrator or seeded for the demo. Public staff registration is out of scope.

## Functional requirements

### FR-01 — Submit a service request

The form must collect customer name, email, phone, service category, requested date, service area, and description. Category must be one of Plumbing, Electrical, or Cleaning. Required values must be validated on the server. Invalid submissions must show field-level guidance and must not create a request.

### FR-02 — Confirm a request

On successful submission, the system must save the request, generate a unique non-sequential reference, create the initial status event, and display the reference and next-step instructions. The system must not show the customer’s private details on the confirmation screen beyond the submitted email.

### FR-03 — Look up request status

The customer must provide both the reference and the email used at submission. A successful lookup shows service category, current status, created/updated times, and public status messages. A mismatch or unknown request returns the same generic not-found response and reveals no request data.

### FR-04 — Staff sign-in and role checks

Staff must sign in with email and password. Passwords must be stored as one-way hashes. Administrator and provider permissions must be checked on the server for every protected page and action. Inactive accounts must be denied access.

### FR-05 — Review and filter requests

An administrator can view the request queue and filter by status, category, and provider. Opening a request shows customer/service details, assignment, status history, and internal notes. Internal notes are never shown in public lookup.

### FR-06 — Assign a provider

An administrator can assign one active provider to a request and set or update the confirmed service date. A successful assignment records the actor and timestamp in the history. Inactive or non-provider accounts cannot be assigned.

### FR-07 — Update job status

An assigned provider can move a request from Assigned to In Progress and from In Progress to Completed. The administrator may correct status when needed. Each change records the previous status, new status, actor, timestamp, and an appropriate public message. Invalid transitions must be rejected.

### FR-08 — Responsive and accessible interface

Customer and staff pages must work on mobile and desktop, provide labels and keyboard-operable controls, and show loading, empty, success, and error states.

## Acceptance scenarios

1. Given complete valid customer details, when the form is submitted, then a saved request and unique reference are returned.
2. Given an invalid email or missing required field, when the form is submitted, then validation guidance appears and no request is saved.
3. Given a correct reference and matching email, when lookup is submitted, then only public request details and status history appear.
4. Given a wrong email or unknown reference, when lookup is submitted, then the same generic not-found response appears.
5. Given an administrator and an active provider, when the administrator assigns that provider, then the request and its history record the assignment.
6. Given a provider assigned to a request, when they perform a permitted status change, then the status and history update.
7. Given a provider who is not assigned to a request, when they try to view or change it, then access is denied.
8. Given a public customer, when they request a staff URL or action, then access is denied.

## Deferred requirements

Payments, provider self-registration, customer accounts, bidding, automated matching, chat, live maps, ratings, reviews, recurring bookings, and multi-company support.
