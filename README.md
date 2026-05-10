# Parcel Tracking Service

REST API for parcel registration and tracking built with Django + Django REST Framework.

## Features

- Post offices, parcels, and parcel status history models.
- Auto-generated unique tracking number for each parcel.
- Parcel status updates with automatic history records.
- Filtering by status and sender city with pagination.
- Validation and business rules for status changes and parcel data.
- Token authentication for workers on status updates.
- Status change logging to console logger `tracking.status`.
- Unified auth: all parcel/offices API routes require token.

## Tech Stack

- Python 3.11+
- Django
- Django REST Framework
- SQLite (default, can be changed to PostgreSQL)

## Run Locally

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py bootstrap
python manage.py runserver
```

`bootstrap` applies migrations, creates a default account (unless it already exists),
and seeds demo data:

- Username: `INITIAL_USER_USERNAME` or `worker`
- Password: `INITIAL_USER_PASSWORD` or `devpass123`
- Offices: `number=1` (Kyiv), `number=2` (Lviv)
- Demo parcels: `TRKDEMO00001`, `TRKDEMO00002`

For production, set strong credentials via environment variables or set `INITIAL_USER_SKIP=true` and create users manually.

## Run With Docker Compose

```bash
docker compose up --build
```

On container start the app runs migrations, `ensure_initial_user`, and `seed_demo_data`.
Compose sets `INITIAL_USER_USERNAME=worker` and `INITIAL_USER_PASSWORD=devpass123` by default
- change these for anything beyond local dev.

App: `http://127.0.0.1:8000`  
PostgreSQL: `localhost:5432`

## API Documentation

- OpenAPI schema: `GET /api/schema/`
- Swagger UI: `GET /api/docs/`

## Main API Endpoints

- `POST /api/parcels/` - create parcel (initial status `created` is added automatically).
- `GET /api/parcels/{tracking_number}/` - get parcel details with full status history.
- `POST /api/parcels/{tracking_number}/status/` - update parcel status.
- `GET /api/offices/{id}/parcels/` - list parcels currently in this office (`arrived` status).
- `GET /api/parcels/?status=in_transit&from_city=Kyiv` - filtered parcel list with pagination.
- `POST /api/auth/token/` - obtain worker token.

All `/api/parcels/*` and `/api/offices/*` endpoints require auth header:
`Authorization: Bearer <token>`.

## Example Requests

Create two offices:

```bash
python manage.py shell -c "from tracking.models import PostOffice; PostOffice.objects.create(number=1, city='Kyiv', address='Main st 1', postal_code='01001'); PostOffice.objects.create(number=2, city='Lviv', address='Square 2', postal_code='79000')"
```

Create parcel:

```bash
curl -X POST http://127.0.0.1:8000/api/parcels/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <worker_token>" \
  -d "{\"sender_full_name\":\"Ivan Petrenko\",\"sender_phone\":\"+380501112233\",\"recipient_full_name\":\"Olena Kovalenko\",\"recipient_phone\":\"+380671234567\",\"weight_kg\":\"2.50\",\"declared_value\":\"1200.00\",\"origin_office\":1,\"destination_office\":2}"
```

Update status:

```bash
curl -X POST http://127.0.0.1:8000/api/parcels/TRKXXXXXXXXXX/status/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <worker_token>" \
  -d "{\"new_status\":\"accepted\",\"office\":1,\"comment\":\"Accepted at origin office\"}"
```

Get token for worker:

```bash
curl -X POST http://127.0.0.1:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"worker\",\"password\":\"devpass123\"}"
```

Get parcel details:

```bash
curl http://127.0.0.1:8000/api/parcels/TRKXXXXXXXXXX/ \
  -H "Authorization: Bearer <worker_token>"
```

## Business Rules Implemented

- Cannot set `delivered` before parcel reaches `arrived`.
- Cannot change status once parcel is in terminal state (`delivered` or `returned`).
- Weight must be greater than `0` and less or equal to `30` kg.
- Declared value must be greater or equal to `0`.
- Origin and destination offices must be different.

## Tests

Run tests:

```bash
python manage.py test
```

Covered cases:

- Parcel creation and initial status history.
- Status update auth requirements.
- Status transition constraints (`delivered` and terminal statuses).
- Validation for same origin and destination office.
