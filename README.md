# 🗃️ Ask Your Database

A Gen AI–powered analytics assistant that lets you query a relational database using plain English. Type a question like *"What are the total sales by region?"* and the app converts it into a real SQL query, runs it against a live cloud database, and returns the results.

**🔗 Live demo:** https://sales-genai-project-ecy33utncshoduahv43uwd.streamlit.app
**🔗 API:** https://sales-genai-project.onrender.com

---

## Overview

This project demonstrates an end-to-end pipeline combining four core skills:

- **ANSI SQL** — normalized relational schema with joins, aggregations, and window functions
- **Python** — FastAPI backend that orchestrates the LLM call, safety validation, and query execution
- **Gen AI** — an LLM (openai/gpt-oss-120b via Groq) converts natural language into SQL, using the database schema as context
- **Cloud Fundamentals** — managed cloud database, cloud-hosted backend, environment variable/secrets management, and a cloud-hosted frontend

## Architecture

```
User (browser)
     │
     ▼
Streamlit frontend  ──────────────►  FastAPI backend  ──────────────►  Groq API (openai/gpt-oss-120b)
(Streamlit Cloud)      HTTP POST      (Render, free tier)   prompt        NL → SQL translation
                        /ask                │
                                            ▼
                                  Safety validation layer
                                  (blocks non-SELECT queries)
                                            │
                                            ▼
                                  Neon (managed Postgres)
                                            │
                                            ▼
                                  Results → JSON → rendered as a table
```

**Flow:**
1. User types a question in the Streamlit UI
2. Streamlit sends it to the FastAPI `/ask` endpoint
3. FastAPI builds a prompt (question + schema) and sends it to Groq's openai/gpt-oss-120b model
4. The LLM returns a SQL query
5. A safety check confirms the query is read-only (`SELECT` only, no `DROP`/`DELETE`/`INSERT`/etc.)
6. The validated query runs against the Neon Postgres database
7. Results are returned as JSON and rendered as a table in the UI

## Tech Stack

| Layer | Technology |
|---|---|
| Database | PostgreSQL, hosted on [Neon](https://neon.tech) (free tier) |
| Backend | Python, [FastAPI](https://fastapi.tiangolo.com/), deployed on [Render](https://render.com) (free tier) |
| Gen AI | [Groq API](https://console.groq.com) running openai/gpt-oss-120b |
| Frontend | [Streamlit](https://streamlit.io), deployed on Streamlit Community Cloud |
| Driver | `psycopg2-binary` |

## Database Schema

```sql
regions(region_id, region_name)
customers(customer_id, customer_name, region_id, signup_date)
products(product_id, product_name, category, unit_price)
orders(order_id, customer_id, product_id, quantity, order_date)
```

Relationships:
- `customers.region_id → regions.region_id`
- `orders.customer_id → customers.customer_id`
- `orders.product_id → products.product_id`

## Safety Guardrails

Since an LLM is generating and executing SQL against a real database, the app enforces a simple but strict safety layer before any query runs:

- Query must start with `SELECT`
- Query is rejected if it contains `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `CREATE`, or `TRUNCATE`
- Rejected queries are never executed — the API returns an error instead

This prevents the LLM from accidentally (or if prompted adversarially) modifying or destroying data.

## Example Queries

- "What are the total sales by region?"
- "Which are the top 3 best-selling products by revenue?"
- "How many customers signed up in each region?"
- "Which customers spent the most money between February and March 2024?"

## Project Structure

```
sales_genai_project/
├── main.py             # FastAPI backend: schema, prompt, safety check, /ask endpoint
├── app.py               # Streamlit frontend
├── requirements.txt      # Python dependencies
├── .gitignore            # excludes .env and cache files
└── .env                  # local secrets (not committed) — GROQ_API_KEY, DATABASE_URL
```

## Running Locally

### 1. Clone the repo
```bash
git clone https://github.com/HARSHBAJPAI-13/sales-genai-project.git
cd sales-genai-project
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Set up environment variables
Create a `.env` file in the project root:
```
GROQ_API_KEY=your_groq_api_key
DATABASE_URL=postgresql://user:password@host/dbname?sslmode=require
```

- Get a free Groq API key at [console.groq.com](https://console.groq.com)
- Get a free Postgres database at [neon.tech](https://neon.tech)

### 4. Create the schema and sample data
Run the SQL in [`schema.sql`](#database-schema) (or the `CREATE TABLE` / `INSERT` statements above) against your database using Neon's SQL editor, or a client like DBeaver.

### 5. Run the backend
```bash
python -m uvicorn main:app --reload
```
API available at `http://127.0.0.1:8000/docs`

### 6. Run the frontend
In a separate terminal:
```bash
python -m streamlit run app.py
```
UI available at `http://localhost:8501`

## Deployment

| Component | Service | Notes |
|---|---|---|
| Database | Neon | Free tier, managed Postgres |
| Backend | Render | Free tier web service; build command `pip install -r requirements.txt`, start command `uvicorn main:app --host 0.0.0.0 --port $PORT` |
| Frontend | Streamlit Community Cloud | Deploys directly from GitHub, points at `app.py` |

Secrets (`GROQ_API_KEY`, `DATABASE_URL`) are set as environment variables in the Render dashboard — never committed to the repo.
