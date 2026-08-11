import uuid

from flask import (
    Flask,
    jsonify,
    render_template,
    request
)

import config

from chatbot import BankingChatbot

from db import test_connection


# ============================================================
# Flask
# ============================================================

app = Flask(
    __name__
)


# ============================================================
# Validate configuration
# ============================================================

config.validate_config()


# ============================================================
# Create chatbot
# ============================================================

chatbot = BankingChatbot()


# ============================================================
# Home
# ============================================================

@app.get("/")
def home():

    return render_template(
        "index.html"
    )


# ============================================================
# Health
# ============================================================

@app.get("/health")
def health():

    oracle_status = "connected"

    try:

        test_connection()

    except Exception as exc:

        oracle_status = (
            f"error: {exc}"
        )

    return jsonify({

        "status": "ok",

        "oracle": oracle_status,

        "gemini_model": (
            config.GEMINI_MODEL
        )
    })


# ============================================================
# Chat
# ============================================================

@app.post("/chat")
def chat():

    data = (
        request
        .get_json(
            silent=True
        )
        or {}
    )

    question = str(
        data.get(
            "message",
            ""
        )
    ).strip()

    session_id = str(
        data.get(
            "session_id"
        )
        or uuid.uuid4()
    )

    try:

        result = chatbot.response(
            session_id,
            question
        )

        return jsonify({

            "success": True,

            "session_id": (
                session_id
            ),

            **result
        })

    except Exception as exc:

        app.logger.exception(
            "Chat request failed"
        )

        return jsonify({

            "success": False,

            "error": str(exc)

        }), 500


# ============================================================
# Rebuild PDF index
# ============================================================

@app.post("/rebuild-index")
def rebuild_index():

    try:

        chunks = (
            chatbot
            .rebuild_documents()
        )

        return jsonify({

            "success": True,

            "chunks_indexed": chunks
        })

    except Exception as exc:

        app.logger.exception(
            "RAG indexing failed"
        )

        return jsonify({

            "success": False,

            "error": str(exc)

        }), 500


# ============================================================
# Run
# ============================================================

if __name__ == "__main__":

    app.run(

        host=config.FLASK_HOST,

        port=config.FLASK_PORT,

        debug=config.FLASK_DEBUG
    )