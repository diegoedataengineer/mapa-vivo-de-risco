# Acesso do Airflow existente (VPS fora da AWS, sem OIDC) ao mínimo necessário: escrever em bases/ e imagens/ no S3 e
# submeter/acompanhar jobs no Batch. Chave de acesso guardada na conexão `aws_mvr` do Airflow; rotação trimestral.
variable "nome" { type = string }
variable "ambiente" { type = string }
variable "bucket_dados_arn" { type = string }
variable "fila_cpu_arn" { type = string }
variable "job_exposicao_arn" { type = string }

resource "aws_iam_user" "airflow" {
  name = "${var.nome}-${var.ambiente}-airflow"
  tags = { finalidade = "ingestao de bases publicas pelo Airflow da VPS" }
}

resource "aws_iam_user_policy" "airflow" {
  user = aws_iam_user.airflow.name
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      { Effect = "Allow", Action = ["s3:PutObject", "s3:GetObject", "s3:ListBucket"], Resource = [var.bucket_dados_arn, "${var.bucket_dados_arn}/bases/*", "${var.bucket_dados_arn}/imagens/*"] },
      { Effect = "Allow", Action = ["batch:SubmitJob"], Resource = [var.fila_cpu_arn, var.job_exposicao_arn] },
      { Effect = "Allow", Action = ["batch:DescribeJobs", "batch:TerminateJob"], Resource = "*" }
    ]
  })
}

resource "aws_iam_access_key" "airflow" {
  user = aws_iam_user.airflow.name
}

output "usuario" { value = aws_iam_user.airflow.name }
output "chave_id" { value = aws_iam_access_key.airflow.id }
output "chave_segredo" {
  value     = aws_iam_access_key.airflow.secret
  sensitive = true
}
