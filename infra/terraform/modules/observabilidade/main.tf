# Logs centralizados, alarmes com fundamento (erros 5xx, latência, tarefas saudáveis, jobs com falha, CPU do banco)
# e um tópico SNS que avisa a equipe. Retenção de log menor em dev.
variable "nome" { type = string }
variable "ambiente" { type = string }
variable "retencao_logs_dias" { type = number }
variable "email_alertas" { type = string }
variable "alb_arn_suffix" { type = string }
variable "target_group_arn_suffix" { type = string }
variable "banco_cluster" { type = string }

resource "aws_cloudwatch_log_group" "servicos" {
  name              = "/mvr/${var.ambiente}"
  retention_in_days = var.retencao_logs_dias
}

resource "aws_sns_topic" "alertas" {
  name = "${var.nome}-${var.ambiente}-alertas"
}

resource "aws_sns_topic_subscription" "email" {
  topic_arn = aws_sns_topic.alertas.arn
  protocol  = "email"
  endpoint  = var.email_alertas
}

resource "aws_cloudwatch_metric_alarm" "api_5xx" {
  alarm_name          = "${var.nome}-${var.ambiente}-api-5xx"
  namespace           = "AWS/ApplicationELB"
  metric_name         = "HTTPCode_Target_5XX_Count"
  statistic           = "Sum"
  period              = 300
  evaluation_periods  = 2
  threshold           = 5
  comparison_operator = "GreaterThanThreshold"
  dimensions          = { LoadBalancer = var.alb_arn_suffix, TargetGroup = var.target_group_arn_suffix }
  alarm_actions       = [aws_sns_topic.alertas.arn]
  treat_missing_data  = "notBreaching"
}

resource "aws_cloudwatch_metric_alarm" "api_latencia" {
  alarm_name          = "${var.nome}-${var.ambiente}-api-latencia-p95"
  namespace           = "AWS/ApplicationELB"
  metric_name         = "TargetResponseTime"
  extended_statistic  = "p95"
  period              = 300
  evaluation_periods  = 3
  threshold           = 1.5
  comparison_operator = "GreaterThanThreshold"
  dimensions          = { LoadBalancer = var.alb_arn_suffix, TargetGroup = var.target_group_arn_suffix }
  alarm_actions       = [aws_sns_topic.alertas.arn]
  treat_missing_data  = "notBreaching"
}

resource "aws_cloudwatch_metric_alarm" "api_sem_saudaveis" {
  alarm_name          = "${var.nome}-${var.ambiente}-api-sem-tarefas-saudaveis"
  namespace           = "AWS/ApplicationELB"
  metric_name         = "HealthyHostCount"
  statistic           = "Minimum"
  period              = 60
  evaluation_periods  = 3
  threshold           = 1
  comparison_operator = "LessThanThreshold"
  dimensions          = { LoadBalancer = var.alb_arn_suffix, TargetGroup = var.target_group_arn_suffix }
  alarm_actions       = [aws_sns_topic.alertas.arn]
}

resource "aws_cloudwatch_metric_alarm" "banco_cpu" {
  alarm_name          = "${var.nome}-${var.ambiente}-banco-cpu"
  namespace           = "AWS/RDS"
  metric_name         = "CPUUtilization"
  statistic           = "Average"
  period              = 300
  evaluation_periods  = 3
  threshold           = 80
  comparison_operator = "GreaterThanThreshold"
  dimensions          = { DBClusterIdentifier = var.banco_cluster }
  alarm_actions       = [aws_sns_topic.alertas.arn]
}

# jobs de lote com falha viram evento -> e-mail (o Batch publica mudanças de estado no EventBridge)
resource "aws_cloudwatch_event_rule" "job_falhou" {
  name = "${var.nome}-${var.ambiente}-job-falhou"
  event_pattern = jsonencode({
    source      = ["aws.batch"]
    detail-type = ["Batch Job State Change"]
    detail      = { status = ["FAILED"] }
  })
}

resource "aws_cloudwatch_event_target" "job_falhou" {
  rule = aws_cloudwatch_event_rule.job_falhou.name
  arn  = aws_sns_topic.alertas.arn
}

resource "aws_sns_topic_policy" "eventos" {
  arn = aws_sns_topic.alertas.arn
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "events.amazonaws.com" }
      Action    = "sns:Publish"
      Resource  = aws_sns_topic.alertas.arn
    }]
  })
}

output "log_group" { value = aws_cloudwatch_log_group.servicos.name }
output "topico_alertas" { value = aws_sns_topic.alertas.arn }
