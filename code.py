import streamlit as st
import pandas as pd
import sqlite3
import os
import re
import plotly.express as px

from dotenv import load_dotenv
from google import genai


load_dotenv()

client = genai.Client(
    api_key=os.getenv("API_KEY")
)


FORBIDDEN_KEYWORDS = [
    "DROP", "DELETE", "UPDATE", "INSERT", "ALTER",
    "TRUNCATE", "CREATE", "REPLACE", "ATTACH", "DETACH",
    "PRAGMA", "VACUUM", "GRANT", "REVOKE"
]


def validate_sql(sql: str) -> tuple[bool, str]:


    cleaned = sql.strip()

    if not cleaned:
        return False, 

    if not re.match(r"^\s*(SELECT|WITH)\b", cleaned, re.IGNORECASE):
        return False, 

    statements = [s for s in cleaned.split(";") if s.strip()]
    if len(statements) > 1:
        return False, 

    upper_sql = cleaned.upper()
    for keyword in FORBIDDEN_KEYWORDS:
        if re.search(rf"\b{keyword}\b", upper_sql):
            return False, f"استفاده از دستور «{keyword}» مجاز نیست."

    return True, ""



@st.cache_data(show_spinner=False)
def generate_sql(question, schema):

    prompt = f"""
You are an expert SQLite developer.

Your task:
Convert user's natural language question into SQL.

Database Schema:

{schema}


Rules:
- Return ONLY SQL.
- Use SQLite syntax.
- Only generate SELECT statements. Never modify data.
- Do not use markdown.
- Do not explain.


User Question:

{question}
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    sql = response.text


    sql = sql.replace("```sql", "")
    sql = sql.replace("```", "")
    sql = sql.strip()

    return sql


@st.cache_data(show_spinner=False)
def explain_result(question: str, result_csv: str) -> str:

    prompt = f"""
You are a helpful data analyst.

The user asked this question:
{question}

Here is the query result (as CSV):
{result_csv}

Task:
Write a short, clear, natural-language answer to the user's question
based on this data. Respond in the same language as the user's question.
Do not mention SQL or CSV. Just answer naturally, like a human analyst.
Keep it concise (2-4 sentences).
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    return response.text.strip()


@st.cache_data(show_spinner=False)
def run_query_cached(db_path: str, sql: str) -> pd.DataFrame:
    conn = sqlite3.connect(db_path)
    try:
        result = pd.read_sql_query(sql, conn)
    finally:
        conn.close()
    return result



st.set_page_config(page_title="AI Data Analyst", page_icon="🤖", layout="wide")

st.title(" AI Data Analyst")



if "history" not in st.session_state:
    st.session_state.history = []   

if "selected_question" not in st.session_state:
    st.session_state.selected_question = ""

with st.sidebar:
    st.header("⚙️ تنظیمات")

    show_chart = st.checkbox("نمایش نمودار خودکار", value=True)
    max_rows = st.slider("حداکثر ردیف نمایش داده شود", 5, 200, 50)

    st.divider()

    st.subheader("🕘 تاریخچه سوال‌ها")

    if len(st.session_state.history) == 0:
        st.caption("هنوز سوالی پرسیده نشده.")
    else:
        for i, q in enumerate(reversed(st.session_state.history)):
            if st.button(q, key=f"hist_{i}"):
                st.session_state.selected_question = q



uploaded_file = st.file_uploader(
    "Upload Excel File",
    type=["xlsx", "csv"]
)


if uploaded_file is not None:



    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    st.subheader("Data Preview")
    st.dataframe(df.head())

    db_path = "database.db"
    conn = sqlite3.connect(db_path)


    df.to_sql(
        "uploaded_data",
        conn,
        if_exists="replace",
        index=False
    )

    st.success("Data saved to SQLite")

  

    cursor = conn.cursor()

    cursor.execute("""
    SELECT name
    FROM sqlite_master
    WHERE type='table';
    """)

    tables = cursor.fetchall()

    schema_text = ""

    for table in tables:
        table_name = table[0]
        schema_text += f"\nTable {table_name}\n"

        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()

        for col in columns:
            schema_text += f"{col[1]} {col[2]}\n"

    with st.expander("📋 Database Schema"):
        st.text(schema_text)

    
    conn.close()


    question = st.text_input(
        "Ask something about your data",
        value=st.session_state.selected_question
    )

    query = ""

    if question:

        query = generate_sql(question, schema_text)

        st.subheader("Generated SQL")
        st.code(query, language="sql")

  

    if st.button("Run Query"):

        if not query:
            st.warning("First ask a question")
        else:

            is_valid, error_message = validate_sql(query)

            if not is_valid:
                st.error(f"⛔ کوئری رد شد: {error_message}")
            else:
                try:
                    result = run_query_cached(db_path, query)

                    
                    if question not in st.session_state.history:
                        st.session_state.history.append(question)

                    st.subheader("Result")
                    st.dataframe(result.head(max_rows))

                    
                    if not result.empty:
                        with st.spinner("در حال آماده‌سازی پاسخ..."):
                            answer = explain_result(
                                question,
                                result.head(max_rows).to_csv(index=False)
                            )

                        st.subheader("💬 پاسخ")
                        st.write(answer)

                   

                    if show_chart and not result.empty:

                        numeric_cols = result.select_dtypes(include="number").columns.tolist()
                        text_cols = result.select_dtypes(exclude="number").columns.tolist()

                        if len(numeric_cols) >= 1 and len(text_cols) >= 1:

                            st.subheader("📊 نمودار")

                            chart_type = st.radio(
                                "نوع نمودار",
                                ["Bar", "Line", "Pie"],
                                horizontal=True
                            )

                            x_col = text_cols[0]
                            y_col = numeric_cols[0]

                            if chart_type == "Bar":
                                fig = px.bar(result, x=x_col, y=y_col)
                            elif chart_type == "Line":
                                fig = px.line(result, x=x_col, y=y_col)
                            else:
                                fig = px.pie(result, names=x_col, values=y_col)

                            st.plotly_chart(fig, use_container_width=True)

                        elif len(numeric_cols) >= 1:
                            st.subheader("📊 نمودار")
                            st.line_chart(result[numeric_cols])

                except Exception as e:
                    st.error(f"SQL Error: {e}")
