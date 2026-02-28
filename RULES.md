## 1. Branch Naming Conventions
Use a **prefix/description** system. 
All branch names should be lowercase and use hyphens `-` to separate words.

`feature/`: New functionality (e.g., `feature/user-authentication`, `feature/room-booking-logic`)
`bugfix/`: Fixing a bug (e.g., `bugfix/fix-postgres-connection`)
`refactor/`: Improving code without changing functionality (e.g., `refactor/models-cleanup`)
`docs/`: Documentation changes only (e.g., `docs/update-readme`)

**Command:** `git checkout -b feature/your-feature-name`

---

## 2. Commit Message Standards
**Format:** `<type>: <short description>`

`feat:`: A new feature for the user.
`fix:`: A bug fix.
`chore:`: Updating build tasks, package manager configs, etc. (e.g., `chore: add .env.example`)
`style:`: Changes that do not affect the meaning of the code (white-space, formatting, missing semi-colons, etc).

**Example:** `git commit -m "feat: implement reservation logic for hotel room"`

---

## 3. Python & Django Naming Rules
Follow **PEP 8** standards to keep the code readable.

**Variables & Functions**: `snake_case` (lowercase) (e.g., `get_user_balance()` )
**Classes (Models/Views)**: `PascalCase` (e.g., `RoomReservation`)
**Folders & Files**: `snake_case` (e.g., `booking_utils.py`)
**Constants**: `UPPER_CASE` (e.g., `MAX_RESERVATION_LIMIT = 5`)

### Django Specifics:

* **Models:** Always use singular names (e.g., `Post`, not `Posts`).
* **Views:** Use descriptive names like `ReservationListView` or `cancel_booking`.

---


## Hello