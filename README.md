`# Preditor de Sobrevivência Titanic - Pipeline MLOps Serverless

<p align="center">
<img src="[https://img.shields.io/badge/AWS-API%20Gateway%20%7C%20Lambda%20%7C%20DynamoDB-orange?logo=amazon-aws](https://www.google.com/search?q=https://img.shields.io/badge/AWS-API%2520Gateway%2520%257C%2520Lambda%2520%257C%2520DynamoDB-orange%3Flogo%3Damazon-aws)" alt="AWS"/>
<img src="[https://img.shields.io/badge/IaC-Terraform%20v1.5%2B-blueviolet?logo=terraform](https://www.google.com/search?q=https://img.shields.io/badge/IaC-Terraform%2520v1.5%252B-blueviolet%3Flogo%3Dterraform)" alt="Terraform"/>
<img src="[https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-blue?logo=githubactions](https://www.google.com/search?q=https://img.shields.io/badge/CI%252FCD-GitHub%2520Actions-blue%3Flogo%3Dgithubactions)" alt="GitHub Actions"/>
<img src="[https://img.shields.io/badge/Language-Python%203.9-blue?logo=python](https://www.google.com/search?q=https://img.shields.io/badge/Language-Python%25203.9-blue%3Flogo%3Dpython)" alt="Python"/>
</p>

---

## Visão Geral

Este projeto implementa uma esteira automatizada de MLOps e uma API de inferência totalmente Serverless na AWS. A solução é responsável por receber dados de passageiros do Titanic, processar as características e retornar a probabilidade de sobrevivência utilizando um modelo de Machine Learning (Scikit-Learn).

A arquitetura combina:

* **API Gateway + AWS Lambda** -> Hospedagem da API de inferência com roteamento proxy.
* **Amazon DynamoDB** -> Armazenamento de baixa latência em modo sob demanda.
* **Terraform** -> Provisionamento completo de infraestrutura como código (IaC).
* **GitHub Actions** -> Automação de CI/CD para testes, empacotamento e deploy.
* **OpenAPI 3.0** -> Contrato e documentação da API.

---

## Arquitetura da Solução

Abaixo está o diagrama da arquitetura implementada, demonstrando o fluxo de provisionamento via IaC e o caminho da requisição do cliente.mermaid
graph TD
subgraph CI/CD Pipeline
A[Push na branch main] --> B(GitHub Actions)
B -->|1. PyTest| C{Testes Unitários}
C -->|2. Zip Source| D
D -->|3. Terraform Apply| E
end

```
subgraph AWS Cloud Serverless
    F[Cliente / Front-end] -->|HTTP POST| G(API Gateway)
    G -->|Proxy Integration| H(AWS Lambda)
    H -->|Carrega em Cache| I(model.pkl)
    H -->|Grava Predição| J(DynamoDB)
end

E -. Configura.-> G
E -. Faz Deploy.-> H
E -. Cria Tabela.-> J

```

```

---

## Fluxo de Trabalho Ponta a Ponta

1. **Ingestão de Requisição**
   - O cliente envia uma requisição HTTP POST para o API Gateway contendo os dados de entrada em formato JSON.

2. **Roteamento e Validação**
   - O API Gateway atua como proxy e aciona a AWS Lambda de forma efêmera.
   - A camada interna de Schema (DTO) valida se a estrutura corresponde a um array numérico válido.

3. **Inferência e Escoragem**
   - A camada de serviço acessa o arquivo serializado do modelo. O modelo é mantido em memória RAM (Singleton) após a primeira execução para evitar latência de Cold Start nas próximas requisições.

4. **Persistência**
   - A probabilidade calculada e um UUID gerado são gravados na tabela do DynamoDB.

5. **Automação CI/CD**
   - A cada push na branch principal, o GitHub Actions executa os testes, compacta o código e o Terraform atualiza toda a infraestrutura automaticamente na AWS.

---

## Estrutura de Pastas

.
├──.github/workflows/deploy.yml
├── docs/openapi.yaml
├── infra/
│   └── main.tf
├── src/
│   ├── modelo/
│   │   ├── model.pkl
│   │   └── treinamento.ipynb
│   ├── controller.py
│   ├── lambda_function.py
│   ├── repository.py
│   ├── requirements.txt
│   ├── schemas.py
│   └── service.py
├── tests/
│   ├── __init__.py
│   └── test_api.py
└── README.md

---

## API de Inferência

| Método | Rota | Descrição |
|--------|-----------------------|----------------------------------------------------|
| `POST` | `/sobreviventes` | Estima a probabilidade com base nas características |
| `GET` | `/sobreviventes` | Retorna a lista de passageiros avaliados |
| `GET` | `/sobreviventes/{id}` | Consulta a probabilidade de um ID específico |
| `DELETE` | `/sobreviventes/{id}` | Remove o registro do passageiro da base de dados |

### Exemplo de Requisição

```bash
curl -X POST "https://<api_id>[.execute-api.us-east-1.amazonaws.com/v1/sobreviventes](https://.execute-api.us-east-1.amazonaws.com/v1/sobreviventes)" \
     -H "Content-Type: application/json" \
     -d '{
          "caracteristicas": [3, 22.0, 1, 0, 7.25]
         }'

```

---

## Requisitos de Sistema

| Ferramenta | Versão Mínima | Propósito |
| --- | --- | --- |
| Terraform | >= 1.5 | Provisionamento de Infraestrutura |
| AWS CLI | >= 2.0 | Interação com serviços AWS |
| Python | 3.9 | Ambiente de execução da Lambda e Testes |
| GitHub Actions | N/A | Pipeline de CI/CD |

---

## Configurações Necessárias

### Segredos do GitHub (Secrets)

Para que o Terraform consiga autenticar e provisionar os recursos na nuvem, configure as variáveis abaixo na aba de Secrets do repositório:

| Nome | Descrição |
| --- | --- |
| `AWS_ACCESS_KEY_ID` | Chave de acesso IAM para uso da esteira |
| `AWS_SECRET_ACCESS_KEY` | Chave secreta IAM correspondente |
| `AWS_REGION` | Região de deploy (ex: us-east-1) |

---

## Autoria

Desenvolvido por **Sophie Pyxis de Paula** (sophie-pyxis).

---

## Melhorias Futuras

* **Autenticação OIDC**: Substituir o uso de chaves estáticas do IAM por tokens efêmeros, aderindo ao modelo Zero Trust no GitHub Actions.
* **Remote Backend para Terraform**: Migrar o controle de estado local (`tfstate`) para um bucket S3 com DynamoDB Lock (State Locking).
* **AWS Lambda Layers**: Extrair bibliotecas base como Scikit-Learn e Pandas do pacote fonte para otimizar o tempo de build e deploy.
* **Observabilidade**: Envio das métricas de predição para o CloudWatch/Datadog para rastrear o Data Drift do modelo em produção.

```



```