from app.core.aws_clients import get_dynamodb_client
from boto3.dynamodb.types import TypeSerializer, TypeDeserializer
from langchain_core.messages import HumanMessage, AIMessage
from app.core.config import DYNAMODB_TABLE
from pydantic import BaseModel, Field
from typing import Literal
from datetime import datetime, timezone
from app.models.PropertyLead import PropertySearchParams
import logging
import json
import uuid

logger = logging.getLogger(__name__)


class BaseMessage(BaseModel):
    content: dict = Field(description="message content")
    role: Literal["user", "assistant"] = Field(description="role")
    content_type: Literal["text", "property_list"] = Field(
        default="text", description="tipo de contenido "
    )
    metadata: dict = Field(default=dict(), description="metadata")


class DeserializedMessage(BaseMessage):
    PK: str = Field(description="Primary Key")
    SK: str = Field(
        description="Time",
        default_factory=lambda: "TIMESTAMP#"
        + datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        + "#"
        + str(uuid.uuid4()),
    )


class ChatHistory:
    def __init__(self, user_id: str, conv_id: str):
        self.client = get_dynamodb_client()
        self.primary_key = "USER#" + user_id + "#CONV#" + conv_id
        self.context_length = self.get_context_length()
        self.len = 0
        self.serialized_messages = []  # guarda mensajes serialiados
        self.deserialized_messages = []  # guarda mensajes deserializazdos

    """Section: Message History Modifiers"""

    def add_message(
        self, content: dict, role: str, content_type: str, metadata: dict = dict()
    ):
        """Agrega un mensaje a la lista de mensajes"""
        item = DeserializedMessage(
            PK=self.primary_key,
            content=content,
            role=role,
            metadata=metadata,
            content_type=content_type,
        )
        self.deserialized_messages.append(item.model_dump())
        self.serialized_messages.append(self.serialize_item(item))

    def deserialize_messages(self):
        """Deserialiaz los mensajes"""
        self.deserialized_messages = []
        try:
            for message in self.serialized_messages:
                self.deserialized_messages.append(self.deserialize_item(message))
        except Exception as e:
            return e

    def serialize_item(self, model: DeserializedMessage):
        """Serializa un mensaje en formato serializado para dynamodb"""
        from decimal import Decimal

        def convert_floats_to_decimal(obj):
            if isinstance(obj, float):
                return Decimal(
                    str(obj)
                )  # Nunca uses Decimal(float), siempre convierte a str primero
            elif isinstance(obj, list):
                return [convert_floats_to_decimal(item) for item in obj]
            elif isinstance(obj, dict):
                return {k: convert_floats_to_decimal(v) for k, v in obj.items()}
            else:
                return obj

        raw_dict = model.model_dump()
        clean_dict = convert_floats_to_decimal(raw_dict)

        serializer = TypeSerializer()
        serialized_item = {k: serializer.serialize(v) for k, v in clean_dict.items()}

        return serialized_item

    def deserialize_item(self, dynamo_object: dict) -> dict:
        """Deserializador de items en formato diccionario / JSON"""
        deserializer = TypeDeserializer()
        return {k: deserializer.deserialize(v) for k, v in dynamo_object.items()}

    def get_langchain_history(self):
        "Returns a message history in Langchain BaseMessage format"

        def message_mapper(deserialized_message):
            """Maps a single message"""
            type_map = {
                "user": HumanMessage,
                "assistant": AIMessage,
                "ai": AIMessage,
                "human": HumanMessage,
            }
            langchain_message = type_map.get(deserialized_message.get("role"))(
                content=deserialized_message.get("content", dict()).get(
                    "text", "<List of recommended properties>"
                )
            )
            return langchain_message

        langchain_history = []
        try:
            logger.info(
                'Function "get_langchain_history": Attempting to format conversation'
            )
            for message in self.deserialized_messages:
                langchain_history.append(message_mapper(message))
        except Exception as e:
            logger.error(
                f'Function "get_langchain_history": failed to convert history. Detail:{e}'
            )
            logger.info('Function "get_langchain_history": Returning empty list')

        return langchain_history

    """Section: Database interaction"""

    def save_new_messages(self):
        """Guarda el estado actual de los mensajes en dynamodb"""
        new_len = len(self.serialized_messages)
        save_index = (-1) * (new_len - self.len)
        for message in self.serialized_messages[save_index::]:
            self.client.put_item(TableName=DYNAMODB_TABLE, Item=message)
        self.len = new_len

    def get_messages(self, limit: int = 2):
        """Recupera mensajes y guardar en self.messages"""
        self.serialized_messages = []  # inicializamos
        self.deserialized_messages = []

        if limit < 1:
            limit = 1

        response = self.client.query(
            TableName="ChatMessages",
            KeyConditionExpression="PK = :pk_val",
            ExpressionAttributeValues={":pk_val": {"S": self.primary_key}},
            ScanIndexForward=False,
            Limit=limit,
        )

        self.serialized_messages = response.get("Items", [])[::-1]
        self.len = len(self.serialized_messages)
        self.deserialize_messages()

        return response

    """Section: Utils"""

    def retrieve_current_stage(self) -> tuple[str, int]:
        """Devuelve el último estado y la cantidad de veces"""

        try:
            stage_list = []
            for message in self.deserialized_messages:
                stage_list.append(
                    message.get("metadata", {}).get("stage", "query_user")
                )

            last_stage = stage_list[-1]

            stage_count = 0
            for stage in stage_list[::-1]:
                if stage == last_stage:
                    stage_count += 1
                else:
                    break

            return last_stage, stage_count

        except Exception as e:
            print(f"Failed to retrieve stages: {e}, returning default stage")
            return "query_user", 0

    def retrieve_current_lead(self) -> "PropertySearchParams":
        "Retrieves the lead from the last message in the PropertySearchParams class format"
        try:
            lead: str = (
                self.deserialized_messages[-1].get("metadata", {}).get("lead", {})
            )
            if lead == {}:
                return PropertySearchParams()
            else:
                return PropertySearchParams(**json.loads(lead))
        except Exception as e:
            logger.info(f"Failed to retrieve lead: {e}, returning default lead")
            return PropertySearchParams()

    def get_context_length(self):
        "Recovers the context length of the conversation"
        self.get_messages(limit=1)
        try:
            logger.info("Method get_context_length: Retrieving context length")
            context_length = int(
                self.deserialized_messages[0].get("metadata").get("conversation_length")
            )
        except Exception as e:
            logger.error(
                f"Method get_context_length: Could not get context_length/conversation_length. Detail: {e}"
            )
            logger.info("Method get_context_length: Setting context_length to 0")
            context_length = 0
        self.context_length = 0
        return context_length

    def set_context_length(self, value: int):
        self.deserialized_messages[-1]["metadata"]["conversation_length"] = value
