"""Mocking (slide 93): code that calls an LLM API, tested without ever calling it."""
from __future__ import annotations

MODEL = "llama-3.3-70b-versatile"


def ask_groq(question: str, client=None) -> str:
    """Send a question to Groq and return the answer."""
    if not question.strip():
        raise ValueError("Question cannot be empty")
    if client is None:
        from groq import Groq  # imported here, so the tests don't need the package
        client = Groq()        # reads GROQ_API_KEY from the environment
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": question}],
        max_tokens=1024,
    )
    return response.choices[0].message.content


def ask_with_retry(question: str, client=None, attempts: int = 3) -> str:
    """Same as ask_groq, but tries again when the API fails."""
    last_error = None
    for _ in range(attempts):
        try:
            return ask_groq(question, client)
        except ValueError:
            raise  # bad input: asking again won't help
        except Exception as error:  # API down, timeout, rate limit...
            last_error = error
    raise last_error


if __name__ == "__main__":
    # Real call: needs `pip install groq` and GROQ_API_KEY. The tests never do this.
    print(ask_groq("What is 2+2?"))
