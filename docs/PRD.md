# Home Services Marketplace — Product Requirements

**Status:** Draft based on course brief and learner-approved Flask direction  
**Version:** 0.2  
**Purpose:** Build a small portfolio app that demonstrates a request from submission through completion.

## 1. Problem

A small home-services company receives service requests through calls and messages. Details get lost, staff coordinate provider assignments manually, and customers have to call for updates. The app will give each request one record and a clear status.

## 2. Users

- **Customer:** submits a service request and later checks its status.
- **Administrator:** reviews new requests, assigns a provider, and records operational updates.
- **Service provider:** views assigned requests and advances their status.

For the first release, providers and administrators are created by the app operator. Customers do not need accounts.

## 3. Core workflow

1. Customer submits contact details, service category, requested date, area, and a description.
2. The app validates the request and returns a unique reference number.
3. Administrator reviews the request and assigns an active provider.
4. Provider updates progress using allowed status changes.
5. Customer checks the latest status using the reference number and matching email address.

## 4. Version 1 scope

### Must have

- Three fixed categories: plumbing, electrical, and cleaning.
- Request form with required-field validation.
- Unique reference number and confirmation after submission.
- Customer status lookup requiring both reference number and email match.
- Staff sign-in with administrator and provider roles.
- Administrator request queue, filters, detail view, and provider assignment.
- Provider view of assigned jobs and permitted status updates.
- Timestamped status history.
- Responsive layout, helpful empty/error/success states, and setup instructions.

### Out of scope

- Payments, provider bidding, pricing, reviews, chat, live maps, automated matching, customer/provider self-registration, and multiple companies.

## 5. Acceptance checks

1. Given valid request details, when the customer submits, then the app stores the request and shows a unique reference.
2. Given a valid reference and matching email, when the customer looks up the request, then the latest public status and update time appear.
3. Given a wrong email or unknown reference, when a lookup is attempted, then the app gives a generic not-found response without exposing request details.
4. Given an administrator, when they assign an active provider, then the request shows that provider and an assignment event is recorded.
5. Given a provider assigned to a request, when they make a permitted status change, then the new status and time appear in the history.
6. Given a user without the required staff role, when they try to open a staff action, then the server denies the action.

## 6. Starting technical direction

Use Python with Flask, server-rendered Jinja templates, SQLAlchemy, Flask-Login, and Flask-WTF. Use SQLite for local learning and PostgreSQL for the deployed version. Keep the same request and status rules in both environments. This stack is the learner-approved adaptation for this project.

## 7. Definition of done

A customer can submit and look up a request; an administrator can assign it; the assigned provider can complete it; unauthorized staff actions are blocked; the acceptance checks pass; and the deployed demo has a README and no exposed secrets.

## 8. Learning log

- **Current step:** agree on the problem, users, scope, and success checks.
- **Next step:** create the minimal Flask application and inspect each file before adding persistence and roles.
