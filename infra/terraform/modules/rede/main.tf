# VPC com sub-redes públicas (Fargate e Batch com IP público, sem NAT: custo zero de NAT em dev) e privadas (RDS).
variable "nome" { type = string }
variable "cidr" { type = string }
variable "zonas" { type = list(string) }

resource "aws_vpc" "esta" {
  cidr_block           = var.cidr
  enable_dns_hostnames = true
  tags                 = { Name = var.nome }
}

resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.esta.id
}

resource "aws_subnet" "publicas" {
  count                   = length(var.zonas)
  vpc_id                  = aws_vpc.esta.id
  cidr_block              = cidrsubnet(var.cidr, 8, count.index)
  availability_zone       = var.zonas[count.index]
  map_public_ip_on_launch = true
  tags                    = { Name = "${var.nome}-publica-${count.index}", camada = "publica" }
}

resource "aws_subnet" "privadas" {
  count             = length(var.zonas)
  vpc_id            = aws_vpc.esta.id
  cidr_block        = cidrsubnet(var.cidr, 8, 100 + count.index)
  availability_zone = var.zonas[count.index]
  tags              = { Name = "${var.nome}-privada-${count.index}", camada = "privada" }
}

resource "aws_route_table" "publica" {
  vpc_id = aws_vpc.esta.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.igw.id
  }
}

resource "aws_route_table_association" "publicas" {
  count          = length(var.zonas)
  subnet_id      = aws_subnet.publicas[count.index].id
  route_table_id = aws_route_table.publica.id
}

resource "aws_security_group" "servicos" {
  name   = "${var.nome}-servicos"
  vpc_id = aws_vpc.esta.id
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "banco" {
  name   = "${var.nome}-banco"
  vpc_id = aws_vpc.esta.id
  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.servicos.id]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

output "vpc_id" { value = aws_vpc.esta.id }
output "subnets_publicas" { value = aws_subnet.publicas[*].id }
output "subnets_privadas" { value = aws_subnet.privadas[*].id }
output "sg_servicos" { value = aws_security_group.servicos.id }
output "sg_banco" { value = aws_security_group.banco.id }
