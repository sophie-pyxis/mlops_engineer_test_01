# Desafio Técnico — MLOps Engineer Sênior · Itaú Unibanco

Solução para o desafio técnico de MLOps Engineer Sênior, implementando uma **API Serverless de inferência de Machine Learning** com **AWS Lambda, API Gateway, DynamoDB e Terraform**, seguindo boas práticas de **Clean Architecture, SOLID e MLOps**.

---

## Atendimento aos Requisitos do Case

| Requisito | Status | Observação |
|---|---|---|
| Repositório GitHub com todos os códigos | ✅ | Repositório público com código, IaC e documentação |
| API via IaC com Terraform | ✅ | `infra/main.tf` provisiona toda a infraestrutura |
| Contrato OpenAPI 3.0 | ✅ | `docs/openapi.yaml` |
| Endpoint `POST /sobreviventes` | ✅ | Recebe array de features, retorna probabilidade + ID |
| Escoragem em função Lambda com Python | ✅ | Ver justificativa abaixo |
| `GET /sobreviventes` | ✅ | Retorna lista completa de passageiros avaliados |
| `GET /sobreviventes/{id}` | ✅ | Retorna probabilidade do passageiro pelo ID |
| `DELETE /sobreviventes/{id}` | ✅ | Remove o passageiro da base |
| DynamoDB **não provisionado** (On-Demand) | ✅ | `billing_mode = "PAY_PER_REQUEST"` |
| DynamoDB e Lambda via Terraform | ✅ | Ambos provisionados em `infra/main.tf` |

### Justificativa — Lambda via Container Image

O requisito especifica Lambda **com código escrito em Python**, o que foi integralmente atendido. Todo o código de inferência, roteamento e persistência está em Python (`lambda_function.py`, `controller.py`, `service.py`, `repository.py`, `schemas.py`).

A escolha por **Container Image** em vez de pacote ZIP foi técnica: as dependências de ML (`scikit-learn`, `scipy`, `numpy`, `pandas`) somam mais de 250MB descompactadas, ultrapassando os limites tanto do upload direto (50MB) quanto do Lambda Layer (250MB). O Container Image suporta até 10GB e é a abordagem recomendada pela AWS para cargas de trabalho de Machine Learning em Lambda.

---

## Arquitetura da Solução

```mermaid
flowchart LR
    Client([Client Application])
    APIGW[API Gateway]
    Lambda[AWS Lambda]
    ECR[(ECR Repository)]
    Model[(model.pkl)]
    Dynamo[(DynamoDB)]

    Client -->|HTTP Request| APIGW
    APIGW -->|Invoke| Lambda
    Lambda -->|predict_proba| Model
    Lambda -->|PutItem / GetItem| Dynamo
    Dynamo -->|Item| Lambda
    Lambda -->|HTTP Response| APIGW
    APIGW -->|HTTP Response| Client
    ECR -->|Container Image| Lambda
```

**Fluxo da aplicação:**

1. O cliente envia uma requisição HTTP para o API Gateway.
2. O API Gateway roteia a chamada para a função AWS Lambda.
3. A Lambda executa a partir de uma imagem Docker com o modelo e as dependências embutidas.
4. O resultado é persistido no DynamoDB On-Demand.
5. A resposta é retornada ao cliente com o ID e a probabilidade de sobrevivência.

---

## Estrutura do Repositório

```
.
├── .github/
│   └── workflows/
│       └── deploy.yml
├── infra/
│   └── main.tf
├── docs/
│   └── openapi.yaml
├── src/
│   ├── lambda_function.py
│   ├── controller.py
│   ├── service.py
│   ├── repository.py
│   ├── schemas.py
│   ├── requirements.txt
│   └── modelo/
│       └── model.pkl
├── tests/
│   └── test_api.py
├── Dockerfile
├── treinamento.ipynb
└── README.md
```

---

## Princípios de Arquitetura

### Clean Architecture

```mermaid
flowchart TD
    A[lambda_function.py]
    B[controller.py]
    C[service.py]
    D[repository.py]
    E[(DynamoDB)]
    F[(model.pkl)]

    A -->|Entry Point| B
    B -->|Orquestra HTTP| C
    C -->|Inferência| F
    C -->|Negócio| D
    D -->|Persistência| E
```

| Camada      | Arquivo              | Responsabilidade                      |
|-------------|----------------------|---------------------------------------|
| Entry Point | `lambda_function.py` | Handler da Lambda, roteamento inicial |
| Controller  | `controller.py`      | Orquestra requisições HTTP            |
| Service     | `service.py`         | Executa inferência com o modelo pkl   |
| Repository  | `repository.py`      | Abstrai acesso ao DynamoDB            |
| Database    | DynamoDB             | Persistência de dados                 |

---

## Modelo de Machine Learning

O modelo foi treinado no notebook `treinamento.ipynb` usando o dataset público do Titanic.

**Algoritmo:** `RandomForestClassifier` (Scikit-learn 1.2.2)
- `n_estimators=100`, `max_depth=5`, `oob_score=True`, `random_state=42`
- ROC-AUC no conjunto de teste: **0.80**

**Features de entrada (ordem obrigatória no array):**

| Posição | Feature      | Descrição               | Valores                         |
|---------|--------------|-------------------------|---------------------------------|
| 0       | `Age`        | Idade do passageiro     | número decimal (ex: `22.0`)     |
| 1       | `Parch`      | Pais/filhos a bordo     | inteiro (ex: `0`)               |
| 2       | `SibSp`      | Irmãos/cônjuge a bordo  | inteiro (ex: `1`)               |
| 3       | `Fare`       | Valor da passagem       | número decimal (ex: `7.25`)     |
| 4       | `Pclass`     | Classe da cabine        | `1`, `2` ou `3`                 |
| 5       | `Sex_male`   | Sexo                    | `1` = masculino, `0` = feminino |
| 6       | `Embarked_Q` | Embarcou em Queenstown  | `1` = sim, `0` = não            |
| 7       | `Embarked_S` | Embarcou em Southampton | `1` = sim, `0` = não            |

> Se o passageiro embarcou em Cherbourg, `Embarked_Q = 0` e `Embarked_S = 0`.

---

## Especificação da API

Documentação completa em `docs/openapi.yaml` (OpenAPI 3.0).

**Base URL:**
```
https://{id}.execute-api.us-east-1.amazonaws.com/v1
```

### `POST /sobreviventes` — Criar escoragem

**Request:**
```json
{
  "caracteristicas": [22.0, 0, 1, 7.25, 3, 1, 0, 1]
}
```

**Response `201`:**
```json
{
  "id": "uuid-gerado",
  "probabilidade_sobrevivencia": 0.12
}
```

**Response `400`:**
```json
{
  "erro": "Payload inválido: O campo 'caracteristicas' deve ser uma lista válida."
}
```

### `GET /sobreviventes` — Listar todos os passageiros avaliados

### `GET /sobreviventes/{id}` — Buscar passageiro por ID

### `DELETE /sobreviventes/{id}` — Remover passageiro

---

## Infraestrutura como Código (Terraform)

A infraestrutura é provisionada automaticamente via **Terraform** (`infra/main.tf`).

| Recurso Terraform                | Descrição                                      |
|----------------------------------|------------------------------------------------|
| `aws_ecr_repository`             | Repositório de imagens Docker da Lambda        |
| `aws_ecr_lifecycle_policy`       | Remove imagens sem tag após 1 dia              |
| `aws_dynamodb_table`             | Tabela On-Demand — sem provisionamento manual  |
| `aws_lambda_function`            | Função via container image (package_type=Image)|
| `aws_api_gateway_rest_api`       | Gateway provisionado via contrato OpenAPI      |
| `aws_iam_role`                   | Execution role da Lambda                       |
| `aws_iam_policy`                 | Política de privilégio mínimo                  |
| `aws_iam_role_policy_attachment` | Vincula a política à role                      |
| `aws_lambda_permission`          | Autoriza o API Gateway invocar a Lambda        |
| `aws_api_gateway_deployment`     | Publicação do estado atual da API              |
| `aws_api_gateway_stage`          | Stage `v1` da API                              |

---

## Pipeline CI/CD

```mermaid
flowchart LR
    Push([git push master])
    GHA[GitHub Actions]
    Test[pytest]
    Check{Imagem mudou?}
    Build[docker build e push ECR]
    Skip[Reutiliza imagem ECR]
    TF[terraform init e import]
    Apply[terraform apply]
    Deploy([API no ar])

    Push --> GHA
    GHA --> Test
    Test --> Check
    Check -->|sim| Build
    Check -->|não| Skip
    Build --> TF
    Skip --> TF
    TF --> Apply
    Apply --> Deploy
```

O pipeline só executa o deploy se todos os testes passarem. A imagem Docker é reconstruída apenas quando `requirements.txt` ou `Dockerfile` são alterados — o hash MD5 combinado é comparado com a tag `build-hash` armazenada no ECR.

---

## Testes

```bash
pip install -r src/requirements.txt
pip install pytest
PYTHONPATH=src pytest tests/test_api.py
```

Os testes utilizam `MagicMock` para simular o modelo e o DynamoDB — nenhuma chamada real à AWS é feita durante a execução da suite.

---

## Deploy

```bash
cd infra
terraform init
terraform import aws_ecr_repository.titanic_repo titanic-inference-api || true
terraform import aws_dynamodb_table.titanic_table sobreviventes_titanic || true
terraform import aws_iam_role.lambda_exec_role lambda_mlops_exec_role || true
terraform import aws_iam_policy.lambda_policy arn:aws:iam::{account_id}:policy/lambda_mlops_policy || true
terraform import aws_lambda_function.titanic_ml titanic_inference_api || true
terraform apply -auto-approve
```

---

## Tecnologias Utilizadas

| Categoria        | Tecnologia      |
|------------------|-----------------|
| Linguagem        | Python 3.9      |
| ML Framework     | Scikit-learn    |
| Compute          | AWS Lambda      |
| Container        | Docker / ECR    |
| API              | AWS API Gateway |
| Banco de Dados   | AWS DynamoDB    |
| IaC              | Terraform       |
| CI/CD            | GitHub Actions  |
| Documentação API | OpenAPI 3.0     |

---

## Processo de Desenvolvimento

A solução foi construída de forma incremental, com cada decisão técnica respondendo a uma restrição concreta encontrada no caminho.

A arquitetura inicial seguiu o caminho mais direto: Lambda com pacote ZIP, Terraform provisionando os recursos e GitHub Actions orquestrando o pipeline. O código foi estruturado em Clean Architecture desde o início — Controller, Service e Repository — tanto para atender boas práticas quanto para viabilizar testes unitários com mocks sem dependências reais da AWS.

O primeiro obstáculo foi de tamanho: o pacote com `scikit-learn`, `scipy` e `numpy` ultrapassa 50MB no upload direto e 250MB descompactado, invalidando tanto o ZIP quanto o Lambda Layer. A solução foi migrar para **Container Image via ECR**, que suporta até 10GB e é a abordagem recomendada pela AWS para workloads de ML — mantendo todo o código em Python, como exigido.

O segundo desafio foi de estado: o runner efêmero do GitHub Actions descarta o `terraform.tfstate` a cada execução. Sem estado persistido, o Terraform tentava recriar recursos já existentes e falhava com conflitos. A solução adotada foi importar os recursos existentes dinamicamente antes de cada `apply`, usando a AWS CLI para resolver IDs em tempo de execução — uma abordagem pragmática que funciona sem a complexidade de um backend remoto com S3.

A política IAM foi construída de forma iterativa e orientada a erros reais de `AccessDeniedException`, chegando a um conjunto preciso de permissões que aplica o Privilégio Mínimo sem bloquear operações legítimas do Terraform.

Ao final, a solução entrega uma API serverless completamente funcional, com infraestrutura reproduzível, pipeline automatizado, testes isolados e custo operacional próximo de zero para o volume de uso do desafio.

---

## Autora

**Sophie Pyxis de Paula**
GitHub: [@sophie-pyxis](https://github.com/sophie-pyxis)
