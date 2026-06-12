.PHONY: local stop reset setup reload deploy

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
	AWS_ACCESS_KEY_ID=fake AWS_SECRET_ACCESS_KEY=fake aws dynamodb create-table \
		--table-name personal-hub-wiki \
		--attribute-definitions \
			AttributeName=id,AttributeType=S \
			AttributeName=gsi_constant,AttributeType=S \
			AttributeName=gsi_order_sk,AttributeType=S \
			AttributeName=category,AttributeType=S \
		--key-schema AttributeName=id,KeyType=HASH \
		--global-secondary-indexes \
			'[{"IndexName":"gsi_ordering","KeySchema":[{"AttributeName":"gsi_constant","KeyType":"HASH"},{"AttributeName":"gsi_order_sk","KeyType":"RANGE"}],"Projection":{"ProjectionType":"INCLUDE","NonKeyAttributes":["title","category","tags","is_pinned","updated_at","cover_image"]}},{"IndexName":"gsi_by_category","KeySchema":[{"AttributeName":"category","KeyType":"HASH"},{"AttributeName":"gsi_order_sk","KeyType":"RANGE"}],"Projection":{"ProjectionType":"INCLUDE","NonKeyAttributes":["title","tags","is_pinned","cover_image","updated_at"]}}]' \
		--billing-mode PAY_PER_REQUEST \
		--region ap-southeast-1 \
		--endpoint-url http://localhost:8000 > /dev/null 2>&1 || true

local:
	sam build
	docker compose up -d --wait
	$(MAKE) setup
	AWS_ACCESS_KEY_ID=fake AWS_SECRET_ACCESS_KEY=fake AWS_DEFAULT_REGION=ap-southeast-1 APP_ENV=local sam local start-api --env-vars env.local.json --port 8080 --disable-authorizer

reload:
	docker compose down
	sam build --no-cached
	docker compose up -d --wait
	$(MAKE) setup
	AWS_ACCESS_KEY_ID=fake AWS_SECRET_ACCESS_KEY=fake AWS_DEFAULT_REGION=ap-southeast-1 APP_ENV=local sam local start-api --env-vars env.local.json --port 8080 --disable-authorizer

stop:
	docker compose down

reset:
	docker compose down -v

deploy:
	sam build
	sam deploy