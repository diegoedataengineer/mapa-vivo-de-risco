# Composição dos módulos para um ambiente. dev e prod usam este mesmo arquivo (link simbólico) e diferem só nos tfvars.
terraform {
  required_version = ">= 1.9"
  required_providers {
    aws    = { source = "hashicorp/aws", version = "~> 5.80" }
    random = { source = "hashicorp/random", version = "~> 3.6" }
  }
  backend "s3" {}
}

provider "aws" {
  region = var.regiao
  default_tags {
    tags = { projeto = var.nome, ambiente = var.ambiente, gerido_por = "terraform" }
  }
}

variable "nome" { type = string }
variable "ambiente" { type = string }
variable "regiao" { type = string }
variable "cidr" { type = string }
variable "zonas" { type = list(string) }
variable "tag" { type = string } # tag das imagens (sha-<7> em dev, vX.Y.Z em prod); o pipeline passa por -var
variable "api_cpu" { type = number }
variable "api_memoria" { type = number }
variable "api_replicas_min" { type = number }
variable "api_replicas_max" { type = number }
variable "banco_classe" { type = string }
variable "banco_multi_az" { type = bool }
variable "retencao_backup_dias" { type = number }
variable "retencao_logs_dias" { type = number }
variable "gpu_max_vcpus" { type = number }
variable "email_alertas" { type = string }
variable "github_repositorio" { type = string }
variable "github_repositorio_id" { type = string }
variable "github_dono_id" { type = string }
variable "criar_provedor_oidc" { type = bool }
variable "bucket_estado_arn" { type = string }

locals { servicos = ["api", "exposicao", "deteccao"] } # a ingestão roda no Airflow existente, fora da AWS (ADR-0003)

module "rede" {
  source = "../../modules/rede"
  nome   = "${var.nome}-${var.ambiente}"
  cidr   = var.cidr
  zonas  = var.zonas
}

module "registro" {
  source   = "../../modules/registro"
  nome     = var.nome
  servicos = local.servicos
}

module "dados" {
  source               = "../../modules/dados"
  nome                 = var.nome
  ambiente             = var.ambiente
  subnets_privadas     = module.rede.subnets_privadas
  sg_banco             = module.rede.sg_banco
  banco_classe         = var.banco_classe
  banco_multi_az       = var.banco_multi_az
  retencao_backup_dias = var.retencao_backup_dias
}

module "observabilidade" {
  source                  = "../../modules/observabilidade"
  nome                    = var.nome
  ambiente                = var.ambiente
  retencao_logs_dias      = var.retencao_logs_dias
  email_alertas           = var.email_alertas
  alb_arn_suffix          = module.servicos.alb_arn_suffix
  target_group_arn_suffix = module.servicos.target_group_arn_suffix
  banco_identificador     = "${var.nome}-${var.ambiente}"
}

module "servicos" {
  source            = "../../modules/servicos"
  nome              = var.nome
  ambiente          = var.ambiente
  vpc_id            = module.rede.vpc_id
  subnets           = module.rede.subnets_publicas
  sg_servicos       = module.rede.sg_servicos
  imagem_api        = module.registro.repositorios["api"]
  tag_api           = var.tag
  cpu               = var.api_cpu
  memoria           = var.api_memoria
  replicas_min      = var.api_replicas_min
  replicas_max      = var.api_replicas_max
  segredo_banco_arn = module.dados.segredo_banco_arn
  bucket_dados_arn  = module.dados.bucket_dados_arn
  log_group         = "/mvr/${var.ambiente}"
  regiao            = var.regiao
}

module "lote" {
  source            = "../../modules/lote"
  nome              = var.nome
  ambiente          = var.ambiente
  subnets           = module.rede.subnets_publicas
  sg_servicos       = module.rede.sg_servicos
  repositorios      = module.registro.repositorios
  tag               = var.tag
  bucket_dados      = module.dados.bucket_dados
  bucket_dados_arn  = module.dados.bucket_dados_arn
  segredo_banco_arn = module.dados.segredo_banco_arn
  log_group         = "/mvr/${var.ambiente}"
  regiao            = var.regiao
  gpu_max_vcpus     = var.gpu_max_vcpus
}

module "cicd" {
  source               = "../../modules/cicd"
  nome                 = var.nome
  ambiente             = var.ambiente
  repositorio          = var.github_repositorio
  repositorio_id       = var.github_repositorio_id
  dono_id              = var.github_dono_id
  criar_provedor       = var.criar_provedor_oidc
  repositorios_ecr_arn = module.registro.repositorios_arn
  bucket_estado_arn    = var.bucket_estado_arn
}

module "orquestrador" {
  source            = "../../modules/orquestrador"
  nome              = var.nome
  ambiente          = var.ambiente
  bucket_dados_arn  = module.dados.bucket_dados_arn
  fila_cpu_arn      = module.lote.fila_cpu
  job_exposicao_arn = module.lote.job_exposicao
}

output "api_url" { value = "http://${module.servicos.alb_dns}" }
output "airflow_chave_id" { value = module.orquestrador.chave_id }
output "airflow_chave_segredo" {
  value     = module.orquestrador.chave_segredo
  sensitive = true
}
output "cluster" { value = module.servicos.cluster }
output "bucket_dados" { value = module.dados.bucket_dados }
output "repositorios" { value = module.registro.repositorios }
output "role_github" { value = module.cicd.role_arn }
output "fila_gpu" { value = module.lote.fila_gpu }
