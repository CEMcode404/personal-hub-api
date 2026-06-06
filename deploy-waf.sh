#!/bin/bash
set -e

SSM_PARAM="/personal-hub/origin-secret"
STACK_NAME="personal-hub-waf"
REGION_WAF="us-east-1"
REGION_BACKEND="ap-southeast-1"

# Check if SSM parameter already exists in us-east-1
echo "Checking if secret already exists..."
EXISTING=$(aws ssm get-parameter \
  --name "$SSM_PARAM" \
  --region "$REGION_WAF" \
  --no-cli-pager \
  --query "Parameter.Value" \
  --output text \
  --profile personal-hub 2>/dev/null || echo "")

if [ -z "$EXISTING" ]; then
  SECRET=$(python3 -c "import uuid; print(uuid.uuid4())")
  echo "Generated new secret."

  echo "Storing secret in $REGION_WAF..."
  aws ssm put-parameter \
    --name "$SSM_PARAM" \
    --value "$SECRET" \
    --type String \
    --region "$REGION_WAF" \
    --no-cli-pager \
    --profile personal-hub

  echo "Storing secret in $REGION_BACKEND..."
  aws ssm put-parameter \
    --name "$SSM_PARAM" \
    --value "$SECRET" \
    --type String \
    --region "$REGION_BACKEND" \
    --no-cli-pager \
    --profile personal-hub
else
  echo "Secret already exists, syncing to $REGION_BACKEND..."
  aws ssm put-parameter \
    --name "$SSM_PARAM" \
    --value "$EXISTING" \
    --type String \
    --region "$REGION_BACKEND" \
    --overwrite \
    --no-cli-pager \
    --profile personal-hub
fi

# Deploy WAF stack (creates if not exists, updates if exists)
echo "Deploying WAF stack..."
aws cloudformation deploy \
  --template-file waf-template.yaml \
  --stack-name "$STACK_NAME" \
  --region "$REGION_WAF" \
  --no-cli-pager \
  --profile personal-hub

echo ""
echo "WAF deployed successfully!"
echo "WAF ARN:"
aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --region "$REGION_WAF" \
  --query "Stacks[0].Outputs[?OutputKey=='WafWebAclArn'].OutputValue" \
  --output text \
  --no-cli-pager \
  --profile personal-hub