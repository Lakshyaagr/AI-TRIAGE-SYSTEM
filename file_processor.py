from pypdf import PdfReader

def read_pdf(filepath):

    reader = PdfReader(filepath)

    text = ""

    for page in reader.pages:
        page_text = page.extract_text()

        if page_text:
            text += page_text

    return text

from bs4 import BeautifulSoup

def read_html(filepath):

    with open(filepath,
              "r",
              encoding="utf-8") as f:

        html = f.read()

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    return soup.get_text()

import pandas as pd

def read_csv(filepath):

    df = pd.read_csv(filepath)

    return df.to_string()