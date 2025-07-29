FROM public.ecr.aws/lambda/python:3.9

# Copiar requirements
COPY requirements-embeddings.txt .

# Instalar dependencias
RUN pip install --no-cache-dir -r requirements-embeddings.txt -t ${LAMBDA_TASK_ROOT}

# Copiar código Python
COPY bedrock_service.py ${LAMBDA_TASK_ROOT}/
COPY lambda_function.py ${LAMBDA_TASK_ROOT}/

CMD ["lambda_function.lambda_handler"]
