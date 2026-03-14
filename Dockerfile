FROM public.ecr.aws/lambda/python:3.9

# Copia e instala dependências
COPY src/requirements.txt .
RUN pip install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

# Copia o código-fonte e o modelo para o diretório raiz da Lambda
COPY src/ ${LAMBDA_TASK_ROOT}/

CMD ["lambda_function.lambda_handler"]
