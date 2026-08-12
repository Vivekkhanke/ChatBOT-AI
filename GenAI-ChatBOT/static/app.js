const chat =
    document.getElementById("chat");

const form =
    document.getElementById("chatForm");

const input =
    document.getElementById("message");

const statusBox =
    document.getElementById("status");


let sessionId =
    localStorage.getItem(
        "banking_session_id"
    );


if (!sessionId) {

    sessionId =
        crypto.randomUUID();

    localStorage.setItem(
        "banking_session_id",
        sessionId
    );
}


function addMessage(
    text,
    type
) {

    const message =
        document.createElement(
            "div"
        );

    message.className =
        `message ${type}`;

    message.textContent =
        text;

    chat.appendChild(
        message
    );

    chat.scrollTop =
        chat.scrollHeight;
}


function useExample(
    text
) {

    input.value = text;

    input.focus();
}


form.addEventListener(
    "submit",
    async function(event) {

        event.preventDefault();

        const message =
            input.value.trim();

        if (!message) {

            return;
        }


        addMessage(
            message,
            "user"
        );


        input.value = "";

        statusBox.textContent =
            "Gemini is thinking...";


        try {

            const response =
                await fetch(
                    "/chat",
                    {
                        method: "POST",

                        headers: {
                            "Content-Type":
                                "application/json"
                        },

                        body: JSON.stringify({

                            session_id:
                                sessionId,

                            message:
                                message
                        })
                    }
                );


            const data =
                await response.json();


            if (!data.success) {

                addMessage(
                    `Error: ${data.error}`,
                    "bot"
                );

                return;
            }


            sessionId =
                data.session_id;


            localStorage.setItem(
                "banking_session_id",
                sessionId
            );


            addMessage(
                data.answer,
                "bot"
            );


            if (data.sql) {

                console.log(
                    "Oracle SQL:",
                    data.sql
                );
            }


            if (data.sql_error) {

                console.warn(
                    "Oracle SQL error:",
                    data.sql_error
                );
            }

        }

        catch (error) {

            addMessage(
                `Request failed: ${error}`,
                "bot"
            );

        }

        finally {

            statusBox.textContent =
                "";
        }

    }
);