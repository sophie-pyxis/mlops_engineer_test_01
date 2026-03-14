# Define o provedor de nuvem que o Terraform ira gerenciar (AWS)
provider "aws" {
  # Define a regiao padrao para a criacao dos recursos (Norte da Virginia)
  region = "us-east-1"
}

# Declara a criacao de uma tabela no Amazon DynamoDB para persistencia dos dados
resource "aws_dynamodb_table" "titanic_table" {
  # Define o nome da tabela no banco de dados
  name         = "sobreviventes_titanic"
  # Define o modo de cobranca sob demanda (estrategia FinOps para baixo volume)
  billing_mode = "PAY_PER_REQUEST" 
  # Define a chave primaria (Partition Key) da tabela
  hash_key     = "id"

  # Define o esquema do atributo que serve como chave primaria
  attribute {
    # Nome do atributo
    name = "id"
    # Tipo de dado do atributo (S = String)
    type = "S"
  }
}

# Cria uma funcao (Role) no IAM para ser assumida pela AWS Lambda
resource "aws_iam_role" "lambda_exec_role" {
  # Nome da Role de execucao
  name = "lambda_mlops_exec_role"
  # Define a politica de confianca permitindo que o servico Lambda assuma esta role
  assume_role_policy = jsonencode({
    # Versao da linguagem de politica do IAM
    Version = "2012-10-17"
    # Declaracao das permissoes
    Statement =
  })
}

# Cria uma politica (Policy) customizada aplicando o Principio do Privilegio Minimo
resource "aws_iam_policy" "lambda_policy" {
  # Nome da politica
  name = "lambda_mlops_policy"
  # Estrutura JSON com as regras de permissao
  policy = jsonencode({
    # Versao da sintaxe
    Version = "2012-10-17"
    # Lista de declaracoes de acesso
    Statement =
        # Permite gravar logs em qualquer grupo de recursos de log da conta
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        # Permite acoes de manipulacao de dados no banco
        Effect = "Allow"
        # Acoes do DynamoDB necessarias para o CRUD da API
        Action =
        # Restringe estritamente o acesso apenas a tabela 'sobreviventes_titanic' recem criada
        Resource = aws_dynamodb_table.titanic_table.arn 
      }
    ]
  })
}

# Anexa a politica de privilegios restritos a Role da Lambda
resource "aws_iam_role_policy_attachment" "lambda_attach" {
  # Referencia o nome da Role
  role       = aws_iam_role.lambda_exec_role.name
  # Referencia o identificador unico (ARN) da politica
  policy_arn = aws_iam_policy.lambda_policy.arn
}

# Compacta o diretorio da aplicacao (codigo + modelo) em um arquivo ZIP para deploy
data "archive_file" "lambda_zip" {
  # Define o tipo de compressao
  type        = "zip"
  # Diretorio de origem que contem a logica de negocio e o pkl
  source_dir  = "${path.module}/../src"
  # Caminho de destino e nome do arquivo gerado
  output_path = "${path.module}/lambda.zip"
}

# Provisiona a funcao AWS Lambda (Computacao Serverless)
resource "aws_lambda_function" "titanic_ml" {
  # Caminho do pacote ZIP gerado no passo anterior
  filename         = data.archive_file.lambda_zip.output_path
  # Nome descritivo da funcao na AWS
  function_name    = "titanic_inference_api"
  # Associa a Role de IAM com privilegios restritos a esta Lambda
  role             = aws_iam_role.lambda_exec_role.arn
  # Indica o arquivo de entrada e o metodo principal (Entrypoint)
  handler          = "lambda_function.lambda_handler"
  # Define o interpretador e a versao do ambiente de execucao
  runtime          = "python3.9"
  # Gera um hash para o Terraform identificar mudancas no codigo e forcar atualizacao
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  # Tempo maximo de execucao permitido (30 segundos para garantir a inferencia)
  timeout          = 30
  # Aloca 512MB de RAM, otimizando o carregamento da biblioteca Scikit-Learn
  memory_size      = 512 

  # Injeta variaveis de ambiente no contexto da execucao
  environment {
    # Variaveis disponiveis para o codigo Python
    variables = {
      # Passa o nome dinamico da tabela do DynamoDB gerada
      DYNAMODB_TABLE = aws_dynamodb_table.titanic_table.name
    }
  }
}

# Provisiona o API Gateway (Roteador Edge) lendo o contrato OpenAPI (Swagger)
resource "aws_api_gateway_rest_api" "titanic_api" {
  # Nome da API no console da AWS
  name = "titanic-ml-api"
  # Le o arquivo openapi.yaml e substitui a variavel interna pela ARN real da Lambda
  body = templatefile("${path.module}/../docs/openapi.yaml", {
    # Mapeamento da string contida no Swagger para o identificador da Lambda gerada
    lambda_invoke_arn = aws_lambda_function.titanic_ml.invoke_arn
  })
}

# Concede permissao para o API Gateway acionar (invocar) a funcao Lambda
resource "aws_lambda_permission" "apigw_invoke_permission" {
  # Define a acao de invocacao
  action        = "lambda:InvokeFunction"
  # Referencia a funcao Lambda especifica
  function_name = aws_lambda_function.titanic_ml.function_name
  # Define a entidade confiavel (API Gateway)
  principal     = "apigateway.amazonaws.com"
  # Restringe a permissao apenas para chamadas oriundas desta API exata
  source_arn    = "${aws_api_gateway_rest_api.titanic_api.execution_arn}/*/*"
}

# Cria o pacote de publicacao (Deployment) do estado atual do API Gateway
resource "aws_api_gateway_deployment" "api_deployment" {
  # Associa ao ID da API criada
  rest_api_id = aws_api_gateway_rest_api.titanic_api.id
  # Define gatilhos para forcar novo deploy se o Swagger mudar
  triggers = {
    # Calcula o hash do corpo do Swagger para detectar alteracoes
    redeployment = sha1(jsonencode(aws_api_gateway_rest_api.titanic_api.body))
  }
  # Garante disponibilidade zero-downtime (cria novo recurso antes de destruir o antigo)
  lifecycle {
    create_before_destroy = true
  }
}

# Define o estagio de ambiente (Ex: Producao, Homologacao, v1)
resource "aws_api_gateway_stage" "api_stage" {
  # Vincula este estagio ao deployment recem gerado
  deployment_id = aws_api_gateway_deployment.api_deployment.id
  # Relaciona o estagio a raiz da API
  rest_api_id   = aws_api_gateway_rest_api.titanic_api.id
  # Define o nome do ambiente que fara parte da URL (ex: /v1/sobreviventes)
  stage_name    = "v1"
}