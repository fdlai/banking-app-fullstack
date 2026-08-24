Users:
id, first_name, last_name, email, role

Accounts:
id, user_id, account_type, balance, status

Transactions:
id, account_id, transaction_type, amount, timestamp, description

Transfers:
id, from_account_id, to_account_id, amount, timestamp, status

GET /users
GET /users/{id}

GET /accounts
GET /accounts/{id}
POST /accounts

POST /accounts/{id}/deposit
POST /accounts/{id}/withdraw
GET /accounts/{id}/transactions

POST /transfers
