# Armazenamento: S3 para bases públicas, imagens e Parquet (versionado, ciclo de vida), RDS PostgreSQL com PostGIS,
# segredo do banco no Secrets Manager. Dados pessoais só no RDS, criptografado, em sub-rede privada.
variable "nome" { type = string }
variable "ambiente" { type = string }
variable "subnets_privadas" { type = list(string) }
variable "sg_banco" { type = string }
variable "banco_classe" { type = string }
variable "banco_multi_az" { type = bool }
variable "retencao_backup_dias" { type = number }

resource "aws_s3_bucket" "dados" {
  bucket = "${var.nome}-dados-${var.ambiente}"
}

resource "aws_s3_bucket_versioning" "dados" {
  bucket = aws_s3_bucket.dados.id
  versioning_configuration { status = "Enabled" }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "dados" {
  bucket = aws_s3_bucket.dados.id
  rule {
    apply_server_side_encryption_by_default { sse_algorithm = "AES256" }
  }
}

resource "aws_s3_bucket_public_access_block" "dados" {
  bucket                  = aws_s3_bucket.dados.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "dados" {
  bucket = aws_s3_bucket.dados.id
  # imagens brutas vão para armazenamento frio depois de 90 dias; tiles de inferência expiram em 30 dias
  rule {
    id     = "imagens-frias"
    status = "Enabled"
    filter { prefix = "imagens/" }
    transition {
      days          = 90
      storage_class = "GLACIER_IR"
    }
  }
  rule {
    id     = "tiles-temporarios"
    status = "Enabled"
    filter { prefix = "tiles/" }
    expiration { days = 30 }
  }
}

resource "random_password" "banco" {
  length  = 32
  special = false
}

resource "aws_secretsmanager_secret" "banco" {
  name = "${var.nome}/${var.ambiente}/banco"
}

resource "aws_secretsmanager_secret_version" "banco" {
  secret_id = aws_secretsmanager_secret.banco.id
  secret_string = jsonencode({
    username = "mvr"
    password = random_password.banco.result
    host     = aws_db_instance.banco.address
    port     = 5432
    dbname   = "mvr"
  })
}

resource "aws_db_subnet_group" "banco" {
  name       = "${var.nome}-${var.ambiente}"
  subnet_ids = var.subnets_privadas
}

resource "aws_db_instance" "banco" {
  identifier                   = "${var.nome}-${var.ambiente}"
  engine                       = "postgres"
  engine_version               = "16"
  instance_class               = var.banco_classe
  allocated_storage            = 50
  max_allocated_storage        = 500
  db_name                      = "mvr"
  username                     = "mvr"
  password                     = random_password.banco.result
  db_subnet_group_name         = aws_db_subnet_group.banco.name
  vpc_security_group_ids       = [var.sg_banco]
  multi_az                     = var.banco_multi_az
  storage_encrypted            = true
  backup_retention_period      = var.retencao_backup_dias
  deletion_protection          = var.ambiente == "prod"
  skip_final_snapshot          = var.ambiente != "prod"
  performance_insights_enabled = true
  tags                         = { dados_pessoais = "sim", lgpd = "controlador=municipio;operador=mvr" }
}

output "bucket_dados" { value = aws_s3_bucket.dados.bucket }
output "bucket_dados_arn" { value = aws_s3_bucket.dados.arn }
output "segredo_banco_arn" { value = aws_secretsmanager_secret.banco.arn }
output "banco_endpoint" { value = aws_db_instance.banco.address }
