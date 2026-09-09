import os

from google import genai


client = genai.Client(
    api_key=os.environ["GEMINI_API_KEY"]
)


def build_prompt(
    query: str,
    matches: list[dict],
) -> str:

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
2. Do not invent or assume facts.
3. If the answer is not supported by the context, say:
   "I couldn't find that information in the uploaded documents."
4. Cite the relevant document name and page number.
5. Keep the answer clear and concise.

DOCUMENT CONTEXT:

{context}

USER QUESTION:

{query}
""".strip()


def generate_answer(
    query: str,
    matches: list[dict],
) -> str:

    prompt = build_prompt(query, matches)

    response = client.models.generate_content(
        model="gemini-3.1-flash-lite",
        contents=prompt,
    )

    return response.text


def generate_answer_stream(
    query: str,
    matches: list[dict],
):

    prompt = build_prompt(query, matches)

    for chunk in client.models.generate_content_stream(
        model="gemini-3.1-flash-lite",
        contents=prompt,
    ):
        if chunk.text:
            yield chunk.text