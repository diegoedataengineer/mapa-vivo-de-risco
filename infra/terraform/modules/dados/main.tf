# Armazenamento: S3 para bases públicas, imagens e Parquet (versionado, ciclo de vida), RDS PostgreSQL com PostGIS,
# segredo do banco no Secrets Manager. Dados pessoais só no RDS, criptografado, em sub-rede privada.
variable "nome" { type = string }
variable "ambiente" { type = string }
variable "subnets_privadas" { type = list(string) }
variable "sg_banco" { type = string }
variable "banco_acu_min" { type = number } # 0 = pausa quando ocioso (Aurora Serverless v2, PostgreSQL 16.3+)
variable "banco_acu_max" { type = number }
variable "banco_pausa_segundos" { type = number } # ociosidade até pausar (mínimo 300)
variable "banco_instancias" { type = number }     # 1 em dev; 2 em prod (writer + reader em outra AZ)
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
    host     = aws_rds_cluster.banco.endpoint
    port     = 5432
    dbname   = "mvr"
  })
}

resource "aws_db_subnet_group" "banco" {
  name       = "${var.nome}-${var.ambiente}"
  subnet_ids = var.subnets_privadas
}

# Aurora Serverless v2: escala por ACU entre o mínimo e o máximo e, com mínimo 0, pausa depois do tempo de
# ociosidade e cobra só armazenamento. Retomada em segundos na primeira conexão: a API trata o primeiro erro
# com retry. PostGIS é extensão nativa do Aurora PostgreSQL.
resource "aws_rds_cluster" "banco" {
  cluster_identifier              = "${var.nome}-${var.ambiente}"
  engine                          = "aurora-postgresql"
  engine_mode                     = "provisioned"
  engine_version                  = "16.6"
  database_name                   = "mvr"
  master_username                 = "mvr"
  master_password                 = random_password.banco.result
  db_subnet_group_name            = aws_db_subnet_group.banco.name
  vpc_security_group_ids          = [var.sg_banco]
  storage_encrypted               = true
  backup_retention_period         = var.retencao_backup_dias
  deletion_protection             = var.ambiente == "prod"
  skip_final_snapshot             = var.ambiente != "prod"
  final_snapshot_identifier       = var.ambiente == "prod" ? "${var.nome}-${var.ambiente}-final" : null
  enabled_cloudwatch_logs_exports = ["postgresql"]
  serverlessv2_scaling_configuration {
    min_capacity             = var.banco_acu_min
    max_capacity             = var.banco_acu_max
    seconds_until_auto_pause = var.banco_acu_min == 0 ? var.banco_pausa_segundos : null
  }
  tags = { dados_pessoais = "sim", lgpd = "controlador=municipio;operador=mvr" }
}

resource "aws_rds_cluster_instance" "banco" {
  count                        = var.banco_instancias
  identifier                   = "${var.nome}-${var.ambiente}-${count.index}"
  cluster_identifier           = aws_rds_cluster.banco.id
  instance_class               = "db.serverless"
  engine                       = aws_rds_cluster.banco.engine
  engine_version               = aws_rds_cluster.banco.engine_version
  performance_insights_enabled = true
}

# credencial de serviço do Airflow para o módulo Rotinas da API (valor preenchido à mão depois de criar o usuário no Airflow)
resource "aws_secretsmanager_secret" "airflow" {
  name = "${var.nome}/${var.ambiente}/airflow"
}

resource "aws_secretsmanager_secret_version" "airflow" {
  secret_id     = aws_secretsmanager_secret.airflow.id
  secret_string = jsonencode({ url = "https://airflow.exemplo", usuario = "mvr", senha = "troque-me" })
  lifecycle { ignore_changes = [secret_string] }
}

output "bucket_dados" { value = aws_s3_bucket.dados.bucket }
output "bucket_dados_arn" { value = aws_s3_bucket.dados.arn }
output "segredo_banco_arn" { value = aws_secretsmanager_secret.banco.arn }
output "banco_endpoint" { value = aws_rds_cluster.banco.endpoint }
output "banco_cluster" { value = aws_rds_cluster.banco.cluster_identifier }
output "segredo_airflow_arn" { value = aws_secretsmanager_secret.airflow.arn }
