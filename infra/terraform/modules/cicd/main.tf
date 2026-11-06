# Publicação sem chave: o GitHub Actions assume uma role por ambiente via OIDC. A trust policy aceita o `sub`
# com e sem os IDs numéricos de dono e repositório (o GitHub emite os dois formatos). dev aceita a branch main;
# prod só aceita tags v* e o environment "prod" (que exige aprovação manual no GitHub).
variable "nome" { type = string }
variable "ambiente" { type = string }
variable "repositorio" { type = string } # dono/repo
variable "repositorio_id" { type = string }
variable "dono_id" { type = string }
variable "criar_provedor" { type = bool }
variable "repositorios_ecr_arn" { type = list(string) }
variable "bucket_estado_arn" { type = string }

data "aws_caller_identity" "atual" {}

resource "aws_iam_openid_connect_provider" "github" {
  count           = var.criar_provedor ? 1 : 0
  url             = "https://token.actions.githubusercontent.com"
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = ["6938fd4d98bab03faadb97b34396831e3780aea1"]
}

locals {
  provedor_arn = "arn:aws:iam::${data.aws_caller_identity.atual.account_id}:oidc-provider/token.actions.githubusercontent.com"
  dono         = split("/", var.repositorio)[0]
  repo         = split("/", var.repositorio)[1]
  subs = var.ambiente == "prod" ? [
    "repo:${var.repositorio}:environment:prod",
    "repo:${local.dono}@${var.dono_id}/${local.repo}@${var.repositorio_id}:environment:prod",
    ] : [
    "repo:${var.repositorio}:ref:refs/heads/main",
    "repo:${local.dono}@${var.dono_id}/${local.repo}@${var.repositorio_id}:ref:refs/heads/main",
    "repo:${var.repositorio}:environment:dev",
    "repo:${local.dono}@${var.dono_id}/${local.repo}@${var.repositorio_id}:environment:dev",
  ]
}

data "aws_iam_policy_document" "confianca" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]
    principals {
      type        = "Federated"
      identifiers = [local.provedor_arn]
    }
    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }
    condition {
      test     = "StringLike"
      variable = "token.actions.githubusercontent.com:sub"
      values   = local.subs
    }
  }
}

resource "aws_iam_role" "publicar" {
  name               = "${var.nome}-${var.ambiente}-github"
  assume_role_policy = data.aws_iam_policy_document.confianca.json
}

resource "aws_iam_role_policy" "publicar" {
  role = aws_iam_role.publicar.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      { Effect = "Allow", Action = ["ecr:GetAuthorizationToken"], Resource = "*" },
      { Effect = "Allow", Action = ["ecr:BatchCheckLayerAvailability", "ecr:PutImage", "ecr:InitiateLayerUpload", "ecr:UploadLayerPart", "ecr:CompleteLayerUpload", "ecr:BatchGetImage", "ecr:DescribeImages"], Resource = var.repositorios_ecr_arn },
      { Effect = "Allow", Action = ["s3:GetObject", "s3:PutObject", "s3:ListBucket"], Resource = [var.bucket_estado_arn, "${var.bucket_estado_arn}/*"] },
      { Effect = "Allow", Action = ["dynamodb:GetItem", "dynamodb:PutItem", "dynamodb:DeleteItem"], Resource = "arn:aws:dynamodb:*:${data.aws_caller_identity.atual.account_id}:table/${var.nome}-terraform-lock" },
      # o Terraform do ambiente precisa ler e alterar o que ele mesmo criou; escopo por tag do projeto
      { Effect = "Allow", Action = ["ecs:*", "batch:*", "ec2:Describe*", "elasticloadbalancing:*", "logs:*", "cloudwatch:*", "events:*", "sns:*", "rds:Describe*", "secretsmanager:DescribeSecret", "secretsmanager:GetSecretValue", "iam:PassRole", "application-autoscaling:*"], Resource = "*" }
    ]
  })
}

output "role_arn" { value = aws_iam_role.publicar.arn }
