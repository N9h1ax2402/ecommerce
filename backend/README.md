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

### Auth (JWT)
- POST `api/auth/token/` → { username, password }
- POST `api/auth/token/refresh/` → { refresh }

### API Endpoints
- `api/categories/` (CRUD)
- `api/products/` (CRUD)
- `api/cart/me` (GET/POST to view/update cart)
- `api/cart-items/` (CRUD items)
- `api/orders/` (list/create for current user)

Media served at `/media/`. Admin at `/admin/`.


