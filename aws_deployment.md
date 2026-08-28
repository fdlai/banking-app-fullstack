# AWS Deployment Guide

This guide explains how to deploy the TrustPoint Bank application using:

- **Frontend:** React/Vite → Amazon S3 → CloudFront
- **Backend:** FastAPI → AWS Lambda → API Gateway
- **Database:** Supabase PostgreSQL

Each team member can deploy their own copy using their individual AWS credentials.

---

# Architecture

```text
React / Vite
     |
     v
Amazon S3
     |
     v
CloudFront
     |
     | API Requests
     v
API Gateway
     |
     v
AWS Lambda
     |
     v
Mangum
     |
     v
FastAPI
     |
     v
Supabase PostgreSQL
```

CloudFront serves the React frontend.

The frontend communicates **directly with the API Gateway URL**. CloudFront does not sit in front of API Gateway.

---

# 1. Database Setup — Supabase

Create a Supabase project and obtain the PostgreSQL connection string.

For local development and Alembic migrations, the Supabase Session Pooler connection can be used.

Example:

```text
DATABASE_URL=postgresql+psycopg://postgres.<PROJECT_ID>:<PASSWORD>@<SUPABASE_POOLER_HOST>:5432/postgres
```

Do **not** commit database passwords or connection strings to Git.

Once `DATABASE_URL` points to Supabase, run:

```bash
alembic upgrade head
```

This creates the application's tables in the Supabase PostgreSQL database.

---

# 2. Prepare FastAPI for Lambda

AWS Lambda does not run FastAPI through Uvicorn like our local development environment.

We use **Mangum** as an adapter between AWS Lambda/API Gateway and FastAPI.

Make sure Mangum is installed:

```bash
pip install mangum
```

and included in:

```text
requirements.txt
```

At the top of `main.py`:

```python
from mangum import Mangum
```

At the bottom:

```python
handler = Mangum(app)
```

The AWS Lambda handler will therefore be:

```text
main.handler
```

---

# 3. Configure CORS

The deployed CloudFront frontend has a different origin than the backend API.

`main.py` reads the deployed frontend URL from an environment variable:

```python
import os

frontend_origin = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        frontend_origin,
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Each team member can therefore use the same backend code and configure their own CloudFront URL through Lambda.

For example:

```text
FRONTEND_ORIGIN=https://your-cloudfront-domain.cloudfront.net
```

Do not include a trailing `/`.

---

# 4. Build the Lambda Deployment Package

## Important for Windows / Git Bash

Do **not** copy your Windows virtual environment into the Lambda deployment.

AWS Lambda runs on Linux, and some Python dependencies contain platform-specific compiled binaries.

The method that successfully worked for this project was to install the dependencies using the **official AWS Lambda Python 3.12 Docker image**.

Docker must be installed and running before executing these commands.

From the backend project root:

```bash
rm -rf lambda_package
mkdir lambda_package
```

Then install the dependencies:

```bash
MSYS_NO_PATHCONV=1 docker run --rm \
  --entrypoint /bin/bash \
  -v "$PWD":/var/task \
  public.ecr.aws/lambda/python:3.12 \
  -c "pip install -r requirements.txt -t lambda_package"
```

### Why `MSYS_NO_PATHCONV=1`?

Git Bash/MSYS can automatically modify Unix-style paths before passing them to Windows applications.

This can interfere with Docker volume paths.

Setting:

```text
MSYS_NO_PATHCONV=1
```

prevents Git Bash from modifying the Docker path.

---

# 5. Copy the Backend Source Code

After the dependencies have been installed into `lambda_package`, copy the backend source code into it.

For the current TrustPoint Bank project structure, use:

```bash
cp main.py config.py database.py lambda_package/
```

Then copy the backend directories:

```bash
cp -r core data models repositories routers schemas lambda_package/
```

These are the exact copy commands used for the successful deployment.

The resulting directory should contain both the application code and the installed Python dependencies.

For example:

```text
lambda_package/
├── main.py
├── config.py
├── database.py
├── core/
├── data/
├── models/
├── repositories/
├── routers/
├── schemas/
├── fastapi/
├── sqlalchemy/
├── mangum/
├── psycopg/
└── ...other installed dependencies...
```

It is particularly important that:

```text
main.py
```

is directly inside `lambda_package`, because the Lambda handler is:

```text
main.handler
```

---

# 6. Create the Lambda ZIP

Create the ZIP using Python's built-in `shutil` module:

```bash
python -c "import shutil; shutil.make_archive('lambda_deployment', 'zip', 'lambda_package')"
```

This creates:

```text
lambda_deployment.zip
```

in the project root.

This method was used because the standard `zip` command may not be available in Git Bash on Windows.

---

# 7. Create the AWS Lambda Function

In AWS:

```text
AWS Console
→ Lambda
→ Create function
```

Configure the function with:

```text
Runtime: Python 3.12
Architecture: x86_64
```

Use the AWS execution role provided for the training/lab.

Once the function has been created, upload:

```text
lambda_deployment.zip
```

using:

```text
Lambda
→ Code
→ Upload from
→ .zip file
```

Set the Lambda handler to:

```text
main.handler
```

---

# 8. Configure Lambda Environment Variables

Go to:

```text
Lambda
→ Configuration
→ Environment variables
```

Configure the backend environment variables.

The application currently requires:

```text
DATABASE_URL=<Supabase PostgreSQL connection string>

JWT_SECRET_KEY=<your secret key>

JWT_ALGORITHM=HS256

ACCESS_TOKEN_EXPIRE_MINUTES=30

FRONTEND_ORIGIN=https://your-cloudfront-domain.cloudfront.net
```

Do not commit these values to Git.

For the Lambda/serverless database connection, use the appropriate Supabase pooler connection rather than a local PostgreSQL URL.

---

# 9. Create API Gateway

Create an **HTTP API** in Amazon API Gateway.

Connect the API to the Lambda function.

Use:

```text
Payload format version: 2.0
```

Configure the routes needed to forward requests to the Lambda/FastAPI application.

Use the:

```text
$default
```

stage with automatic deployment enabled.

API Gateway will provide an invoke URL similar to:

```text
https://xxxxxxxxxx.execute-api.us-east-1.amazonaws.com
```

This URL becomes the production backend base URL.

Before deploying the frontend, test the backend through API Gateway.

Useful endpoints include:

```text
/
```

```text
/auth/register
```

```text
/auth/login
```

Postman is useful here because it allows the backend deployment to be tested independently of browser CORS configuration.

A successful request confirms the following path is working:

```text
API Gateway
    ↓
Lambda
    ↓
Mangum
    ↓
FastAPI
    ↓
Supabase
```

---

# 10. Configure the Frontend API URL

The React frontend reads its backend URL from:

```text
VITE_API_BASE_URL
```

For the production build, set it to the API Gateway invoke URL:

```text
VITE_API_BASE_URL=https://xxxxxxxxxx.execute-api.us-east-1.amazonaws.com
```

Do not include an endpoint such as `/auth/login` in this value.

The frontend API functions append the appropriate endpoint paths.

Build the production frontend:

```bash
npm run build
```

Vite will create:

```text
dist/
```

---

# 11. Create the Frontend S3 Bucket

Create an Amazon S3 bucket in:

```text
us-east-1
```

Recommended configuration:

```text
Bucket type: General purpose
Object ownership: ACLs disabled
Block all public access: ON
Versioning: Disabled
Encryption: SSE-S3
```

The S3 bucket can remain private because CloudFront will be given access to it.

Upload the **contents** of:

```text
dist/
```

to the root of the S3 bucket.

Correct:

```text
S3 Bucket
├── index.html
├── assets/
├── favicon.svg
└── ...
```

Incorrect:

```text
S3 Bucket
└── dist/
    ├── index.html
    └── assets/
```

Make sure the files inside `assets/` are uploaded as well.

---

# 12. Create the CloudFront Distribution

Create a CloudFront distribution and select the frontend S3 bucket as the origin.

Allow CloudFront to access the private S3 bucket.

Set:

```text
Default root object: index.html
```

CloudFront will provide a domain similar to:

```text
https://xxxxxxxxxxxxxx.cloudfront.net
```

This becomes the production frontend URL.

---

# 13. Configure React Router / SPA Routing

React Router handles routes such as:

```text
/login
/register
/customer
/teller
/admin
```

S3 and CloudFront do not inherently know that these are client-side React routes.

Configure a CloudFront custom error response:

```text
HTTP Error Code: 403
Response Page Path: /index.html
HTTP Response Code: 200
Minimum TTL: 0
```

Also configure:

```text
HTTP Error Code: 404
Response Page Path: /index.html
HTTP Response Code: 200
Minimum TTL: 0
```

This allows a URL such as:

```text
https://your-domain.cloudfront.net/customer
```

to load `index.html`, after which React Router handles `/customer`.

This does **not** bypass authentication or `ProtectedRoute`.

It only allows the React application to load for client-side routes.

---

# 14. Add the CloudFront URL to Lambda

After CloudFront has been created, copy the CloudFront frontend URL.

Return to:

```text
Lambda
→ Configuration
→ Environment variables
```

Set:

```text
FRONTEND_ORIGIN=https://xxxxxxxxxxxxxx.cloudfront.net
```

Do not include a trailing `/`.

This allows the deployed frontend to make browser requests to the API Gateway/FastAPI backend without being blocked by CORS.

---

# 15. Updating Lambda After Backend Changes

You do **not** need to completely rebuild `lambda_package` every time application code changes.

If the Python dependencies have not changed, copy the changed application files into the existing package.

For example, if only `main.py` changed:

```bash
cp main.py lambda_package/main.py
```

Remove the previous ZIP:

```bash
rm -f lambda_deployment.zip
```

Recreate it:

```bash
python -c "import shutil; shutil.make_archive('lambda_deployment', 'zip', 'lambda_package')"
```

Then upload the new:

```text
lambda_deployment.zip
```

through:

```text
Lambda
→ Code
→ Upload from
→ .zip file
```

Uploading the new ZIP updates the Lambda code.

A separate deployment step is not required.

### If dependencies change

If `requirements.txt` changes, rebuild the package from scratch:

```bash
rm -rf lambda_package
mkdir lambda_package
```

Reinstall dependencies:

```bash
MSYS_NO_PATHCONV=1 docker run --rm \
  --entrypoint /bin/bash \
  -v "$PWD":/var/task \
  public.ecr.aws/lambda/python:3.12 \
  -c "pip install -r requirements.txt -t lambda_package"
```

Copy the application source again:

```bash
cp main.py config.py database.py lambda_package/

cp -r core data models repositories routers schemas lambda_package/
```

Then recreate the ZIP:

```bash
python -c "import shutil; shutil.make_archive('lambda_deployment', 'zip', 'lambda_package')"
```

---

# 16. Updating the Frontend

After making frontend changes, rebuild:

```bash
npm run build
```

Upload the new contents of:

```text
dist/
```

to the frontend S3 bucket.

If CloudFront continues serving an older cached version, create a CloudFront invalidation for:

```text
/*
```

---

# 17. Final Deployment Test

Verify the following:

1. Open the CloudFront URL.
2. Confirm the React application loads.
3. Confirm `/login` loads.
4. Log in with a valid user.
5. Confirm the `/auth/login` API request succeeds.
6. Confirm the JWT/authentication flow works.
7. Confirm the user reaches the correct dashboard.
8. Test at least one authenticated API request.
9. Refresh while on a React route such as `/customer`.
10. Confirm the React application still loads correctly.
11. Log out and log back in.

If these tests succeed, the complete deployment is working:

```text
Browser
   ↓
CloudFront
   ↓
S3 / React
   ↓
API Gateway
   ↓
Lambda
   ↓
Mangum
   ↓
FastAPI
   ↓
Supabase PostgreSQL
```

---

# 18. Git Ignore

The generated Lambda deployment files should **not** be committed to Git.

Add the following to `.gitignore`:

```gitignore
lambda_package/
lambda_deployment.zip
```

These are generated deployment artifacts and can be recreated from the source code and `requirements.txt`.

---

# Troubleshooting

## `ModuleNotFoundError` or binary package errors in Lambda

Do not package the local Windows `.venv`.

Rebuild `lambda_package` using the AWS Lambda Docker image described in Step 4.

---

## Docker volume/path errors in Git Bash

Make sure the command begins with:

```text
MSYS_NO_PATHCONV=1
```

This prevents Git Bash from rewriting the Docker mount path.

---

## API works in Postman but fails in the browser with a CORS error

Check the Lambda environment variable:

```text
FRONTEND_ORIGIN
```

It should exactly match the CloudFront origin:

```text
https://xxxxxxxxxxxxxx.cloudfront.net
```

Do not include a trailing `/`.

---

## CloudFront homepage works but `/login` or `/customer` fails on refresh

Check the CloudFront custom error responses for:

```text
403 → /index.html → 200
404 → /index.html → 200
```

---

## Frontend is calling localhost after deployment

Check:

```text
VITE_API_BASE_URL
```

It must contain the API Gateway URL **before** running:

```bash
npm run build
```

Vite environment variables are built into the production bundle at build time.

---

## Lambda ZIP is fairly large

A deployment ZIP containing all Python dependencies can be tens of megabytes.

This is expected for this project.

Do not commit the ZIP to Git; recreate it when needed using the steps above.
