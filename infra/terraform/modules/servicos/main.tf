# API em ECS Fargate atrás de um ALB, com autoescala por CPU e health check em /saude. Imagem fixada por tag
# (sha ou versão), nunca :latest: o deploy é a troca da tag pelo pipeline.
variable "nome" { type = string }
variable "ambiente" { type = string }
variable "vpc_id" { type = string }
variable "subnets" { type = list(string) }
variable "sg_servicos" { type = string }
variable "imagem_api" { type = string }
variable "tag_api" { type = string }
variable "cpu" { type = number }
variable "memoria" { type = number }
variable "replicas_min" { type = number }
variable "replicas_max" { type = number }
variable "segredo_banco_arn" { type = string }
variable "bucket_dados_arn" { type = string }
variable "log_group" { type = string }
variable "regiao" { type = string }

resource "aws_ecs_cluster" "este" {
  name = "${var.nome}-${var.ambiente}"
  setting {
    name  = "containerInsights"
    value = "enabled"
  }
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

resource "aws_iam_role" "execucao" {
  name               = "${var.nome}-${var.ambiente}-execucao"
  assume_role_policy = data.aws_iam_policy_document.ecs_assume.json
}

resource "aws_iam_role_policy_attachment" "execucao" {
  role       = aws_iam_role.execucao.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role_policy" "execucao_segredos" {
  role = aws_iam_role.execucao.id
  policy = jsonencode({
    Version   = "2012-10-17"
    Statement = [{ Effect = "Allow", Action = ["secretsmanager:GetSecretValue"], Resource = var.segredo_banco_arn }]
  })
}

resource "aws_iam_role" "tarefa" {
  name               = "${var.nome}-${var.ambiente}-tarefa"
  assume_role_policy = data.aws_iam_policy_document.ecs_assume.json
}

resource "aws_iam_role_policy" "tarefa" {
  role = aws_iam_role.tarefa.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      { Effect = "Allow", Action = ["s3:GetObject", "s3:PutObject", "s3:ListBucket"], Resource = [var.bucket_dados_arn, "${var.bucket_dados_arn}/*"] },
      { Effect = "Allow", Action = ["events:PutEvents"], Resource = "*" }
    ]
  })
}

resource "aws_ecs_task_definition" "api" {
  family                   = "${var.nome}-${var.ambiente}-api"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.cpu
  memory                   = var.memoria
  execution_role_arn       = aws_iam_role.execucao.arn
  task_role_arn            = aws_iam_role.tarefa.arn
  runtime_platform {
    cpu_architecture        = "ARM64"
    operating_system_family = "LINUX"
  }
  container_definitions = jsonencode([{
    name         = "api"
    image        = "${var.imagem_api}:${var.tag_api}"
    essential    = true
    portMappings = [{ containerPort = 8000, protocol = "tcp" }]
    environment = [
      { name = "MVR_AMBIENTE", value = var.ambiente },
      { name = "MVR_VERSAO", value = var.tag_api }
    ]
    secrets = [{ name = "MVR_BANCO", valueFrom = var.segredo_banco_arn }]
    healthCheck = {
      command  = ["CMD-SHELL", "python -c \"import urllib.request; urllib.request.urlopen('http://localhost:8000/saude')\" || exit 1"]
      interval = 30
      timeout  = 5
      retries  = 3
    }
    logConfiguration = {
      logDriver = "awslogs"
      options   = { "awslogs-group" = var.log_group, "awslogs-region" = var.regiao, "awslogs-stream-prefix" = "api" }
    }
  }])
}

resource "aws_security_group" "alb" {
  name   = "${var.nome}-${var.ambiente}-alb"
  vpc_id = var.vpc_id
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_lb" "api" {
  name               = "${var.nome}-${var.ambiente}"
  load_balancer_type = "application"
  subnets            = var.subnets
  security_groups    = [aws_security_group.alb.id]
}

resource "aws_lb_target_group" "api" {
  name        = "${var.nome}-${var.ambiente}-api"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"
  health_check {
    path    = "/saude"
    matcher = "200"
  }
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.api.arn
  port              = 80
  protocol          = "HTTP"
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.api.arn
  }
}

resource "aws_ecs_service" "api" {
  name            = "api"
  cluster         = aws_ecs_cluster.este.id
  task_definition = aws_ecs_task_definition.api.arn
  desired_count   = var.replicas_min
  launch_type     = "FARGATE"
  network_configuration {
    subnets          = var.subnets
    security_groups  = [var.sg_servicos]
    assign_public_ip = true
  }
  load_balancer {
    target_group_arn = aws_lb_target_group.api.arn
    container_name   = "api"
    container_port   = 8000
  }
  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }
  deployment_minimum_healthy_percent = 100
  deployment_maximum_percent         = 200
  lifecycle { ignore_changes = [desired_count] }
}

resource "aws_appautoscaling_target" "api" {
  max_capacity       = var.replicas_max
  min_capacity       = var.replicas_min
  resource_id        = "service/${aws_ecs_cluster.este.name}/${aws_ecs_service.api.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_policy" "api_cpu" {
  name               = "cpu-60"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.api.resource_id
  scalable_dimension = aws_appautoscaling_target.api.scalable_dimension
  service_namespace  = aws_appautoscaling_target.api.service_namespace
  target_tracking_scaling_policy_configuration {
    target_value = 60
    predefined_metric_specification { predefined_metric_type = "ECSServiceAverageCPUUtilization" }
  }
}

output "cluster" { value = aws_ecs_cluster.este.name }
output "servico_api" { value = aws_ecs_service.api.name }
output "alb_dns" { value = aws_lb.api.dns_name }
output "target_group_arn_suffix" { value = aws_lb_target_group.api.arn_suffix }
output "alb_arn_suffix" { value = aws_lb.api.arn_suffix }
