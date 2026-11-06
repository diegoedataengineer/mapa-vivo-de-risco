# Bootstrap (uma vez por conta, à mão)

O estado remoto precisa existir antes do primeiro `terraform init`:

```bash
aws s3api create-bucket --bucket mvr-terraform-estado --region us-east-1
aws s3api put-bucket-versioning --bucket mvr-terraform-estado --versioning-configuration Status=Enabled
aws dynamodb create-table --table-name mvr-terraform-lock --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH --billing-mode PAY_PER_REQUEST
```

Depois, por ambiente, sempre plan em arquivo e apply desse arquivo:

```bash
cd infra/terraform/envs/dev
terraform init -backend-config=backend.hcl
terraform plan -out=plano.tfplan -var tag=sha-$(git rev-parse --short=7 HEAD)
terraform apply plano.tfplan
```

O primeiro apply de dev cria o provedor OIDC e a role do GitHub; a partir daí o pipeline publica sozinho.
