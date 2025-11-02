## Clothing Ecommerce Backend (Django + DRF)

### Requirements
- Python 3.13+
- Windows PowerShell (or your preferred shell)

### Setup
```powershell
python -m venv venv
venv\Scripts\pip install -r requirements.txt
```

### Environment
Create `.env` in project root (example):
```
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=admin@example.com
DJANGO_SUPERUSER_PASSWORD=admin123
```

Load `.env` into current PowerShell session and create superuser:
```powershell
$pairs = Get-Content .env | Where-Object {$_ -match '='}; foreach ($line in $pairs) { $k,$v = $line -split '=',2; if ($k -and $v) { Set-Item -Path Env:$k -Value $v } }
venv\Scripts\python manage.py createsuperuser --noinput
```

### Run
```powershell
venv\Scripts\python manage.py migrate
venv\Scripts\python manage.py runserver
```

### Fixtures (sample data)

#### Load fixtures:
```powershell
# Load catalog data (products, categories, tags)
python manage.py loaddata fixtures/seed_catalog.json

# Load users (for testing API authentication)
python manage.py loaddata fixtures/seed_users.json
```

#### Create/update fixtures:

**Catalog data:**
```powershell
python manage.py dumpdata catalog --indent 2 --output fixtures/seed_catalog.json
```

**Users (with properly hashed passwords):**
```powershell
python create_user_fixtures.py
```
This creates 3 test users:
- `admin` / `admin123` (superuser)
- `customer1` / `customer123` (regular user)
- `customer2` / `customer123` (regular user)

Note: Avoid dumping sensitive apps directly - use the script for users.

### User Authentication

#### Register:
- POST `api/users/register/`
  ```json
  {
    "username": "user123",
    "email": "user@example.com",
    "password": "password123",
    "password_confirm": "password123",
    "first_name": "John",
    "last_name": "Doe"
  }
  ```
  Returns: User data + JWT tokens (access & refresh)

#### Login:
- POST `api/users/login/`
  ```json
  {
    "username": "user123",
    "password": "password123"
  }
  ```
  Returns: User data + JWT tokens (access & refresh)

#### Profile:
- GET `api/users/profile/` (Requires: Authorization: Bearer <token>)
  Returns: Current user profile data

#### Alternative JWT endpoints (DRF SimpleJWT):
- POST `api/auth/token/` → { username, password }
- POST `api/auth/token/refresh/` → { refresh }

### API Endpoints
- `api/categories/` (CRUD)
- `api/products/` (CRUD)
- `api/cart/me` (GET/POST to view/update cart)
- `api/cart-items/` (CRUD items)
- `api/orders/` (list/create for current user)

Media served at `/media/`. Admin at `/admin/`.


