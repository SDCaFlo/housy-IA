# housy-IA

CURRENT STATUS:
- dynamodb operations: OK
- chatbot conversation: OK . Stage 1. Stage 2.
- FAST API endpoints deployed.
- Dockerfile creation: OK.
- Deploy in AWS : Ok

NEXT STEPS:
- Add Chatbot stage 3 ( In proccess)


FUTURE FIXES:
- Async functions for DynamoDB writing
- Log implementation


Websites:
chatbot-api: https://chatbot-api.housycorp.com/docs
backend: https://backend.housycorp.com/api

```mermaid
stateDiagram-v2
    [*] --> Start: Inicio de conversación

    Start --> NER: Recibir mensaje + extraer entidades
    NER --> CheckSlots: Revisar estados en DynamoDB

    
    state CheckSlots {
        [*] --> Missing: Hay slots en missing
        [*] --> Pending: Hay slots en pending_validation
        [*] --> AllValidated: Todos los slots están validated

        Missing --> AskQuestion: Formular pregunta sobre slot faltante
        Pending --> ValidateTool: Validar con Nominatim u otra herramienta
        AllValidated --> Search: Realizar búsqueda

        AskQuestion --> NER: Recibir respuesta y extraer nueva entidad
        ValidateTool --> ConfirmAddress: Preguntar confirmación si es ambigua
        ValidateTool --> AutoValidate: Confirmar automáticamente si score alto
        ConfirmAddress --> NER
        AutoValidate --> NER
    }

    Search --> [*]: Fin del flujo
```