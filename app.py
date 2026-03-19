import streamlit as st
import requests
import re
from bs4 import BeautifulSoup

OLLAMA_URL = "http://host.docker.internal:11434/api/generate"
MODEL_NAME = "phi3:mini"


# -------------------------------
# DOM ANALYZER
# -------------------------------
def analyze_website(url):

    try:
        response = requests.get(url, timeout=8)
        soup = BeautifulSoup(response.text, "html.parser")

        inputs = []
        buttons = []

        valid_types = ["text", "email", "password"]

        for tag in soup.find_all("input"):

            input_type = tag.get("type")

            if input_type in valid_types:

                identifier = tag.get("id") or tag.get("name")

                if identifier and identifier not in inputs:
                    inputs.append(identifier)

            if len(inputs) >= 5:
                break

        for btn in soup.find_all("button"):

            text = btn.text.strip()

            if text and text not in buttons:
                buttons.append(text)

            if len(buttons) >= 3:
                break

        return inputs, buttons

    except Exception:
        return [], []


# -------------------------------
# PROMPT BUILDERS
# -------------------------------
def build_testcase_prompt(url, inputs, buttons):

    return f"""
You are a senior QA engineer.

Generate exactly 5 LOGIN test cases.

URL: {url}
Inputs: {inputs}
Buttons: {buttons}

Return ONLY a table:

Test Case ID | Scenario | Steps | Expected Result

Rules:
- Use IDs TC_LOGIN_01 to TC_LOGIN_05
- Each test case must be exactly one line
- Do not include explanations
"""


def build_playwright_prompt(url, inputs, buttons):

    return f"""
You are an automation engineer.

Generate a Playwright test script.

URL: {url}

Inputs: {inputs}
Buttons: {buttons}

Rules:
- Use Playwright JavaScript syntax
- Open browser
- Navigate to URL
- Fill detected inputs
- Click login button
- Do not include explanations
"""


# -------------------------------
# AI SERVICE
# -------------------------------
def call_ai(prompt):

    try:

        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL_NAME,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.2,
                    "num_predict": 400
                }
            },
            timeout=300
        )

        result = response.json()

        if "response" in result:
            output = result["response"]

            output = re.sub(r"<.*?>", "", output)

            return output.strip()

        return "AI response error"

    except Exception as e:
        return f"AI request failed: {e}"


# -------------------------------
# STREAMLIT UI
# -------------------------------
st.title("AI Smart QA Assistant")

url = st.text_input("Enter Website URL")

if url:

    inputs, buttons = analyze_website(url)

    st.subheader("Detected Elements")

    st.write("Inputs:", inputs)
    st.write("Buttons:", buttons)

    col1, col2 = st.columns(2)

    # TEST CASE GENERATION
    with col1:

        if st.button("Generate Test Cases"):

            prompt = build_testcase_prompt(url, inputs, buttons)

            with st.spinner("Generating test cases..."):

                result = call_ai(prompt)

            st.subheader("Manual Test Cases")

            st.code(result)

    # PLAYWRIGHT GENERATION
    with col2:

        if st.button("Generate Playwright Script"):

            prompt = build_playwright_prompt(url, inputs, buttons)

            with st.spinner("Generating automation script..."):

                result = call_ai(prompt)

            st.subheader("Playwright Automation Script")

            st.code(result)
