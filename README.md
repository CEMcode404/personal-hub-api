# Personal Hub API

A serverless backend for my personal hub: content publishing, todos with scheduled reminders, a wiki, research notes, and real-time notifications.

> **Status:** Archived. This project is no longer deployed or maintained. It's kept public as a reference project.

## Tech Stack

- **Runtime** — Python 3.13
- **API** — API Gateway (HTTP + WebSocket), Lambda
- **Auth** — Cognito with mandatory TOTP MFA
- **Data** — DynamoDB, S3
- **Scheduling & notifications** — EventBridge Scheduler, SNS
- **Edge** — CloudFront, WAF, ACM
- **Infrastructure** — AWS SAM, CloudFormation
- **Local Development** — Docker, DynamoDB Local, LocalStack (S3)

## Prerequisites

- [Python 3.13](https://www.python.org/downloads/)
- [AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html)
- [Docker](https://www.docker.com/products/docker-desktop/)
- [AWS CLI](https://aws.amazon.com/cli/) configured with `personal-hub` profile

## Local Development

### First Time Setup

1. Clone the repo

```bash
git clone <repo-url>
cd personal-hub-api
```

2. Install dependencies

```bash
pip install -r requirements-dev.txt
```

3. Copy the env file and fill in values

```bash
cp env.local.example.json env.local.json
```

4. Start the local environment

```bash
make local
```

This will:

- Build the Lambda function
- Start DynamoDB Local and LocalStack (S3) in Docker
- Create the required tables and media bucket
- Start the local API at `http://localhost:8080` (authorizers are disabled locally)

### Running Tests

```bash
pytest
```

### Available Commands

| Command       | Description                                                                       |
| ------------- | --------------------------------------------------------------------------------- |
| `make local`  | Start the full local dev environment                                              |
| `make stop`   | Stop all local services (data is preserved)                                       |
| `make reset`  | Stop all local services and wipe all data                                         |
| `make setup`  | Create local DynamoDB tables and S3 bucket (runs automatically with `make local`) |
| `make reload` | Rebuild without cache and restart the local environment (data is preserved)       |
| `make deploy` | Deploy to prod                                                                    |

## Deployment

### First Time — WAF Setup

The WAF stack must be deployed once before the main backend. It creates the origin secret used to restrict API Gateway access to CloudFront only.

```bash
./deploy-waf.sh
```

This will:

- Generate a random secret and store it in SSM Parameter Store (`ap-southeast-1`)
- Deploy the WAF Web ACL to `us-east-1` with rate limiting and AWS managed rules (common exploits, known bad inputs)

### First Time — Backend

Create the required SSM parameters first:

| Parameter                           | Description                     |
| ----------------------------------- | ------------------------------- |
| `/personal-hub/notify-phone-number` | Phone number for SMS reminders  |
| `/personal-hub/allowed-origin`      | Frontend origin for CORS        |
| `/personal-hub/media-bucket-name`   | S3 bucket for uploaded media    |
| `/personal-hub/media-cdn-domain`    | CloudFront domain serving media |

Then deploy:

```bash
sam build
sam deploy --guided
```

Follow the prompts — SAM will create the required S3 bucket and save your config to `samconfig.toml`.

After deploying, create your admin user in Cognito and run `./manage-mfa.sh` to set up MFA.

### Subsequent Deploys

```bash
sam build
sam deploy
```

Or using the make command:

```bash
make deploy
```

### Environments

Deployment targets are configured in `samconfig.toml`. The default deploys to `ap-southeast-1` (Singapore).

## Security

| Layer                | Protection                                               |
| -------------------- | -------------------------------------------------------- |
| WAF on CloudFront    | Common exploits, known bad inputs, rate limiting at edge |
| Origin secret header | Only CloudFront can call API Gateway directly            |
| Lambda authorizer    | Validates secret header before invoking business logic   |
| Cognito              | JWT authentication with mandatory TOTP MFA               |
| DynamoDB IAM         | Lambda only has access to its own tables                 |

## Infrastructure Security Audit

Uses [Prowler](https://github.com/prowler-cloud/prowler) for periodic AWS security checks.

### Setup

```bash
pip install prowler-cloud
```

### Run

```bash
ulimit -n 4096 && prowler aws --region ap-southeast-1
```

Reports are saved to `output/` as HTML, CSV, and JSON.

### What to fix vs ignore

| Severity | Action                             |
| -------- | ---------------------------------- |
| Critical | Fix immediately                    |
| High     | Fix soon                           |
| Medium   | Review — many are compliance noise |
| Low      | Ignore for personal project        |

Known acceptable findings for this project:

- CloudWatch metric filter alarms — compliance requirement, overkill for personal use
- DynamoDB CMK encryption — default AWS encryption is sufficient
- IAM password policy — single user account, not applicable
- VPC single region — intentional, single region deployment

## Project Structure

```
src/
├── handlers/          # HTTP layer — routes and request/response handling
│   └── authorizer.py  # CloudFront origin secret validator
├── services/          # Business logic
├── repositories/      # Database operations
├── models/            # Data models
├── schemas/           # Request body validation
├── utils/             # Shared utilities
├── db.py              # DynamoDB connection
├── main.py            # Lambda handler entry point
└── router.py          # Route registration
tests/                 # Unit tests
template.yaml          # Main SAM template (API, Lambda, DynamoDB, Cognito)
waf-template.yaml      # WAF CloudFormation stack (us-east-1)
deploy-waf.sh          # WAF deploy script
manage-mfa.sh          # Cognito MFA setup and recovery
docker-compose.yml     # Local DynamoDB and LocalStack
Makefile               # Local dev commands
samconfig.toml         # SAM deployment configuration
requirements.txt       # Production dependencies
requirements-dev.txt   # Development and test dependencies
```