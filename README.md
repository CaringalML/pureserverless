# StrawDrive

A Google Drive-like file storage web app running on AWS Lambda — fully serverless, no EC2, no servers to manage. Push to `strawdrive` and it deploys itself.

**Live stack:** Django 5 → Mangum → AWS Lambda → API Gateway v2 → CloudFront → S3  
**Auth:** AWS Cognito (signup, email verify, signin, forgot/reset password)  
**Domain:** `drive.nodepulsecaringal.xyz` (custom domain via ACM + Cloudflare + API Gateway)  
**Region:** Sydney (`ap-southeast-2`)

---

## Architecture

```
Browser (drive.nodepulsecaringal.xyz)
  └── Cloudflare (proxied — DDoS protection, hides AWS URL)
        └── API Gateway v2 (HTTP API, custom domain, $default catch-all)
              └── Lambda (Python 3.12 — Django 5 + Mangum)
                    ├── Cognito (signup, verify, signin, forgot/reset password)
                    ├── Neon PostgreSQL (file metadata — credentials via SSM)
                    ├── S3 (file storage — private, versioned)
                    │     └── Direct browser upload via presigned POST URL
                    │         (file bytes never pass through Lambda)
                    ├── CloudFront (signed URLs — only way to read files from S3)
                    ├── Tailwind CSS / HTMX / Alpine.js (CDN — no build step)
                    └── CloudWatch Logs + SNS alerts (4xx + spike alarms)

Terraform Remote State
  ├── S3 Bucket (maangasserverless) — Intelligent-Tiering
  └── DynamoDB Table (terraform-state-lock) — state locking
```

### Upload flow

```
1. Browser → Lambda: "give me a presigned POST URL"
2. Lambda → Browser: { url, fields, s3_key }   (signed by IAM, 5-min TTL)
3. Browser → S3: POST directly with file + fields  (XHR for progress events)
4. Browser → Lambda: "confirm upload for s3_key"
5. Lambda → S3: head_object (verify it landed)
6. Lambda → DB: save DriveFile metadata row
7. Browser: file row appears in the list
```

### View / download flow

```
1. Browser → Lambda: GET /files/<id>/view/
2. Lambda → SSM: fetch CloudFront private key (cached after first cold start)
3. Lambda → sign URL with RSA key (1-hour expiry)
4. Browser: 302 redirect to signed CloudFront URL
5. Browser → CloudFront → S3: serves the file
```

---

## Branches

| Branch | Description |
|--------|-------------|
| `hello-world` | Minimal Django hello world page |
| `CRUD` | Django CRUD with HTMX inline edits |
| `auth` | AWS Cognito authentication — signup, verify, signin, dashboard, forgot/reset password |
| `strawdrive` | **Current** — full file storage app (S3 + CloudFront + Cognito + custom domain) |

The CI/CD pipeline triggers on pushes to `strawdrive`. See [.github/workflows/deploy.yml](.github/workflows/deploy.yml).

---

## Project Structure

```
.
├── .github/
│   └── workflows/
│       └── deploy.yml              # CI/CD pipeline (triggers on strawdrive branch)
├── lambda/
│   └── serverless_web_app/         # Django application
│       ├── config/
│       │   ├── urls.py
│       │   └── settings/
│       │       ├── base.py         # shared settings, SSM fetch, StrawDrive config
│       │       ├── dev.py          # local dev (DEBUG=True, no SSM)
│       │       └── prod.py         # Lambda prod (secure headers, CSRF origins)
│       ├── accounts/               # Cognito auth app
│       │   ├── views.py            # signup, verify, signin, signout, forgot/reset
│       │   ├── forms.py            # SignUpForm, SignInForm, ForgotPasswordForm, ResetPasswordForm
│       │   └── urls.py
│       ├── drive/                  # StrawDrive app
│       │   ├── models.py           # DriveFile (owner_sub, name, s3_key, size, content_type, storage_class)
│       │   ├── views.py            # upload_url, confirm_upload, view_file, delete_file, archive_files
│       │   ├── urls.py
│       │   └── migrations/
│       ├── templates/
│       │   ├── base.html           # StrawDrive layout + avatar dropdown
│       │   ├── accounts/           # signup, verify, signin, forgot/reset templates
│       │   └── drive/
│       │       └── home.html       # file list + XHR upload with progress bar
│       ├── manage.py
│       ├── requirements.txt
│       └── wsgi.py                 # Mangum handler
├── terraform-state/                # run once manually to bootstrap state backend
├── apigateway.tf                   # HTTP API, stage (throttling), $default route
├── cloudfront_drive.tf             # CloudFront distribution (signed URLs required)
├── cloudfront_keys.tf              # RSA key pair for CloudFront URL signing
├── cloudwatch.tf                   # Log group, 4xx alarm, spike alarm
├── cognito.tf                      # Cognito User Pool + App Client
├── custom_domain.tf                # ACM cert + API Gateway custom domain
├── iam.tf                          # Lambda execution role + policies
├── lambda.tf                       # Lambda function + env vars
├── outputs.tf                      # API URL, Cognito IDs, Cloudflare CNAME targets
├── provider.tf
├── s3_drive.tf                     # Drive bucket (private, versioned, lifecycle)
├── sns.tf                          # SNS topic + email subscription
├── ssm.tf                          # SSM SecureString for DB URL
├── variables.tf
├── versions.tf                     # Terraform version + S3 backend
└── terraform.tfvars                # secrets — gitignored
```

---

## File Storage — S3 Lifecycle Tiers

StrawDrive automatically moves files through cheaper storage tiers as they age:

| Tier | Trigger | Retrieval | Use case |
|------|---------|-----------|----------|
| **Standard** | Upload | Instant | Active files |
| **Standard-IA** | 30 days (automatic) | Instant | Less-accessed files |
| **Glacier Instant Retrieval** | 90 days (automatic) | Instant | Rarely accessed |
| **Glacier Flexible** | User-triggered archive | 3–5 hours | Long-term archive |
| **Deep Archive** | User-triggered archive | 12 hours | Coldest storage, lowest cost |

User-triggered archiving uses S3 copy-in-place (copy object back to itself with a new `StorageClass`) — no data movement or download required.

---

## Custom Domain Setup

This is how `drive.nodepulsecaringal.xyz` was configured — no Route 53 needed because the domain is already on Cloudflare.

### How it works

```
Cloudflare DNS (proxied)
  └── CNAME drive → <api-gateway-regional-domain>.execute-api.ap-southeast-2.amazonaws.com
        └── API Gateway custom domain (TLS terminated by ACM cert)
              └── API mapping → serverless_web_app stage (no /dev prefix)
```

Cloudflare's proxy sits in front, providing DDoS protection and hiding the raw AWS URL.

### Step-by-step process

#### Step 1 — Run `terraform apply`

Terraform creates the ACM certificate and the API Gateway custom domain. After apply, read the outputs:

```bash
terraform output acm_validation_cname_name   # e.g. _abc123.drive.nodepulsecaringal.xyz
terraform output acm_validation_cname_value  # e.g. _xyz789.acm-validations.aws.
terraform output cloudflare_cname_target     # e.g. d-xxxxxx.execute-api.ap-southeast-2.amazonaws.com
```

#### Step 2 — Add ACM validation CNAME in Cloudflare (proxy OFF)

In Cloudflare DNS, add a CNAME record:

| Field | Value |
|-------|-------|
| Type | CNAME |
| Name | `_abc123.drive` (the part before your root domain) |
| Target | `_xyz789.acm-validations.aws.` |
| Proxy | **DNS only** (grey cloud) |

ACM needs to see the raw DNS record to validate ownership. If Cloudflare proxies it, ACM cannot reach it.

Wait for the certificate to become `Issued` — this takes 2–30 minutes once the record is live.

```bash
aws acm describe-certificate --certificate-arn <arn> --region ap-southeast-2 \
  --query 'Certificate.Status'
# "ISSUED" means you're good to proceed
```

#### Step 3 — Add the final drive CNAME in Cloudflare (proxy ON)

Once the cert is `Issued`, add the main CNAME:

| Field | Value |
|-------|-------|
| Type | CNAME |
| Name | `drive` |
| Target | value from `terraform output cloudflare_cname_target` |
| Proxy | **Proxied** (orange cloud) |

Proxy ON gives you Cloudflare's DDoS protection and hides the raw AWS URL from public DNS lookups.

#### Step 4 — Done

Visit `https://drive.nodepulsecaringal.xyz`. The TLS certificate is from Let's Encrypt (Cloudflare's edge cert), and your ACM cert handles the Cloudflare → AWS leg.

### Why no `/dev` prefix in URLs

`aws_apigatewayv2_api_mapping` maps the custom domain at the root (`/`), not at a stage prefix. API Gateway strips the stage name before passing the request to Lambda. `FORCE_SCRIPT_NAME` and `api_gateway_base_path` are not needed and have been removed.

---

## Prerequisites

- [Terraform](https://developer.hashicorp.com/terraform/downloads) >= 1.6.0
- [AWS CLI](https://aws.amazon.com/cli/) configured with credentials
- Python 3.12
- A [Neon](https://neon.tech) PostgreSQL database (free tier is sufficient)
- A domain on Cloudflare (or any DNS provider that supports CNAME records)
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

Fill in your values:

```hcl
database_url  = "postgresql://user:password@host.ap-southeast-2.aws.neon.tech/dbname?sslmode=require"
custom_domain = "drive.yourdomain.com"
```

`database_url` is gitignored. Terraform stores it in SSM Parameter Store as an encrypted `SecureString`. Lambda reads it at cold start via IAM role — the plain-text URL never appears in the console or CI logs.

### 3. Add GitHub Actions secrets

Go to **Settings → Secrets and variables → Actions** and add:

| Secret | Description |
|--------|-------------|
| `AWS_ACCESS_KEY_ID` | AWS IAM access key |
| `AWS_SECRET_ACCESS_KEY` | AWS IAM secret key |
| `DATABASE_URL` | Neon connection string (used by CI to run migrations) |

The IAM user needs permissions for: Lambda, API Gateway, IAM, CloudWatch Logs, S3, DynamoDB, SSM, Cognito, CloudFront, ACM, SNS.

### 4. Push to the strawdrive branch

```bash
git push origin strawdrive
```

GitHub Actions will: install dependencies → run migrations → terraform plan → terraform apply.

After the first deploy, follow the **Custom Domain Setup** steps above to configure DNS.

### 5. Confirm your SNS subscription

AWS sends a confirmation email to `lawrencecaringal5@gmail.com` after the first deploy. Click **Confirm subscription** or no alerts will be delivered.

---

## CI/CD Pipeline

Defined in [.github/workflows/deploy.yml](.github/workflows/deploy.yml). Triggers on push to `strawdrive`.

```
push to strawdrive
    ├── pip install -r requirements.txt -t lambda/serverless_web_app/  (for Lambda zip)
    ├── pip install -r requirements.txt                                 (for manage.py migrate)
    ├── python manage.py migrate
    ├── terraform init
    ├── terraform plan -out=tfplan
    └── terraform apply -auto-approve tfplan
```

---

## Authentication (Cognito)

StrawDrive uses AWS Cognito with the `USER_PASSWORD_AUTH` flow. No third-party auth libraries — direct Cognito API calls via boto3.

| Route | Description |
|-------|-------------|
| `/signup/` | Creates Cognito user, triggers verification email |
| `/verify/` | Submits 6-digit code from email |
| `/signin/` | Authenticates, stores tokens in Django session |
| `/signout/` | Clears session |
| `/forgot-password/` | Sends reset code to email |
| `/reset-password/` | Submits code + new password |

After signin, tokens are stored in the Django session (`access_token`, `refresh_token`, `user_sub`, `user_email`). All drive routes are protected by the `cognito_login_required` decorator.

The Cognito App Client has `generate_secret = false` — no client secret is needed. Auth is enforced by the IAM role on Lambda.

---

## Drive Features

| Feature | How it works |
|---------|-------------|
| **Upload** | Browser gets presigned POST URL from Lambda, uploads directly to S3 via XHR (progress bar). Lambda confirms via `head_object` and saves metadata to DB. |
| **View / Download** | Lambda generates a 1-hour CloudFront signed URL and redirects the browser. Files are never proxied through Lambda. |
| **Delete** | S3 object deleted, DB row deleted. HTMX removes the row from the DOM with no page reload. |
| **Archive** | S3 copy-in-place to `GLACIER` or `DEEP_ARCHIVE`. DB storage_class updated. HTMX updates the row in-place. |
| **Multiple archive** | Select checkboxes, click archive — all selected files sent in one request, all updated atomically. |

### CloudFront signed URLs

Files are not publicly accessible. Every `GET /files/<id>/view/` request:
1. Checks the session (`cognito_login_required`)
2. Verifies the file belongs to the authenticated user
3. Signs a CloudFront URL with the RSA private key (stored in SSM SecureString, loaded at cold start)
4. Redirects the browser to the signed URL (1-hour expiry)

The RSA key pair is generated by the Terraform `tls` provider on first `terraform apply`. The private key goes into SSM; the public key is registered with CloudFront as a key group. Anonymous requests to CloudFront are denied.

---

## Rate Limiting

API Gateway stage throttling in [apigateway.tf](apigateway.tf):

```hcl
throttling_rate_limit  = 100   # max sustained requests/sec
throttling_burst_limit = 200   # max requests during a spike
```

Requests exceeding limits receive `429 Too Many Requests` from API Gateway — Lambda is never invoked, the database is never touched, you are never billed for excess traffic.

---

## Alerting

SNS email alerts to `lawrencecaringal5@gmail.com`. Defined in [sns.tf](sns.tf) and [cloudwatch.tf](cloudwatch.tf).

| Alarm | Metric | Threshold | Signal |
|-------|--------|-----------|--------|
| `4xx-errors` | `4XXError` (API Gateway) | > 50 in 1 min | 429s firing — attacker is being blocked |
| `request-spike` | `Count` (API Gateway) | > 500 in 1 min | High volume before throttling kicks in |

Both alarms send a recovery email when traffic returns to normal.

---

## Database Credentials Flow

```
terraform.tfvars (local, gitignored)
    └── terraform apply
            └── aws_ssm_parameter (SecureString, KMS-encrypted)
                    └── Lambda IAM role (ssm:GetParameter)
                            └── base.py fetches at cold start
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

Runs with `config.settings.dev` (DEBUG=True, no SSM, no Cognito calls needed for local).

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
| `apigateway.tf` | HTTP API, stage (throttling), $default catch-all route, Lambda permission |
| `cognito.tf` | User Pool, App Client (no secret, `USER_PASSWORD_AUTH`) |
| `custom_domain.tf` | ACM certificate (DNS validation), API Gateway custom domain + API mapping |
| `s3_drive.tf` | Drive S3 bucket (private, versioned, lifecycle tiers, CORS, OAC bucket policy) |
| `cloudfront_drive.tf` | CloudFront distribution (OAC origin, signed URLs enforced via key group) |
| `cloudfront_keys.tf` | RSA key pair (`tls_private_key`), SSM SecureString, CloudFront public key + key group |
| `sns.tf` | SNS topic + email subscription |
| `cloudwatch.tf` | Log group (14-day retention), 4xx alarm, request spike alarm |
| `iam.tf` | Lambda execution role, `AWSLambdaBasicExecutionRole`, SSM read policy, S3 + CloudFront policies |
| `ssm.tf` | `aws_ssm_parameter` — database URL as `SecureString` |
| `variables.tf` | `aws_region`, `lambda_function_name`, `environment`, `database_url`, `custom_domain` |
| `outputs.tf` | API URL, Cognito IDs, drive bucket, CloudFront domain, ACM validation CNAMEs |

---

## Environment Variables (Lambda)

| Variable | Source | Description |
|----------|--------|-------------|
| `DJANGO_SETTINGS_MODULE` | `lambda.tf` | `config.settings.prod` |
| `ENVIRONMENT` | `lambda.tf` | `dev` |
| `SSM_DATABASE_URL_NAME` | `lambda.tf` | SSM path for DB URL |
| `COGNITO_USER_POOL_ID` | `lambda.tf` | Cognito User Pool ID |
| `COGNITO_CLIENT_ID` | `lambda.tf` | Cognito App Client ID |
| `DRIVE_BUCKET_NAME` | `lambda.tf` | S3 bucket for file storage |
| `CLOUDFRONT_DOMAIN` | `lambda.tf` | CloudFront domain for signing URLs |
| `CLOUDFRONT_KEY_PAIR_ID` | `lambda.tf` | CloudFront public key ID (for signing) |
| `CLOUDFRONT_PRIVATE_KEY_SSM_NAME` | `lambda.tf` | SSM path for RSA private key |
| `ALLOWED_HOSTS` | `lambda.tf` | `drive.nodepulsecaringal.xyz` |
| `CSRF_TRUSTED_ORIGINS` | `lambda.tf` | `https://drive.nodepulsecaringal.xyz` |

---

## Key Design Decisions

**Why direct S3 upload instead of proxying through Lambda?**
API Gateway has a 6MB payload limit. Lambda proxying large files would hit that immediately. Presigned POST URLs let the browser upload directly to S3 — Lambda only generates the URL and confirms afterward. File bytes never touch Lambda.

**Why XHR instead of fetch() for uploads?**
The Fetch API does not expose upload progress events. `XMLHttpRequest` has `xhr.upload.addEventListener('progress', ...)` which fires as bytes are sent, enabling the progress bar.

**Why read CSRF token from `<meta>` instead of cookie?**
`SESSION_COOKIE_HTTPONLY = True` means JavaScript cannot read HttpOnly cookies. The CSRF token is written into a `<meta name="csrf-token">` tag in the base template so Alpine.js can read it safely.

**Why CloudFront signed URLs?**
The S3 bucket is fully private — no public access at all. CloudFront is the only way to read objects (via OAC). Signed URLs add a second layer: even CloudFront URLs expire after 1 hour and are tied to the user's authenticated session. There is no way for a user to share or bookmark a permanent link to someone else's file.

**Why SSM SecureString for the CloudFront private key?**
The RSA private key grants the ability to sign CloudFront URLs for all files in the bucket. Storing it as a Lambda environment variable would expose it in the AWS console. SSM SecureString encrypts it with KMS and Lambda reads it at cold start using its IAM role.

**Why Cloudflare proxy ON for the final CNAME?**
With proxy ON, Cloudflare acts as a reverse proxy — public DNS returns Cloudflare's IPs, not the raw API Gateway domain. This provides DDoS protection at Cloudflare's edge and hides the underlying AWS infrastructure from DNS lookups.

**Why proxy OFF for the ACM validation CNAME?**
ACM validates certificate ownership by resolving a specific CNAME record and expecting a raw DNS answer. If Cloudflare proxies the validation record, ACM sees Cloudflare's IP instead of the expected value and validation fails. The record must be DNS only (grey cloud) until the certificate is issued, after which it can be left or removed.

**Why no Route 53?**
Route 53 costs $0.50/hosted zone/month. The domain is already on Cloudflare's free plan. Cloudflare supports CNAME records pointing to API Gateway regional endpoints directly. ACM DNS validation works fine with any DNS provider that supports CNAME records.

**Why `generate_secret = false` on the Cognito App Client?**
Mobile and SPA clients cannot safely store a client secret. Since Lambda handles all auth calls server-side via IAM role, there is no need for a client secret — Cognito trusts the call because Lambda has the correct IAM permissions.

**Why settings split (base/dev/prod)?**
`DJANGO_SETTINGS_MODULE=config.settings.prod` is set on Lambda. `prod.py` enables secure headers, CSRF origins, and secure session cookies. `dev.py` uses `DEBUG=True` locally without touching SSM or Cognito. Debug output never reaches production.

---

## Estimated AWS Costs

| Service | Free Tier | After free tier |
|---------|-----------|-----------------|
| Lambda | 1M requests/mo | ~$0.20/1M requests |
| API Gateway | 1M requests/mo | ~$1.00/1M requests |
| CloudFront | 1TB transfer + 10M requests/mo | ~$0.0085/GB transfer |
| S3 Storage | 5GB | ~$0.025/GB/mo (Standard) |
| S3 Glacier IR | — | ~$0.004/GB/mo |
| S3 Glacier Flexible | — | ~$0.0036/GB/mo |
| S3 Deep Archive | — | ~$0.00099/GB/mo |
| Cognito | 50,000 MAU | $0.0055/MAU after |
| ACM Certificate | Free | Always free |
| CloudWatch Logs | 5GB ingestion | ~$0.50/GB |
| SSM Parameter Store | 10,000 API calls/mo | $0 for standard parameters |
| SNS | 1,000 email notifications/mo | ~$2.00/100,000 after |
| S3 (state) | Minimal | < $0.01/mo |
| DynamoDB (lock) | 25GB + 200M requests | $0 for this use case |
| Neon PostgreSQL | 0.5GB | $0 on free tier |
