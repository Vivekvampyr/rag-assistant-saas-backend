from google import genai
from app.core.config import settings

client = genai.Client(
    api_key=settings.GEMINI_API_KEY
)


MODEL_NAME = "gemini-3.1-flash-lite"


def build_prompt(
    question: str,
    matches: list[dict],
) -> str:
    """
    Build a grounded prompt from retrieved document chunks.
    """

    context_parts = []

    for index, match in enumerate(matches, start=1):
        context_parts.append(
            f"""
SOURCE {index}
Document: {match["filename"]}
Page: {match["page_number"]}

Content:
{match["content"]}
""".strip()
        )

    context = "\n\n".join(context_parts)

    return f"""
You are a document-grounded AI assistant.

Answer the user's question using ONLY the provided document context.

Rules:
1. Do not use outside knowledge.
2. Do not invent facts.
3. If the answer is not supported by the context, say:
   "I couldn't find that information in the uploaded documents."
4. Answer directly and clearly.
5. Cite the relevant document name and page number.
6. Do not mention information that is not supported by the sources.

DOCUMENT CONTEXT:

{context}

USER QUESTION:

{question}
""".strip()


def generate_answer(
    question: str,
    matches: list[dict],
) -> str:
    """
    Generate a grounded answer using retrieved chunks.
    """

    prompt = build_prompt(
        question=question,
        matches=matches,
    )

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
    )

    if not response.text:
        raise RuntimeError("Gemini returned an empty response.")

    return response.text


def generate_answer_stream(
    question: str,
    matches: list[dict],
):
    """
    Stream a grounded answer from Gemini.
    """

    prompt = build_prompt(
        question=question,
        matches=matches,
    )

    for chunk in client.models.generate_content_stream(
        model=MODEL_NAME,
        contents=prompt,
    ):
        if chunk.text:
            yield chunk.text