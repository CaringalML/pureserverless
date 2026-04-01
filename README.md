# Serverless Web App

A full Django CRUD web application running on AWS Lambda, provisioned with Terraform and deployed automatically via GitHub Actions CI/CD. No servers to manage — push to a branch and it deploys itself.

**Live stack:** Django 5 → Mangum (ASGI) → AWS Lambda → API Gateway v2 → Sydney (`ap-southeast-2`)

**Frontend:** Tailwind CSS (CDN) + HTMX + Alpine.js — reactive UI with zero page reloads, no build step, no Node.js.

---

## Architecture

```
Browser
  └── API Gateway v2 (HTTP API, $default catch-all route)
        └── Lambda (Python 3.12 — Django + Mangum)
              ├── Neon PostgreSQL (serverless Postgres, credentials via AWS SSM)
              ├── Tailwind CSS  (CDN)
              ├── HTMX          (CDN — partial HTML swaps, no full page reloads)
              ├── Alpine.js     (CDN — lightweight UI state)
              └── CloudWatch Logs (/aws/lambda/serverless-web-app-dev)

Terraform Remote State
  ├── S3 Bucket (maangasserverless) — Intelligent-Tiering storage
  └── DynamoDB Table (terraform-state-lock) — state locking
```

---

## Branches

| Branch | Description |
|--------|-------------|
| `hello-world` | Minimal Django hello world page |
| `CRUD` | Full CRUD app — Items list with inline create, edit, delete via HTMX |

The CI/CD pipeline targets whichever branch is set as `TARGET_BRANCH` in [.github/workflows/deploy.yml](.github/workflows/deploy.yml). Database migrations run automatically when `TARGET_BRANCH` is `CRUD`.

---

## Project Structure

```
.
├── .github/
│   └── workflows/
│       └── deploy.yml              # CI/CD pipeline
├── lambda/
│   └── serverless_web_app/         # Django application
│       ├── config/
│       │   ├── urls.py             # root URL conf
│       │   └── settings/
│       │       ├── base.py         # shared settings + SSM credential fetch
│       │       ├── dev.py          # local development
│       │       └── prod.py         # Lambda production
│       ├── core/                   # main Django app
│       │   ├── models.py           # Item model
│       │   ├── views.py            # CRUD views (HTMX-aware, returns partials)
│       │   ├── forms.py            # ItemForm with Tailwind widgets
│       │   ├── urls.py             # URL patterns
│       │   └── migrations/
│       ├── templates/
│       │   ├── base.html           # Tailwind + HTMX + Alpine layout
│       │   └── core/
│       │       ├── index.html              # items list with Alpine toggle
│       │       ├── item_detail.html
│       │       ├── item_form.html          # fallback full-page form
│       │       ├── item_confirm_delete.html
│       │       └── partials/
│       │           ├── item_row.html       # single item row (HTMX target)
│       │           ├── create_form.html    # inline create form
│       │           └── item_edit_form.html # inline edit form
│       ├── manage.py
│       ├── requirements.txt
│       └── wsgi.py                 # Mangum ASGI Lambda handler
├── terraform-state/                # bootstrap — run once manually
│   ├── dynamodb.tf
│   ├── s3.tf
│   ├── provider.tf
│   ├── variables.tf
│   ├── versions.tf
│   └── outputs.tf
├── apigateway.tf                   # API Gateway v2 + routes
├── cloudwatch.tf                   # CloudWatch log group
├── iam.tf                          # Lambda execution role + SSM read policy
├── lambda.tf                       # Lambda function + zip packaging
├── outputs.tf                      # API URL, function name/ARN
├── provider.tf                     # AWS provider
├── ssm.tf                          # SSM SecureString for database URL
├── variables.tf                    # region, function name, environment, database_url
├── versions.tf                     # Terraform + S3 backend config
├── terraform.tfvars.example        # copy to terraform.tfvars and fill in secrets
└── terraform.tfvars                # real secrets — gitignored
```

---

## Prerequisites

- [Terraform](https://developer.hashicorp.com/terraform/downloads) >= 1.6.0
- [AWS CLI](https://aws.amazon.com/cli/) configured with credentials
- Python 3.12
- A [Neon](https://neon.tech) PostgreSQL database (free tier is sufficient)
- A GitHub repository with Actions enabled

---

## First-Time Setup

### 1. Bootstrap the Terraform state backend

Run this **once** to create the S3 bucket and DynamoDB table that store all future Terraform state.

```bash
cd terraform-state
terraform init
terraform apply
```

> The S3 bucket name (`maangasserverless`) must be globally unique. Change it in
> `terraform-state/variables.tf` and `versions.tf` before running if it conflicts.

### 2. Create terraform.tfvars

```bash
cp terraform.tfvars.example terraform.tfvars
```

Fill in your Neon connection string:

```hcl
database_url = "postgresql://user:password@host.ap-southeast-2.aws.neon.tech/dbname?sslmode=require"
```

This file is gitignored. Terraform stores the URL in AWS SSM Parameter Store as an encrypted `SecureString`. Lambda reads it at cold start via IAM role — the plain-text URL never appears in the console, state output, or CI logs.

### 3. Add GitHub Actions secrets

Go to **Settings → Secrets and variables → Actions** and add:

| Secret | Description |
|--------|-------------|
| `AWS_ACCESS_KEY_ID` | AWS IAM access key |
| `AWS_SECRET_ACCESS_KEY` | AWS IAM secret key |
| `DATABASE_URL` | Neon connection string (used by CI to run migrations) |

The IAM user needs permissions for: Lambda, API Gateway, IAM, CloudWatch Logs, S3, DynamoDB, SSM.

### 4. Push to the CRUD branch

```bash
git push origin CRUD
```

GitHub Actions will install dependencies, run migrations, terraform plan, terraform apply, and print the live API URL.

---

## CI/CD Pipeline

Defined in [.github/workflows/deploy.yml](.github/workflows/deploy.yml).

Set `TARGET_BRANCH` at the top of the file to control which branch triggers a deployment:

```yaml
env:
  TARGET_BRANCH: CRUD  # Switch to 'hello-world' for the minimal app
```

```
push to TARGET_BRANCH
    ├── pip install -r requirements.txt -t lambda/serverless_web_app/
    ├── python manage.py migrate (only when TARGET_BRANCH == 'CRUD')
    ├── terraform init -migrate-state -force-copy
    ├── terraform plan -out=tfplan
    └── terraform apply -auto-approve tfplan
            └── Prints API URL, Lambda ARN, function name

open pull request
    ├── terraform plan
    └── Posts plan output as a PR comment
```

---

## HTMX + Alpine.js Interactions

All CRUD operations run without full page reloads. Django views detect the `HX-Request` header and return HTML partials instead of full pages.

| Action | Mechanism |
|--------|-----------|
| **Create** | Alpine toggles inline form open/closed. HTMX POSTs to `/create/`, server returns `item_row.html` inserted at top of list. `HX-Trigger: itemCreated` header tells Alpine to close the form. |
| **Edit** | Edit button triggers HTMX GET to `/<pk>/edit/`, server returns `item_edit_form.html` which replaces the row in-place. Save POSTs back, server returns the updated row. |
| **Cancel edit** | HTMX GET to `/<pk>/row/` fetches the original row and swaps it back. |
| **Delete** | HTMX POST to `/<pk>/delete/` with a confirm dialog. Server deletes and returns empty — HTMX removes the row from the DOM. |

---

## Database Credentials Flow

```
terraform.tfvars (local, gitignored)
    └── terraform apply
            └── aws_ssm_parameter (SecureString, KMS-encrypted)
                    └── Lambda IAM role (ssm:GetParameter)
                            └── base.py _get_database_url() fetches at cold start
                                    └── dj-database-url parses into DATABASES
```

---

## Local Development

```bash
cd lambda/serverless_web_app
pip install -r requirements.txt
export DATABASE_URL="postgresql://..."
python manage.py migrate
python manage.py runserver
```

Runs with `config.settings.dev` (DEBUG=True, no SSM). Visit `http://localhost:8000`.

---

## Terraform State

| Resource | Name | Purpose |
|----------|------|---------|
| S3 Bucket | `maangasserverless` | Stores `terraform.tfstate` (Intelligent-Tiering) |
| DynamoDB Table | `terraform-state-lock` | Locks state during plan/apply |

**State file path:** `serverless-web-app/terraform.tfstate`

### Clearing a stale lock

```bash
aws dynamodb delete-item \
  --table-name terraform-state-lock \
  --key '{"LockID": {"S": "maangasserverless/serverless-web-app/terraform.tfstate"}}' \
  --region ap-southeast-2
```

---

## Terraform Resources

| File | Resources |
|------|-----------|
| `lambda.tf` | `aws_lambda_function`, `archive_file` (zips Django app) |
| `apigateway.tf` | HTTP API, stage, integration, `$default` catch-all route, Lambda permission |
| `iam.tf` | Lambda execution role, `AWSLambdaBasicExecutionRole`, SSM read policy |
| `ssm.tf` | `aws_ssm_parameter` — database URL as `SecureString` |
| `cloudwatch.tf` | Log group `/aws/lambda/serverless-web-app-dev` (14-day retention) |
| `versions.tf` | Terraform version, providers, S3 backend |
| `variables.tf` | `aws_region`, `lambda_function_name`, `environment`, `database_url` |
| `outputs.tf` | `api_endpoint`, `lambda_function_name`, `lambda_function_arn` |

---

## Key Design Decisions

**Why HTMX + Alpine instead of React/Vue?**
No build step, no bundler, no `node_modules`. Two CDN script tags give you SPA-like interactions — inline forms, in-place edits, no-reload deletes. The server renders HTML fragments; HTMX swaps them into the page. Django stays the source of truth for both data and markup.

**Why Tailwind CDN?**
Serving static files through Lambda means every CSS/JS request triggers a Lambda invocation. CDN scripts load directly in the browser — Lambda is never involved.

**Why SSM Parameter Store for the database URL?**
Plain-text Lambda environment variables are visible in the AWS console and in Terraform state. SSM `SecureString` encrypts the value with KMS. Lambda reads it at cold start using its IAM role — no credentials in the console, no credentials in state output.

**Why `api_gateway_base_path="/dev"` in Mangum?**
API Gateway v2 includes the stage name in the path sent to Lambda (e.g. `/dev/items/`). Mangum strips the prefix so Django sees `/items/` and matches routes correctly.

**Why `FORCE_SCRIPT_NAME = "/dev"` in prod settings?**
Without it, Django's `{% url %}` and `redirect()` generate paths without the stage prefix (e.g. `/items/`), which 404 behind API Gateway. `FORCE_SCRIPT_NAME` prepends `/dev` to every generated URL.

**Why settings split (base/dev/prod)?**
`DJANGO_SETTINGS_MODULE=config.settings.prod` is set on Lambda. Dev settings (DEBUG=True, no SSM) are used locally. Debug output never reaches production.

---

## Environment Variables (Lambda)

| Variable | Value | Description |
|----------|-------|-------------|
| `DJANGO_SETTINGS_MODULE` | `config.settings.prod` | Activates production settings |
| `ENVIRONMENT` | `dev` | Used in `FORCE_SCRIPT_NAME` and SSM parameter path |
| `DJANGO_SECRET_KEY` | *(set in Lambda console or via Terraform)* | Django secret key |
| `SSM_DATABASE_URL_NAME` | `/serverless-web-app/dev/database-url` | SSM path — Lambda fetches DB URL from here |

---

## Estimated AWS Costs

| Service | Free Tier | Cost after free tier |
|---------|-----------|----------------------|
| Lambda | 1M requests/mo | ~$0.20 per 1M requests |
| API Gateway | 1M requests/mo | ~$1.00 per 1M requests |
| CloudWatch Logs | 5GB ingestion | ~$0.50/GB |
| S3 (state) | Minimal | < $0.01/mo |
| DynamoDB (lock) | 25GB + 200M requests | $0 for this use case |
| SSM Parameter Store | 10,000 API calls/mo | $0 for this use case |
| Neon PostgreSQL | 0.5GB storage | $0 on free tier |
