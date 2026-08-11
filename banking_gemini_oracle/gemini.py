from langchain_google_genai import (
    ChatGoogleGenerativeAI
)

import config


def get_llm():

    if not config.GOOGLE_API_KEY:

        raise RuntimeError(
            "GOOGLE_API_KEY is not configured."
        )

    return ChatGoogleGenerativeAI(

        model=config.GEMINI_MODEL,

        temperature=0,

        google_api_key=config.GOOGLE_API_KEY,

        max_retries=2
    )