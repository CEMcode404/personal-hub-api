# Personal Hub API

A serverless REST API backend for my personal hub — starting with content management, built to expand into other personal apps over time.

## Tech Stack

- **Runtime** — Python 3.13
- **Infrastructure** — AWS SAM (Lambda + API Gateway + DynamoDB + WAF)
- **Local Development** — Docker + DynamoDB Local

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

2. Copy the env file and fill in values

```bash
   cp env.local.example.json env.local.json
```

3. Start the local environment

```bash
   make local
```

This will:

- Build the Lambda function
- Start DynamoDB Local in Docker
- Create the required tables
- Start the local API at `http://localhost:3000`

### Available Commands

| Command       | Description                                                |
| ------------- | ---------------------------------------------------------- |
| `make local`  | Start the full local dev environment                       |
| `make stop`   | Stop all local services (data is preserved)                |
| `make reset`  | Stop all local services and wipe all data                  |
| `make setup`  | Create DynamoDB tables (run once after first `make local`) |
| `make reload` | Reload the page to reflect the new changes                 |
| `make deploy` | Deploy to prod                                             |

## Deployment

### First Time — WAF Setup

The WAF stack must be deployed once before the main backend. It creates the origin secret used to restrict API Gateway access to CloudFront only.

```bash
./deploy-waf.sh
```

This will:

- Generate a random secret and store it in SSM Parameter Store (`us-east-1` and `ap-southeast-1`)
- Deploy the WAF Web ACL to `us-east-1` with rate limiting and AWS managed rules (XSS, SQLi)

### First Time — Backend

```bash
sam build
sam deploy --guided
```

Follow the prompts — SAM will create the required S3 bucket and save your config to `samconfig.toml`.

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

| Layer                | Protection                                             |
| -------------------- | ------------------------------------------------------ |
| WAF on CloudFront    | XSS, SQLi, rate limiting at edge                       |
| Origin secret header | Only CloudFront can call API Gateway directly          |
| Lambda authorizer    | Validates secret header before invoking business logic |
| Cognito              | JWT authentication for admin endpoints                 |
| DynamoDB IAM         | Lambda only has access to its own tables               |

## Project Structure

```
src/
├── handlers/       # HTTP layer — routes and request/response handling
│   └── authorizer.py  # CloudFront origin secret validator
├── services/       # Business logic
├── repositories/   # Database operations
├── models/         # Data models
├── schemas/        # Request body validation
├── utils/          # Shared utilities
├── db.py           # DynamoDB connection
├── main.py         # Lambda handler entry point
└── router.py       # Route registration
waf-template.yaml   # WAF CloudFormation stack (us-east-1)
deploy-waf.sh       # WAF deploy script
```
