.PHONY: local stop reset setup reload

setup:
	AWS_ACCESS_KEY_ID=fake AWS_SECRET_ACCESS_KEY=fake aws dynamodb create-table \
		--table-name personal-hub-content \
		--attribute-definitions AttributeName=id,AttributeType=S \
		--key-schema AttributeName=id,KeyType=HASH \
		--billing-mode PAY_PER_REQUEST \
		--region ap-southeast-1 \
		--endpoint-url http://localhost:8000 > /dev/null 2>&1 || true
	AWS_ACCESS_KEY_ID=fake AWS_SECRET_ACCESS_KEY=fake aws dynamodb create-table \
		--table-name personal-hub-research \
		--attribute-definitions AttributeName=id,AttributeType=S \
		--key-schema AttributeName=id,KeyType=HASH \
		--billing-mode PAY_PER_REQUEST \
		--region us-east-1 \
		--endpoint-url http://localhost:8000 > /dev/null 2>&1 || true
	AWS_ACCESS_KEY_ID=fake AWS_SECRET_ACCESS_KEY=fake aws dynamodb create-table \
		--table-name personal-hub-todos \
		--attribute-definitions AttributeName=id,AttributeType=S \
		--key-schema AttributeName=id,KeyType=HASH \
		--billing-mode PAY_PER_REQUEST \
		--region us-east-1 \
		--endpoint-url http://localhost:8000 > /dev/null 2>&1 || true
	AWS_ACCESS_KEY_ID=fake AWS_SECRET_ACCESS_KEY=fake aws dynamodb create-table \
		--table-name personal-hub-connections \
		--attribute-definitions AttributeName=connectionId,AttributeType=S \
		--key-schema AttributeName=connectionId,KeyType=HASH \
		--billing-mode PAY_PER_REQUEST \
		--region us-east-1 \
		--endpoint-url http://localhost:8000 > /dev/null 2>&1 || true
	AWS_ACCESS_KEY_ID=fake AWS_SECRET_ACCESS_KEY=fake aws dynamodb create-table \
		--table-name personal-hub-notifications \
		--attribute-definitions AttributeName=id,AttributeType=S \
		--key-schema AttributeName=id,KeyType=HASH \
		--billing-mode PAY_PER_REQUEST \
		--region us-east-1 \
		--endpoint-url http://localhost:8000 > /dev/null 2>&1 || true

local:
	sam build
	docker compose up -d --wait
	$(MAKE) setup
	AWS_ACCESS_KEY_ID=fake AWS_SECRET_ACCESS_KEY=fake AWS_DEFAULT_REGION=ap-southeast-1 APP_ENV=local sam local start-api --env-vars env.local.json --port 8080

reload:
	docker compose down
	sam build --no-cached
	docker compose up -d --wait
	$(MAKE) setup
	AWS_ACCESS_KEY_ID=fake AWS_SECRET_ACCESS_KEY=fake AWS_DEFAULT_REGION=ap-southeast-1 APP_ENV=local sam local start-api --env-vars env.local.json --port 8080

stop:
	docker compose down

reset:
	docker compose down -v