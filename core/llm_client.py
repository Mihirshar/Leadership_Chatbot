import os
from typing import Generator
from google import genai
from google.genai import types

MODEL = "gemini-2.5-flash"


def _get_client() -> genai.Client:
    api_key = os.environ.get("GOOGLE_API_KEY", "")
    if not api_key:
        raise ValueError(
            "GOOGLE_API_KEY not set. Please set it as an environment variable."
        )
    return genai.Client(api_key=api_key)


def _build_history(conversation_history: list) -> list[types.Content]:
    history = []
    for msg in conversation_history:
        role = "model" if msg["role"] == "assistant" else "user"
        history.append(types.Content(role=role, parts=[types.Part.from_text(text=msg["content"])]))
    return history


def stream_leader_response(
    system_prompt: str,
    conversation_history: list,
    user_message: str,
) -> Generator[str, None, None]:
    client = _get_client()

    config = types.GenerateContentConfig(
        system_instruction=system_prompt,
        max_output_tokens=4096,
        temperature=0.8,
    )

    history = _build_history(conversation_history)
    history.append(types.Content(role="user", parts=[types.Part.from_text(text=user_message)]))

    for chunk in client.models.generate_content_stream(
        model=MODEL,
        contents=history,
        config=config,
    ):
        if chunk.text:
            yield chunk.text


def get_leader_response(
    system_prompt: str,
    conversation_history: list,
    user_message: str,
) -> str:
    client = _get_client()

    config = types.GenerateContentConfig(
        system_instruction=system_prompt,
        max_output_tokens=4096,
        temperature=0.8,
    )

    history = _build_history(conversation_history)
    history.append(types.Content(role="user", parts=[types.Part.from_text(text=user_message)]))

    response = client.models.generate_content(
        model=MODEL,
        contents=history,
        config=config,
    )
    return response.text
