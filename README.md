# Banking App API

Backend REST API for our banking application, built with **Python** and **FastAPI**.

The initial version of the API uses hardcoded in-memory data. Database integration will be added later.

## Getting Started

### 1. Clone the repository

Clone the repository and navigate into the project directory.

If you already have the repository cloned, make sure you have the latest version of `main`:

```bash
git checkout main
git pull origin main
```

### 2. Create a virtual environment

From the root directory of the project:

```bash
python -m venv .venv
```

Each team member should create their own local `.venv`. The `.venv` folder is ignored by Git and should **not** be committed.

### 3. Activate the virtual environment

#### Windows — Git Bash

```bash
source .venv/Scripts/activate
```

#### Windows — PowerShell

```powershell
.venv\Scripts\Activate.ps1
```

#### macOS / Linux

```bash
source .venv/bin/activate
```

After activation, you should see `(.venv)` at the beginning of your terminal prompt.

### 4. Install dependencies

With the virtual environment activated:

```bash
pip install -r requirements.txt
```

This currently installs FastAPI and Uvicorn.

### 5. Run the API

From the project root:

```bash
uvicorn main:app --reload
```

The development server should start at:

```text
http://127.0.0.1:8000
```

### 6. Open the FastAPI documentation

FastAPI automatically provides interactive Swagger documentation at:

```text
http://127.0.0.1:8000/docs
```

You can use this page to view and test the API endpoints.

## Development Workflow

Before working on your assigned feature, create a feature branch from the latest version of `main`.

Example:

```bash
git checkout main
git pull origin main
git checkout -b feature/your-feature
```

---

# Planned Data Models

These are the agreed-upon initial data shapes for the hardcoded version of the API.

## User

| Field        | Description                              |
| ------------ | ---------------------------------------- |
| `id`         | Unique user ID                           |
| `first_name` | User's first name                        |
| `last_name`  | User's last name                         |
| `email`      | User's email address                     |
| `role`       | User role, such as `customer` or `admin` |

## Account

| Field          | Description                                             |
| -------------- | ------------------------------------------------------- |
| `id`           | Unique account ID                                       |
| `user_id`      | ID of the user who owns the account                     |
| `account_type` | Account type, such as `checking` or `savings`           |
| `balance`      | Current account balance                                 |
| `status`       | Account status, such as `active`, `frozen`, or `closed` |

## Transaction

| Field              | Description                             |
| ------------------ | --------------------------------------- |
| `id`               | Unique transaction ID                   |
| `account_id`       | Account associated with the transaction |
| `transaction_type` | Type of transaction                     |
| `amount`           | Transaction amount                      |
| `timestamp`        | Date and time of the transaction        |
| `description`      | Description of the transaction          |

## Transfer

| Field             | Description                   |
| ----------------- | ----------------------------- |
| `id`              | Unique transfer ID            |
| `from_account_id` | Account sending the money     |
| `to_account_id`   | Account receiving the money   |
| `amount`          | Amount being transferred      |
| `timestamp`       | Date and time of the transfer |
| `status`          | Transfer status               |

---

# Planned API Endpoints

## Users

```text
GET /users
GET /users/{id}
```

## Accounts

```text
GET  /accounts
GET  /accounts/{id}
POST /accounts
```

## Transactions

```text
POST /accounts/{id}/deposit
POST /accounts/{id}/withdraw
GET  /accounts/{id}/transactions
```

## Transfers

```text
POST /transfers
```

---

# Team Responsibilities

| Team Member | Feature                                 |
| ----------- | --------------------------------------- |
| Luis        | Users / roles                           |
| Emanuel     | Accounts                                |
| Steven      | Transactions, deposits, and withdrawals |
| Josiah      | Transfers                               |
| Fred        | FastAPI structure and integration       |
