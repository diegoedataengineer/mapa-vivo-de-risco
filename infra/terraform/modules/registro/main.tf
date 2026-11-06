# Um repositório ECR por serviço. Imagens são imutáveis por tag (sha curto e versão semântica); as sem tag expiram.
variable "nome" { type = string }
variable "servicos" { type = list(string) }

resource "aws_ecr_repository" "servico" {
  for_each             = toset(var.servicos)
  name                 = "${var.nome}/${each.key}"
  image_tag_mutability = "IMMUTABLE"
  image_scanning_configuration { scan_on_push = true }
}

resource "aws_ecr_lifecycle_policy" "servico" {
  for_each   = aws_ecr_repository.servico
  repository = each.value.name
  policy = jsonencode({
    rules = [
      { rulePriority = 1, description = "sem tag expira em 7 dias", selection = { tagStatus = "untagged", countType = "sinceImagePushed", countUnit = "days", countNumber = 7 }, action = { type = "expire" } },
      { rulePriority = 2, description = "mantém as 50 últimas por sha", selection = { tagStatus = "tagged", tagPrefixList = ["sha-"], countType = "imageCountMoreThan", countNumber = 50 }, action = { type = "expire" } }
    ]
  })
}

output "repositorios" { value = { for k, r in aws_ecr_repository.servico : k => r.repository_url } }
output "repositorios_arn" { value = [for r in aws_ecr_repository.servico : r.arn] }
