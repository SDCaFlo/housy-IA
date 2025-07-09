def get_chat_stage_metadata(latest_messages):
    for msg in reversed(latest_messages):
        try:
            metadata = msg.get("metadata", {})
            if isinstance(metadata, dict) and "stage" in metadata:
                return int(metadata["stage"])
        except Exception:
            continue
    return "extract"