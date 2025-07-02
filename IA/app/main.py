from fastapi import FastAPI
from app.api.chatbot_endpoint import router
from app.api.chatbot_recovery import router as chat_router
from app.api.embed_endpoint import router as embed_router
from fastapi.middleware.cors import CORSMiddleware




app = FastAPI(
    title="Chatbot API",
    version = "1.0.0",
)


## Configuración de CORS para seguridad
origins = [
    "*",  # Esto permite todo (no recomendado en producción)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Lista de orígenes permitidos
    allow_credentials=True,
    allow_methods=["*"],  # También puedes poner solo ["GET", "POST", ...]
    allow_headers=["*"],
)

# Incluye la ruta de los archivos  api/routes.py
app.include_router(router, prefix='/chatbot')
app.include_router(chat_router, prefix='/chat_history')
app.include_router(embed_router, prefix='/embed_service')


# References: https://apidog.com/articles/how-to-use-fastapi-apirouter/