from collections import defaultdict, deque
from threading import Lock

from langchain_core.messages import (
    HumanMessage,
    AIMessage,
    SystemMessage
)

from gemini import get_llm

from rag import BankingRAG

from sql_agent import (
    ask_oracle,
    format_oracle_context
)


def normalize_ai_message_content(content):

    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):
        text_parts = []

        for part in content:

            if isinstance(part, str):
                text_parts.append(part)

            elif isinstance(part, dict):
                text_value = part.get("text")

                if isinstance(text_value, str):
                    text_parts.append(text_value)

                else:
                    fallback = part.get("content")

                    if isinstance(fallback, str):
                        text_parts.append(fallback)

            else:
                if hasattr(part, "text"):
                    text_value = getattr(part, "text")

                    if isinstance(text_value, str):
                        text_parts.append(text_value)

        return "\n".join(text_parts).strip()

    if content is None:
        return ""

    return str(content).strip()


class BankingChatbot:

    def __init__(self):

        self.llm = get_llm()

        self.rag = BankingRAG()

        self.history = defaultdict(
            lambda: deque(
                maxlen=10
            )
        )

        self.lock = Lock()

    # --------------------------------------------------------
    # Rebuild PDF vector index
    # --------------------------------------------------------

    def rebuild_documents(self):

        return self.rag.build_index()

    # --------------------------------------------------------
    # Decide if Oracle should be queried
    # --------------------------------------------------------

    def is_database_question(
        self,
        question
    ):

        question = (
            question
            .lower()
        )

        keywords = [

            "account",

            "account details",

            "balance",

            "savings",

            "current account",

            "customer",

            "customer details",

            "credit score",

            "credit card balance",

            "loan",

            "loan balance",

            "transaction",

            "profile",

            "my details"
        ]

        return any(
            keyword in question
            for keyword in keywords
        )

    # --------------------------------------------------------
    # Generate response
    # --------------------------------------------------------

    def response(
        self,
        session_id,
        question
    ):

        question = question.strip()

        if not question:

            return {
                "answer": (
                    "Please enter a question."
                ),
                "sql": None,
                "sql_error": None
            }

        oracle_context = ""

        sql_used = None

        sql_error = None

        # ====================================================
        # Oracle
        # ====================================================

        if self.is_database_question(
            question
        ):

            try:

                result = ask_oracle(
                    question
                )

                oracle_context = (
                    format_oracle_context(
                        result
                    )
                )

                sql_used = result[
                    "sql"
                ]

            except Exception as exc:

                sql_error = str(
                    exc
                )

        # ====================================================
        # PDF RAG
        # ====================================================

        pdf_context = (
            self.rag.get_context(
                question
            )
        )

        # ====================================================
        # Chat history
        # ====================================================

        with self.lock:

            previous_messages = list(
                self.history[
                    session_id
                ]
            )

        # ====================================================
        # Gemini system prompt
        # ====================================================

        system_prompt = """

You are a professional banking
helpdesk assistant.

You have access to two information sources:

1. ORACLE DATABASE CONTEXT

This contains customer and account
information retrieved from Oracle.

2. BANKING POLICY CONTEXT

This contains information retrieved
from approved banking policy PDFs.

IMPORTANT RULES:

- Answer using the supplied context.

- Never invent customer information.

- Never invent account balances.

- Never invent credit scores.

- Never invent policy rules.

- If information is unavailable,
  clearly say that you cannot find it.

- Never reveal database passwords.

- Never reveal API keys.

- Never reveal internal system credentials.

- Do not expose internal implementation
  details unless specifically required.

- Use Oracle information for
  customer/account questions.

- Use PDF information for
  banking policy questions.

- If both are relevant, use both.

- Keep the answer professional,
  concise and understandable.

"""

        user_prompt = f"""

USER QUESTION:

{question}


ORACLE DATABASE CONTEXT:

{oracle_context or "No Oracle context available."}


BANKING POLICY CONTEXT:

{pdf_context}


Answer the user's question using
only the available context.

"""

        messages = [

            SystemMessage(
                content=system_prompt
            )
        ]

        messages.extend(
            previous_messages
        )

        messages.append(
            HumanMessage(
                content=user_prompt
            )
        )

        # ====================================================
        # Gemini
        # ====================================================

        response = self.llm.invoke(
            messages
        )

        answer = normalize_ai_message_content(
            response.content
        )

        # ====================================================
        # Store conversation
        # ====================================================

        with self.lock:

            self.history[
                session_id
            ].append(

                HumanMessage(
                    content=question
                )
            )

            self.history[
                session_id
            ].append(

                AIMessage(
                    content=answer
                )
            )

        return {

            "answer": answer,

            "sql": sql_used,

            "sql_error": sql_error
        }