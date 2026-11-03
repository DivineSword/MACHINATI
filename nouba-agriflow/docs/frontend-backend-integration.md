# Frontend ↔ Backend Integration Guide

This document is written for a coding agent that needs to turn the static frontend mockups into a real UI connected to the FastAPI backend in this repository.

Priority: integrate the backend contract first, then align the static pages to real data.

## 1. Objective

The goal is to transform the prototype pages in `frontend/` into working pages backed by the real API and DB logic already implemented in `backend/app/`.

Do not treat the HTML files as final product code. Treat them as design references.

---

## 2. Current architecture

The project currently has two main parts:

- Backend: FastAPI app in `backend/app/`
- Frontend: static HTML mockups in `frontend/` plus a React/Vite app in `frontend/src/`

The backend already contains the real business logic for:

- WhatsApp webhook ingestion
- request processing
- request review status changes
- machine listing
- SQLite persistence

The frontend HTML files are design/prototype pages and currently use hardcoded demo data.

---

## 3. Backend contract that must be honored

From the actual code in `backend/app/main.py` and `backend/app/db.py`, the backend exposes the following contract.

### GET /api/requests
Returns a list of requests ordered by newest first.

This is the main endpoint for dashboards.

Example response shape:

```json
[
  {
    "id": 1,
    "farmer_phone": "+212600000000",
    "payload": {
      "machine_type": "tractor",
      "operation": "soil preparation",
      "area_hectares": 5,
      "location": "Sefrou",
      "preferred_date": "2026-11-12"
    },
    "status": "pending_review",
    "created_at": "2026-11-03T09:00:00",
    "updated_at": "2026-11-03T09:00:00"
  }
]
```

### PATCH /api/requests/{request_id}/status
Updates the status of a request.

The UI must send a JSON body such as:

```json
{ "status": "approved" }
```

Allowed values:

- `pending_review`
- `approved`
- `rejected`
- `completed`

Important: the backend enforces this in `main.py` and does not accept arbitrary values.

### GET /api/machines
Returns machine inventory.

The frontend should treat this as the source of truth for machine cards and counts.

Example response shape:

```json
[
  {
    "id": 1,
    "name": "Tracteur Massey Ferguson 240",
    "machine_type": "tractor",
    "location": "Sefrou",
    "hourly_rate": 450,
    "available": 1
  }
]
```

---

## 4. What the static frontend pages currently do wrong

The HTML mockups in `frontend/index.html`, `frontend/cooperative.html`, and `frontend/equipe-machinati.html` are not yet connected to the backend because they contain:

- static fake data
- hardcoded tables and cards
- demo counters
- mock action buttons without API calls
- no request lifecycle logic
- no authentication
- no persistence layer

These pages are useful as design prototypes, but they are not production-integrated UI.

---

## 5. Real integration rules

### Rule 1: UI must use backend data, not hardcoded arrays

This is the first requirement for a coding agent. Replace static demo content with API-driven rendering.

Any dashboard card or table should be rendered from:

- `GET /api/requests`
- `GET /api/machines`

Instead of writing static HTML rows for requests and machines.

### Rule 2: map backend data to page labels

The frontend should not directly expose raw backend status strings to end users without translation.

The backend status values are simpler than the mockup labels.

You will need a translation layer like:

```js
const statusMap = {
  pending_review: 'À traiter',
  approved: 'Approuvée',
  rejected: 'Refusée',
  completed: 'Terminée'
};
```

This is necessary because the mockups use more user-facing labels than the backend currently exposes.

### Rule 3: approval/rejection actions must call the API

Every action button that changes state must call the backend, not just modify DOM text.

The dashboard mockup contains buttons like:

- Accept
- Refuse
- Other dates

Those actions should become API calls like:

```js
fetch(`/api/requests/${id}/status`, {
  method: 'PATCH',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ status: 'approved' })
});
```

### Rule 4: do not assume all mockup fields exist in backend

The backend payload is a JSON object stored under `payload`. The frontend must read values from there and format them for display.

The mockup uses fields such as:

- customer name
- booking date
- machine category
- operational metrics
- distribution charts

The backend stores request payloads as JSON in `payload`, and machine details are in the `machines` table.

You must map from backend JSON objects to UI-friendly fields before rendering.

---

## 6. Page-by-page integration plan

### A. Landing page (`frontend/index.html`)

This page should become a machine catalog or booking entry page.

Use:

- `GET /api/machines` for visible inventory
- optional future `POST` flows for booking requests if added later

Implementation note: this page is lower-priority because there is no backend endpoint yet for browser-side request creation.

### B. Cooperative dashboard (`frontend/cooperative.html`)

This is the best candidate for real integration because it matches the backend design closely.

Needed changes:

- replace hardcoded list entries with `GET /api/requests`
- render request `payload` fields
- calculate pending/approved counts from request data
- connect buttons to `PATCH /api/requests/{id}/status`
- render machine inventory from `GET /api/machines`

This page should be implemented first.

### C. Operations dashboard (`frontend/equipe-machinati.html`)

This page is a reporting layer and should be fed from the same endpoints.

Needed changes:

- compute stats from `GET /api/requests`
- compute machine counts from `GET /api/machines`
- map statuses to operational groups
- display summary cards and charts based on real data

This page should not rely on fictional data once it is connected.

---

## 7. Core logic the pages are missing

The frontend mockups do not reflect the actual workflow in the backend:

- inbound WhatsApp messages
- AI transcription and extraction
- draft conversation state
- missing-field follow-up questions
- explicit confirmation before creating a request
- human review and approval pipeline

This is the most important difference between the static pages and the real product.

The UI pages are only the presentation layer. The app logic lives in the backend service layer and database workflow.

---

## 8. Important backend gaps to be aware of

Before exposing the UI publicly, you still need to build or define backend support for:

- real machine creation/editing
- browser-side request creation
- robust request validation
- auth and role-based access
- protected API access for cooperative and operators
- machine availability + booking conflict validation
- durable background job handling for AI and webhook failures

The current backend is a functional MVP, not a full production dashboard with all business rules implemented.

---

## 9. Recommended integration order

1. Connect the cooperative dashboard to `/api/requests` and `/api/machines`
2. Add real status update actions via PATCH
3. Render dynamic cards and counts from the API
4. Connect the landing page to machine data
5. Add operational analytics from request summaries
6. Add authentication and protected API routes before public deployment
7. Add booking and machine management endpoints later

---

## 10. Small implementation pattern

A simple front-end pattern is:

```js
async function loadRequests() {
  const res = await fetch('/api/requests');
  const requests = await res.json();
  renderRequests(requests);
}

async function updateRequestStatus(id, status) {
  await fetch(`/api/requests/${id}/status`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status })
  });
}
```

This should replace hardcoded DOM blocks.

---

## 11. Implementation checklist for the coding agent

Use this as the practical execution order:

1. Read the backend contract in `backend/app/main.py` and `backend/app/db.py`.
2. Pick `frontend/cooperative.html` as the first integration target.
3. Replace static request rows with `fetch('/api/requests')`.
4. Replace static machine rows with `fetch('/api/machines')`.
5. Add a status translation helper for UI labels.
6. Add PATCH handlers for each action button.
7. Refresh the table after successful status changes.
8. Repeat for `frontend/equipe-machinati.html` using computed metrics from the same APIs.
9. Leave `frontend/index.html` as a design mock until booking endpoints exist.
10. Add auth before any public deployment.

---

## 12. Final recommendation

Use the static HTML pages as visual prototypes only.

The actual priority is to integrate the cooperative dashboard with the real backend first, because that is the part that already matches the app’s existing database and API model.

This is the shortest route to a functional product without building the entire front-end from scratch.
