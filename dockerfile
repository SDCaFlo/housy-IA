# Etapa base liviana
FROM python:3.10-slim-bullseye

# Crea directorio de trabajo en el contenedor
WORKDIR /project

# Copia requirements y los instala
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia el código de la app
COPY IA/app ./app

# Comando para ejecutar FastAPI con uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]