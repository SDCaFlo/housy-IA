from typing import List, Dict
from app.services.stages import stage1_extract, stage2_recommendation
from app.models.ChatMessage import ChatMessage
from app.services.embeddings.search_opensearch import (
    search_similar_properties,
    hay_propiedades_en_ciudad
)
from app.utils.intention_detection import tiene_intencion_busqueda
# Ya NO importar extract_city_chain que usaba langchain
# En lugar de eso usaremos llamada directa a call_model para extraer ciudad
from app.services.llm_contact import call_model  # nueva función para llamar Bedrock


def format_message(message: str, role: str = "user"):
    return {'role': role, 'content': [{'text': message}]}


def format_conversation(conversation_history):
    formatted_history = []
    for item in conversation_history['Items'][::-1]:
        text = item['message']['S']
        role = item['role']['S']
        metadata = item.get("metadata", {}).get("M", {})
        formatted_history.append({
            'role': role,
            'message': text,
            'metadata': {k: v.get('N', v.get('S')) for k, v in metadata.items()} if metadata else None
        })
    return formatted_history


def get_chat_stage_metadata(latest_messages):
    for msg in reversed(latest_messages):
        try:
            metadata = msg.get("metadata", {})
            if isinstance(metadata, dict) and "stage" in metadata:
                return int(metadata["stage"])
        except Exception:
            continue
    return 1


def extract_city_from_message(message: str) -> str:
    """
    Llama a call_model con un prompt para extraer la ciudad desde el texto del usuario.
    """
    system_prompt = "Extrae el nombre de la ciudad del siguiente texto. Devuelve solo el nombre de la ciudad."
    history = [{"role": "user", "content": [{"text": message}]}]
    city = call_model(history, system_prompt)
    return city.strip().lower()


def proccess_chat_turn(user_id: str, conv_id: str, message: str):
    from app.core.aws_clients import get_dynamodb_client
    from app.services.dynamodb_queries import (
        get_latests_messages,
        response_to_conversation,
        serialize_message,
        write_message
    )

    primary_key = f"USER#{user_id}#CONV#{conv_id}"
    dynamodb = get_dynamodb_client()
    latest_messages = get_latests_messages(dynamodb, primary_key, limit=10)
    latest_conversation = response_to_conversation(latest_messages)
    latest_conversation.append(format_message(message, role="user"))

    # Guardar mensaje del usuario
    write_message(dynamodb, "ChatMessages",
                  serialize_message(message, primary_key, role='user'))

    chat_stage = get_chat_stage_metadata(latest_messages)

    if chat_stage == 1:
        if tiene_intencion_busqueda(message):
            ciudad = extract_city_from_message(message)

            if not hay_propiedades_en_ciudad(ciudad):
                msg = f"Lo siento, no tenemos propiedades en '{ciudad.title()}'. ¿Quieres buscar en otra zona?"
                write_message(dynamodb, "ChatMessages",
                              serialize_message(msg, primary_key, role='assistant', metadata={"stage": 1}))
                return {
                    "stage": "stage_1_no_results",
                    "data": {"message": msg}
                }

            resultados = search_similar_properties(message, ciudad=ciudad, k=3)
            resultados_ordenados = sorted(resultados, key=lambda x: x["score"], reverse=True)

            texto_recomendacion = "🏡 Estas propiedades podrían interesarte:\n\n"
            ids = []
            for i, r in enumerate(resultados_ordenados, 1):
                texto_recomendacion += (
                    f"🏠 Propiedad recomendada #{i} (ID: {r['id']}, Score: {r['score']:.4f}):\n{r['text']}\n\n"
                )
                ids.append(r["id"])

            msg = texto_recomendacion
            write_message(dynamodb, "ChatMessages",
                          serialize_message(msg, primary_key, role='assistant', metadata={"stage": 2, "ciudad": ciudad}))

            return {
                "stage": "stage_2_recommendation",
                "data": {"message": msg, "ids": ids}
            }

        # Si no tiene intención clara, seguir preguntando
        response = stage1_extract.handle(latest_conversation)
        write_message(dynamodb, "ChatMessages",
                      serialize_message(response, primary_key, role='assistant', metadata={"stage": 1}))

        return {
            "stage": "stage_1_extract",
            "data": {"message": response}
        }

    elif chat_stage == 2:
        ciudad = extract_city_from_message(message)

        if not hay_propiedades_en_ciudad(ciudad):
            msg = f"No tenemos propiedades en '{ciudad.title()}'. ¿Quieres buscar en otra zona?"
            write_message(dynamodb, "ChatMessages",
                          serialize_message(msg, primary_key, role='assistant', metadata={"stage": 2}))
            return {
                "stage": "stage_2_no_results",
                "data": {"message": msg}
            }

        resultados = search_similar_properties(message, ciudad=ciudad, k=3)
        resultados_ordenados = sorted(resultados, key=lambda x: x["score"], reverse=True)

        texto_recomendacion = "🏡 Estas propiedades podrían interesarte:\n\n"
        ids = []
        for i, r in enumerate(resultados_ordenados, 1):
            texto_recomendacion += (
                f"🏠 Propiedad recomendada #{i} (ID: {r['id']}, Score: {r['score']:.4f}):\n{r['text']}\n\n"
            )
            ids.append(r["id"])

        msg = texto_recomendacion
        write_message(dynamodb, "ChatMessages",
                      serialize_message(msg, primary_key, role='assistant', metadata={"stage": 2, "ciudad": ciudad}))

        return {
            "stage": "stage_2_recommendation",
            "data": {"message": msg, "ids": ids}
        }

    # Fallback reinicio de conversación
    response = "Gracias por tu interés. ¿Te gustaría comenzar una nueva búsqueda?"
    write_message(dynamodb, "ChatMessages",
                  serialize_message(response, primary_key, role='assistant', metadata={"stage": 1}))

    return {
        "stage": "reset",
        "data": {"message": response}
    }
