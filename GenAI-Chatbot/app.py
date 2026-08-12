import uuid
from functools import wraps

from flask import (
    Flask,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    flash,
    url_for
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
app.secret_key = config.FLASK_SECRET_KEY


# ============================================================
# Validate configuration
# ============================================================

config.validate_config()


# ============================================================
# Create chatbot
# ============================================================

chatbot = BankingChatbot()


def login_required(view):

    @wraps(view)
    def wrapped(*args, **kwargs):

        if session.get("logged_in"):
            return view(*args, **kwargs)

        if request.endpoint in {"chat", "rebuild_index"}:
            return jsonify({
                "success": False,
                "error": "Login required"
            }), 401

        return redirect(url_for("login"))

    return wrapped


# ============================================================
# Login
# ============================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = str(
            request.form.get("username", "")
        ).strip()

        password = str(
            request.form.get("password", "")
        ).strip()

        if not username or not password:
            flash("Enter both email and password to continue.")

        else:
            session["logged_in"] = True
            session["display_name"] = (
                username.split("@", 1)[0]
                .replace(".", " ")
                .replace("_", " ")
                .title()
            )

            return redirect(
                url_for("dashboard")
            )

    return render_template(
        "login.html"
    )


# ============================================================
# Logout
# ============================================================

@app.get("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("login")
    )


# ============================================================
# Home
# ============================================================

@app.get("/")
def home():

    return render_template(
        "login.html"
    )


# ============================================================
# Dashboard
# ============================================================

@app.get("/dashboard")
@login_required
def dashboard():

    return render_template(
        "index.html",
        display_name=(
            session.get(
                "display_name",
                "Vivek K"
            )
        )
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
@login_required
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
@login_required
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
