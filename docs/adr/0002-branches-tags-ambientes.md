# ADR-0002 — Branches, tags, ambientes e promoção

Data: 05/11/2026 · Status: aceita

## Contexto
A disciplina pede CI/CD com versionamento, integração, testes, geração de artefatos e implantação (webaulas 03, 04 e 05:
pipeline de deploy, Terraform, gestão de configuração de software com itens de configuração, nomeação e versionamento,
auditoria). O time é pequeno e o produto vai a prefeituras: precisa de histórico rastreável e rollback simples.

## Decisão
- **Trunk-based com `main` protegida.** Trabalho em `feature/<tema>` curto (dias, não semanas), PR obrigatório com CI
  verde e uma revisão. Sem branch `develop`: a `main` é o que está em dev.
- **Dois ambientes na AWS, mesmo código, tfvars diferentes.** `dev` recebe todo merge na `main` sem aprovação; `prod`
  recebe só tags.
- **Tags semânticas `vX.Y.Z` na `main` são o único gatilho de produção.** `X` muda contrato de API ou de dados; `Y`
  funcionalidade; `Z` correção. O workflow confere que a tag está na `main`, publica as imagens com a tag, roda o plan de
  prod e espera aprovação manual do environment `prod` antes do apply. O release no GitHub nasce com as notas geradas.
- **Itens de configuração.** Imagem de contêiner (sempre com `sha-<7>` e, em release, `vX.Y.Z`; tags imutáveis no ECR),
  estado do Terraform por ambiente (S3 versionado + lock), tfvars por ambiente, versão do modelo de ML (registrada com
  o sha da imagem que o treinou), versão de cada base pública (data e origem gravadas na ingestão). Nada é `:latest`.
- **Rollback** é re-executar o release com a tag anterior: a imagem já existe no ECR e o plan mostra só a troca de tag.
  O ECS faz rollback automático por circuit breaker quando o deploy não estabiliza.
- **Sem chave de nuvem no GitHub.** Uma role por ambiente, assumida por OIDC; o `sub` aceito em prod é só
  `environment:prod`.

## Consequências
- Um hotfix em produção é: branch da `main`, PR, merge, tag. Dev recebe junto, de graça.
- Auditoria da configuração responde "o que está em prod?" com uma tag, um sha e um estado do Terraform.
- Custo: dev roda pequeno (1 tarefa, banco micro, GPU só sob demanda e Spot); prod tem 2 réplicas, banco multi-AZ.
