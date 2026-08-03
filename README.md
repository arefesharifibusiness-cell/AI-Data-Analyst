 AI Data Analyst

AI-powered Text-to-SQL application built with Streamlit and Google Gemini.

Upload an Excel or CSV file, ask questions in natural language, and let the application automatically:

🧠 Convert your question into SQL
🛡️ Validate the generated SQL before execution
📊 Execute safe SQL queries on SQLite
💬 Explain the results in natural language
📈 Generate interactive visualizations automatically


Features
📂 Upload CSV and Excel datasets
🤖 Natural Language → SQL using Gemini 2.5 Flash
🔒 SQL validation layer to prevent dangerous queries
💬 AI-generated explanation of query results
📊 Automatic Plotly visualizations
⚡ Streamlit caching for better performance
📝 Query history
🗄️ Automatic SQLite database creation


Tech Stack
Technology	Purpose
Python	Backend
Streamlit	Web UI
SQLite	Database
Google Gemini	SQL Generation & Result Explanation
Plotly	Interactive Charts
Pandas	Data Processing


SQL Security

Every generated SQL query is validated before execution.

Allowed:

SELECT
WITH

Blocked:

DROP
DELETE
UPDATE
INSERT
ALTER
CREATE
TRUNCATE
PRAGMA
Multiple SQL statements

Only safe read-only queries are executed.


Architecture
Excel / CSV
      │
      ▼
Pandas DataFrame
      │
      ▼
SQLite Database
      │
      ▼
Natural Language Question
      │
      ▼
Gemini 2.5 Flash
      │
      ▼
Generated SQL
      │
      ▼
SQL Validation Layer
      │
      ▼
SQLite Execution
      │
      ▼
Result DataFrame
      │
      ├────────► Plotly Chart
      │
      ▼
Gemini Explanation
