from PyPDF2 import PdfReader
from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)


def extract_pdf_text(pdf_path):

    reader = PdfReader(pdf_path)

    text = ""

    for page in reader.pages:

        page_text = page.extract_text()

        if page_text:
            text += page_text

    return text


def answer_question(document_text, question):

    prompt = f"""
You are a document question answering assistant.

Answer ONLY using the document content below.

DOCUMENT:
{document_text}

QUESTION:
{question}

If the answer is not found in the document,
say:
"Answer not found in uploaded document."
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response.choices[0].message.content