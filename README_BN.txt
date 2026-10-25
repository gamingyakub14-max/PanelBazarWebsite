# Panel Bazar full website (Flask + SQLite)

## Features
- Sign up and login with hashed passwords
- SQLite persistent user accounts and balances
- Product catalog
- Atomic balance deduction when a logged-in user buys a product
- Manual bKash/Nagad deposit request and admin approval/rejection
- Duplicate transaction ID prevention
- Admin dashboard: review deposits, add/subtract user balance, view users and orders
- CSRF form tokens and basic security headers

## Important
This is a starter project. Before real public launch:
- Deploy behind HTTPS.
- Set a long random `SECRET_KEY` environment variable.
- Set `ADMIN_USERNAME`, `ADMIN_PASSWORD`, and `ADMIN_EMAIL` environment variables BEFORE first run to create the admin account. Use a unique, strong password.
- Set `BKASH_NUMBER` and `NAGAD_NUMBER` to the correct payment numbers (currently placeholders in the template). The app reads these environment variables for the Add Fund page.
- Keep the SQLite database on persistent storage. Do not deploy on an ephemeral filesystem.
- Back up the database.
- Deposit approvals are manual; verify payment in your own payment account before approving.
- Do not sell or distribute software that violates a game's/service's terms or compromises other users.

## Local / hosting run
1. Upload and unzip the project on a Python-capable host.
2. Install dependencies: `pip install -r requirements.txt`
3. Set environment variables:
   - `SECRET_KEY` = long random secret
   - `ADMIN_USERNAME` = your admin username
   - `ADMIN_PASSWORD` = strong admin password
   - `ADMIN_EMAIL` = your admin email
   - `BKASH_NUMBER` = your bKash personal number
   - `NAGAD_NUMBER` = your Nagad personal number
   - `COOKIE_SECURE=1` after HTTPS is enabled
4. Run with a production WSGI server, for example `gunicorn app:app` (install gunicorn if your host requires it). Do not use Flask debug mode publicly.
5. Visit `/register` to create a customer account, `/login` to sign in, `/admin` for the admin dashboard.

Admin account creation happens on startup only if the configured email/username do not already exist. If changing admin credentials later, change them through a controlled database/admin process; do not expose credentials in public code.
