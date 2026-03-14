provider "aws" {
  region = "us-east-1"
}

resource "aws_dynamodb_table" "titanic_table" {
  name         = "sobreviventes_titanic"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "id"

  attribute {
    name = "id"
    type = "S"
  }
}

# Role assumida pela Lambda durante a execução — trust policy obrigatória
resource "aws_iam_role" "lambda_exec_role" {
  name = "lambda_mlops_exec_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect    = "Allow"
        Principal = { Service = "lambda.amazonaws.com" }
        Action    = "sts:AssumeRole"
      }
    ]
  })
}

# Política customizada aplicando Privilégio Mínimo: apenas CloudWatch Logs e DynamoDB
resource "aws_iam_policy" "lambda_policy" {
  name = "lambda_mlops_policy"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        # Permissão para gravar logs no CloudWatch
        Effect   = "Allow"
        Action   = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        # Permissão restrita ao CRUD da tabela sobreviventes_titanic
        Effect   = "Allow"
        Action   = [
          "dynamodb:PutItem",
          "dynamodb:GetItem",
          "dynamodb:DeleteItem",
          "dynamodb:Scan"
        ]
        Resource = aws_dynamodb_table.titanic_table.arn
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_attach" {
  role       = aws_iam_role.lambda_exec_role.name
  policy_arn = aws_iam_policy.lambda_policy.arn
}

# Compacta src/ em ZIP para deploy — hash garante atualização automática ao mudar o código
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../src"
  output_path = "${path.module}/lambda.zip"
}

resource "aws_lambda_function" "titanic_ml" {
  filename         = data.archive_file.lambda_zip.output_path
  function_name    = "titanic_inference_api"
  role             = aws_iam_role.lambda_exec_role.arn
  handler          = "lambda_function.lambda_handler"
  runtime          = "python3.9"
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  # 30s para acomodar Cold Start do Scikit-Learn; 512MB para carregamento do modelo pkl
  timeout          = 30
  memory_size      = 512

  environment {
    variables = {
      DYNAMODB_TABLE = aws_dynamodb_table.titanic_table.name
    }
  }
}

# API Gateway provisionado via contrato OpenAPI — lambda_invoke_arn injetado pelo templatefile
resource "aws_api_gateway_rest_api" "titanic_api" {
  name = "titanic-ml-api"
  body = templatefile("${path.module}/../docs/openapi.yaml", {
    lambda_invoke_arn = aws_lambda_function.titanic_ml.invoke_arn
  })
}

resource "aws_lambda_permission" "apigw_invoke_permission" {
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.titanic_ml.function_name
  principal     = "apigateway.amazonaws.com"
  # Restringe invocação apenas a esta API, evitando acesso por outros Gateways
  source_arn    = "${aws_api_gateway_rest_api.titanic_api.execution_arn}/*/*"
}

# create_before_destroy garante zero-downtime ao republicar a API
resource "aws_api_gateway_deployment" "api_deployment" {
  rest_api_id = aws_api_gateway_rest_api.titanic_api.id

  triggers = {
    redeployment = sha1(jsonencode(aws_api_gateway_rest_api.titanic_api.body))
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_api_gateway_stage" "api_stage" {
  deployment_id = aws_api_gateway_deployment.api_deployment.id
  rest_api_id   = aws_api_gateway_rest_api.titanic_api.id
  stage_name    = "v1"
}
