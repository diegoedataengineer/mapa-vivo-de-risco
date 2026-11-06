# Processamento em lote orientado a eventos: filas do AWS Batch em Fargate (ingestão e exposição) e em EC2 Spot com GPU
# (detecção de edificações). Um objeto novo em imagens/ no S3 publica evento no EventBridge, que submete o job de detecção.
variable "nome" { type = string }
variable "ambiente" { type = string }
variable "subnets" { type = list(string) }
variable "sg_servicos" { type = string }
variable "repositorios" { type = map(string) }
variable "tag" { type = string }
variable "bucket_dados" { type = string }
variable "bucket_dados_arn" { type = string }
variable "segredo_banco_arn" { type = string }
variable "log_group" { type = string }
variable "regiao" { type = string }
variable "gpu_max_vcpus" { type = number }

data "aws_iam_policy_document" "batch_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["batch.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "batch" {
  name               = "${var.nome}-${var.ambiente}-batch"
  assume_role_policy = data.aws_iam_policy_document.batch_assume.json
}

resource "aws_iam_role_policy_attachment" "batch" {
  role       = aws_iam_role.batch.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSBatchServiceRole"
}

data "aws_iam_policy_document" "ecs_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "job" {
  name               = "${var.nome}-${var.ambiente}-job"
  assume_role_policy = data.aws_iam_policy_document.ecs_assume.json
}

resource "aws_iam_role_policy_attachment" "job_execucao" {
  role       = aws_iam_role.job.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role_policy" "job" {
  role = aws_iam_role.job.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      { Effect = "Allow", Action = ["s3:GetObject", "s3:PutObject", "s3:ListBucket"], Resource = [var.bucket_dados_arn, "${var.bucket_dados_arn}/*"] },
      { Effect = "Allow", Action = ["secretsmanager:GetSecretValue"], Resource = var.segredo_banco_arn },
      { Effect = "Allow", Action = ["events:PutEvents"], Resource = "*" }
    ]
  })
}

resource "aws_batch_compute_environment" "cpu" {
  compute_environment_name = "${var.nome}-${var.ambiente}-cpu"
  type                     = "MANAGED"
  service_role             = aws_iam_role.batch.arn
  compute_resources {
    type               = "FARGATE_SPOT"
    max_vcpus          = 16
    subnets            = var.subnets
    security_group_ids = [var.sg_servicos]
  }
}

data "aws_iam_policy_document" "ec2_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "instancia_gpu" {
  name               = "${var.nome}-${var.ambiente}-gpu"
  assume_role_policy = data.aws_iam_policy_document.ec2_assume.json
}

resource "aws_iam_role_policy_attachment" "instancia_gpu" {
  role       = aws_iam_role.instancia_gpu.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonEC2ContainerServiceforEC2Role"
}

resource "aws_iam_instance_profile" "gpu" {
  name = "${var.nome}-${var.ambiente}-gpu"
  role = aws_iam_role.instancia_gpu.name
}

resource "aws_batch_compute_environment" "gpu" {
  compute_environment_name = "${var.nome}-${var.ambiente}-gpu"
  type                     = "MANAGED"
  service_role             = aws_iam_role.batch.arn
  compute_resources {
    type                = "SPOT"
    allocation_strategy = "SPOT_PRICE_CAPACITY_OPTIMIZED"
    bid_percentage      = 60
    min_vcpus           = 0
    max_vcpus           = var.gpu_max_vcpus
    instance_type       = ["g4dn.xlarge", "g5.xlarge"]
    subnets             = var.subnets
    security_group_ids  = [var.sg_servicos]
    instance_role       = aws_iam_instance_profile.gpu.arn
  }
}

resource "aws_batch_job_queue" "cpu" {
  name     = "${var.nome}-${var.ambiente}-cpu"
  state    = "ENABLED"
  priority = 1
  compute_environment_order {
    order               = 1
    compute_environment = aws_batch_compute_environment.cpu.arn
  }
}

resource "aws_batch_job_queue" "gpu" {
  name     = "${var.nome}-${var.ambiente}-gpu"
  state    = "ENABLED"
  priority = 1
  compute_environment_order {
    order               = 1
    compute_environment = aws_batch_compute_environment.gpu.arn
  }
}

locals {
  log_cfg = { logDriver = "awslogs", options = { "awslogs-group" = var.log_group, "awslogs-region" = var.regiao, "awslogs-stream-prefix" = "lote" } }
  env_comum = [
    { name = "MVR_AMBIENTE", value = var.ambiente },
    { name = "MVR_BUCKET", value = var.bucket_dados },
    { name = "MVR_VERSAO", value = var.tag }
  ]
}

resource "aws_batch_job_definition" "exposicao" {
  name                  = "${var.nome}-${var.ambiente}-exposicao"
  type                  = "container"
  platform_capabilities = ["FARGATE"]
  retry_strategy { attempts = 3 }
  timeout { attempt_duration_seconds = 7200 }
  container_properties = jsonencode({
    image                        = "${var.repositorios["exposicao"]}:${var.tag}"
    command                      = ["python", "-m", "mvr_exposicao", "--municipio", "Ref::municipio"]
    executionRoleArn             = aws_iam_role.job.arn
    jobRoleArn                   = aws_iam_role.job.arn
    resourceRequirements         = [{ type = "VCPU", value = "2" }, { type = "MEMORY", value = "8192" }]
    networkConfiguration         = { assignPublicIp = "ENABLED" }
    fargatePlatformConfiguration = { platformVersion = "LATEST" }
    environment                  = local.env_comum
    secrets                      = [{ name = "MVR_BANCO", valueFrom = var.segredo_banco_arn }]
    logConfiguration             = local.log_cfg
  })
}

resource "aws_batch_job_definition" "deteccao" {
  name                  = "${var.nome}-${var.ambiente}-deteccao"
  type                  = "container"
  platform_capabilities = ["EC2"]
  retry_strategy { attempts = 2 }
  timeout { attempt_duration_seconds = 14400 }
  container_properties = jsonencode({
    image      = "${var.repositorios["deteccao"]}:${var.tag}"
    command    = ["python", "-m", "mvr_deteccao", "--imagem", "Ref::imagem"]
    jobRoleArn = aws_iam_role.job.arn
    resourceRequirements = [
      { type = "VCPU", value = "4" }, { type = "MEMORY", value = "15000" }, { type = "GPU", value = "1" }
    ]
    environment      = local.env_comum
    secrets          = [{ name = "MVR_BANCO", valueFrom = var.segredo_banco_arn }]
    logConfiguration = local.log_cfg
  })
}

# evento: imagem nova no bucket -> job de detecção (EventBridge precisa de notificação do S3 ligada)
resource "aws_s3_bucket_notification" "eventbridge" {
  bucket      = var.bucket_dados
  eventbridge = true
}

data "aws_iam_policy_document" "events_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["events.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "eventos" {
  name               = "${var.nome}-${var.ambiente}-eventos"
  assume_role_policy = data.aws_iam_policy_document.events_assume.json
}

resource "aws_iam_role_policy" "eventos" {
  role = aws_iam_role.eventos.id
  policy = jsonencode({
    Version   = "2012-10-17"
    Statement = [{ Effect = "Allow", Action = ["batch:SubmitJob"], Resource = "*" }]
  })
}

resource "aws_cloudwatch_event_rule" "imagem_nova" {
  name = "${var.nome}-${var.ambiente}-imagem-nova"
  event_pattern = jsonencode({
    source      = ["aws.s3"]
    detail-type = ["Object Created"]
    detail      = { bucket = { name = [var.bucket_dados] }, object = { key = [{ prefix = "imagens/" }] } }
  })
}

resource "aws_cloudwatch_event_target" "imagem_nova" {
  rule     = aws_cloudwatch_event_rule.imagem_nova.name
  arn      = aws_batch_job_queue.gpu.arn
  role_arn = aws_iam_role.eventos.arn
  batch_target {
    job_definition = aws_batch_job_definition.deteccao.arn
    job_name       = "deteccao"
  }
  input_transformer {
    input_paths    = { chave = "$.detail.object.key" }
    input_template = "{\"Parameters\": {\"imagem\": <chave>}}"
  }
}

output "fila_cpu" { value = aws_batch_job_queue.cpu.arn }
output "fila_gpu" { value = aws_batch_job_queue.gpu.arn }
output "job_exposicao" { value = aws_batch_job_definition.exposicao.arn }
output "job_deteccao" { value = aws_batch_job_definition.deteccao.arn }
