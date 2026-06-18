# POS Bakery — Django Point of Sale System

A full-featured Point of Sale web application built with Django, designed for bakery management. This project demonstrates a clean, modular Django architecture with role-based access control, inventory tracking, and daily sales reporting.

---

## Features

- **Role-Based Authentication** — Custom `@role_required` decorator restricting access by user role (`admin` / `cashier`)
- **Custom User Model** — `AUTH_USER_MODEL` override from project inception, following Django best practices
- **Inventory Management** — Product catalogue with categories, stock tracking, and low-stock alerts
- **Point of Sale Interface** — Cashier-facing order creation with multi-payment mode support (cash, card, mobile)
- **Daily Close (Clôture)** — Admin-only end-of-day reporting with sales summary and history
- **Django Admin** — Fully configured back-office for all models
- **Environment-Based Settings** — `SECRET_KEY`, `DEBUG`, and `ALLOWED_HOSTS` managed via environment variables, production-ready

---

## Project Structure

```
POS_BAKERY/
├── config/             # Project settings, root URLs, WSGI/ASGI
├── accounts/           # Custom user model, role-based auth, decorators
│   ├── models.py       # CustomUser extending AbstractUser
│   ├── decorators.py   # @role_required — view-level permission enforcement
│   └── views.py        # Login, dashboard routing by role
├── inventory/          # Product & category management
│   ├── models.py       # Category, Product (with soft delete & stock alert)
│   └── views.py        # CRUD views restricted to admin role
├── sales/              # Order processing and reporting
│   ├── models.py       # Order, OrderLine (price frozen at sale time)
│   └── views.py        # Cashier interface, daily close, stats dashboard
└── templates/          # Django HTML templates (Bootstrap 5)
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Django 5.x |
| Frontend | Bootstrap 5, Bootstrap Icons |
| Database | SQLite (dev) / PostgreSQL-ready (prod) |
| Auth | Django built-in + custom role system |
| Config | Environment variables via `os.environ` |

---

## Quick Start

**1. Clone and set up the environment**
```bash
git clone https://github.com/your-username/pos-bakery.git
cd pos-bakery
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**2. Configure environment variables**
```bash
cp .env.example .env
# Edit .env with your SECRET_KEY and settings
```

**3. Run migrations and create a superuser**
```bash
python manage.py migrate
python manage.py createsuperuser
```

**4. Start the development server**
```bash
python manage.py runserver
```

Access the app at `http://127.0.0.1:8000` and the admin at `http://127.0.0.1:8000/admin/`.

---

## Role System

| Role | Access |
|---|---|
| `admin` (Gérant) | Full access: inventory, sales, daily close, stats, user management |
| `cashier` (Caissier) | Restricted: cashier interface and daily close only |

Role enforcement is handled by a custom decorator in `accounts/decorators.py`:

```python
@role_required(allowed_roles=['admin'])
def product_list(request):
    ...
```

---

## Key Design Decisions

- **Custom User Model defined at project start** — avoids the painful migration issues of adding it later
- **Price frozen at order time** — `unit_price` is copied onto `OrderLine` so historical records stay accurate even if catalogue prices change
- **Soft delete on products** — `is_active=False` hides a product from the POS without deleting sales history
- **`PermissionDenied` (403) over redirect** — unauthorized access returns a proper HTTP 403, not a silent redirect

---

## Author

Django/Python developer — available for freelance projects.
Portfolio: https://www.freelancer.com/u/atonf0abdulAzz
