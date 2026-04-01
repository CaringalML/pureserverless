# Serverless Web App

A full Django web application running on AWS Lambda, provisioned with Terraform and deployed automatically via GitHub Actions CI/CD. No servers to manage — push to `main` and it deploys itself.

**Live stack:** Django 5 → Mangum (ASGI) → AWS Lambda → API Gateway v2 → Sydney (`ap-southeast-2`)

---

## Architecture

```
Browser
  └── API Gateway v2 (HTTP API, $default catch-all route)
        └── Lambda (Python 3.12 — Django + Mangum)
              ├── Tailwind CSS (loaded from CDN, no Lambda cost)
              └── CloudWatch Logs (/aws/lambda/serverless-web-app-dev)

Terraform Remote State
  ├── S3 Bucket (maangasserverless) — Intelligent-Tiering storage
  └── DynamoDB Table (terraform-state-lock) — state locking
```

---

## Project Structure

```
.
├── .github/
│   └── workflows/
│       └── deploy.yml          # CI/CD pipeline
├── lambda/
│   └── serverless_web_app/     # Django application
│       ├── config/
│       │   ├── urls.py         # root URL conf
│       │   └── settings/
│       │       ├── base.py     # shared settings
│       │       ├── dev.py      # local development
│       │       └── prod.py     # Lambda production
│       ├── core/               # main Django app
│       │   ├── apps.py
│       │   ├── urls.py
│       │   └── views.py
│       ├── templates/
│       │   ├── base.html       # Tailwind layout
│       │   └── core/
│       │       └── index.html
│       ├── manage.py
│       ├── requirements.txt    # django, mangum
│       └── wsgi.py             # Mangum ASGI Lambda handler
├── terraform-state/            # bootstrap — run once manually
│   ├── dynamodb.tf             # state lock table
│   ├── s3.tf                   # state bucket
│   ├── provider.tf
│   ├── variables.tf
│   ├── versions.tf
│   └── outputs.tf
├── apigateway.tf               # API Gateway v2 + routes
├── cloudwatch.tf               # CloudWatch log group
├── iam.tf                      # Lambda execution role
├── lambda.tf                   # Lambda function + zip packaging
├── outputs.tf                  # API URL, function name/ARN
├── provider.tf                 # AWS provider
├── variables.tf                # region, function name, environment
└── versions.tf                 # Terraform + S3 backend config
```

---

## Prerequisites

- [Terraform](https://developer.hashicorp.com/terraform/downloads) >= 1.6.0
- [AWS CLI](https://aws.amazon.com/cli/) configured with credentials
- Python 3.12
- A GitHub repository with Actions enabled

---

## First-Time Setup

### 1. Bootstrap the Terraform state backend

This only needs to be done **once**. It creates the S3 bucket and DynamoDB table that store all future Terraform state.

```bash
cd terraform-state
terraform init
terraform apply
```

> The S3 bucket name (`maangasserverless`) must be globally unique. Change it in
> [terraform-state/variables.tf](terraform-state/variables.tf) and [versions.tf](versions.tf)
> before running if it conflicts.

### 2. Add GitHub Actions secrets

Go to your repo → **Settings → Secrets and variables → Actions** and add:

| Secret | Description |
|--------|-------------|
| `AWS_ACCESS_KEY_ID` | AWS IAM access key |
| `AWS_SECRET_ACCESS_KEY` | AWS IAM secret key |

The IAM user needs permissions for: Lambda, API Gateway, IAM, CloudWatch Logs, S3, DynamoDB.

### 3. Push to main

```bash
git push origin main
```

GitHub Actions will:
1. Install Python dependencies into the Lambda source folder
2. Zip the Django app
3. Run `terraform init` (restoring providers from cache)
4. Run `terraform plan`
5. Run `terraform apply` — deploys Lambda + API Gateway
6. Print the API endpoint URL in the job logs

---

## CI/CD Pipeline

Defined in [.github/workflows/deploy.yml](.github/workflows/deploy.yml).

```
push to main
    ├── Install Python deps (pip install -r requirements.txt -t lambda/serverless_web_app/)
    ├── Restore Terraform provider cache (skips 600MB download if lock file unchanged)
    ├── terraform init -migrate-state -force-copy
    ├── terraform validate
    ├── terraform plan -out=tfplan
    └── terraform apply -auto-approve tfplan
            └── Prints DEPLOYMENT OUTPUTS (API URL, Lambda ARN, function name)

open pull request
    ├── terraform plan
    └── Posts plan output as a PR comment
```

**Provider caching:** The `.terraform/` directory is cached keyed on `versions.tf` + `.terraform.lock.hcl`. Providers are only re-downloaded when you change a provider version — all other runs skip the download entirely.

---

## Local Development

```bash
cd lambda/serverless_web_app
pip install -r requirements.txt
python manage.py runserver
```

Runs with `config.settings.dev` (DEBUG=True). Visit `http://localhost:8000`.

---

## Adding a New Page

1. Add a URL in [lambda/serverless_web_app/core/urls.py](lambda/serverless_web_app/core/urls.py)
2. Add a view in [lambda/serverless_web_app/core/views.py](lambda/serverless_web_app/core/views.py)
3. Add a template in [lambda/serverless_web_app/templates/core/](lambda/serverless_web_app/templates/core/)
4. Push to `main` — GitHub Actions deploys it automatically

---

## Adding Python Dependencies

Add packages to [lambda/serverless_web_app/requirements.txt](lambda/serverless_web_app/requirements.txt):

```
django==5.0.4
mangum==0.17.0
requests==2.31.0   # example
```

Push to `main`. The GitHub Actions runner installs all packages into the Lambda folder and bundles them into the zip — no local packaging needed.

---

## Terraform State

State is stored remotely so it is never lost and concurrent applies are prevented.

| Resource | Name | Purpose |
|----------|------|---------|
| S3 Bucket | `maangasserverless` | Stores `terraform.tfstate` |
| DynamoDB Table | `terraform-state-lock` | Locks state during plan/apply |

**State file path in S3:** `serverless-web-app/terraform.tfstate`

**Storage class:** S3 Intelligent-Tiering — automatically moves state files to cheaper tiers during inactive periods, with no retrieval penalties.

### If a pipeline gets stuck and leaves a stale lock

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
| `iam.tf` | Lambda execution role + `AWSLambdaBasicExecutionRole` policy |
| `cloudwatch.tf` | Log group `/aws/lambda/serverless-web-app-dev` (14-day retention) |
| `versions.tf` | Terraform version, providers, S3 backend |
| `variables.tf` | `aws_region`, `lambda_function_name`, `environment` |
| `outputs.tf` | `api_endpoint`, `lambda_function_name`, `lambda_function_arn` |

---

## Key Design Decisions

**Why Mangum?**
Mangum is an ASGI adapter that translates API Gateway's event format into Django's ASGI interface, allowing Django to run as a Lambda handler without modification.

**Why `$default` catch-all route?**
A single `$default` route forwards all methods and paths to Lambda. Django's URL router handles routing internally — this avoids having to define an API Gateway route for every Django URL.

**Why Tailwind CDN instead of WhiteNoise?**
Serving static files through Lambda means every CSS/JS request triggers a Lambda invocation and adds cold start latency. Tailwind CDN loads directly from the internet in the browser — Lambda is never involved.

**Why settings split (base/dev/prod)?**
`DJANGO_SETTINGS_MODULE=config.settings.prod` is set as a Lambda environment variable. Dev settings (DEBUG=True) are used locally via `manage.py`. This prevents debug output from ever reaching production.

**Why `api_gateway_base_path="/dev"`?**
API Gateway v2 includes the stage name (`dev`) in the path it sends to Lambda (e.g. `/dev/`). Mangum's `api_gateway_base_path` strips the prefix so Django sees `/` and matches routes correctly.

---

## Environment Variables (Lambda)

| Variable | Value | Description |
|----------|-------|-------------|
| `DJANGO_SETTINGS_MODULE` | `config.settings.prod` | Activates production settings |
| `ENVIRONMENT` | `dev` | Passed to Django as a template/logic variable |
| `DJANGO_SECRET_KEY` | *(set manually in Lambda console or via Terraform variable)* | Django secret key |

---

## Estimated AWS Costs

This stack is extremely low cost for a personal or small project:

| Service | Free Tier | Typical cost after |
|---------|-----------|-------------------|
| Lambda | 1M requests/mo free | ~$0.20 per 1M requests |
| API Gateway | 1M requests/mo free | ~$1.00 per 1M requests |
| CloudWatch Logs | 5GB ingestion free | ~$0.50/GB |
| S3 (state) | Minimal — state files are KB-sized | < $0.01/mo |
| DynamoDB (lock) | 25GB + 200M requests free | $0 for this use case |
