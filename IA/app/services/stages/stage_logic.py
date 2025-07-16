def get_chat_stage_metadata(latest_messages):
    for msg in reversed(latest_messages):
        try:
            metadata = msg.get("metadata", {})
            if isinstance(metadata, dict) and "stage" in metadata:
                return metadata["stage"]
        except Exception:
            continue
    return "extract"


def get_model_message(stage, response):
    model_message = ""
    try:
        match stage:
            case "extract":
                model_message = response["model_response"]
            case "recommend":
                model_message = str(response)
            case _:
                pass
    except Exception as e:
        model_message = f"error matching message: {e}"
    
    return model_message


