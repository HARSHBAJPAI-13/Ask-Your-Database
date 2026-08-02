import os
import psycopg2
from dotenv import load_dotenv
from groq import Groq
from fastapi import FastAPI
from pydantic import BaseModel

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
DATABASE_URL = os.getenv("DATABASE_URL")

app = FastAPI(title="Ask Your Database")

SCHEMA = """
Tables:
regions(region_id, region_name)
customers(customer_id, customer_name, region_id, signup_date)
products(product_id, product_name, category, unit_price)
orders(order_id, customer_id, product_id, quantity, order_date)

Relationships:
customers.region_id -> regions.region_id
orders.customer_id -> customers.customer_id
orders.product_id -> products.product_id
"""

def run_query(sql):
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    cursor.close()
    conn.close()
    return columns, rows

def generate_sql(question):
    prompt = f"""You are a SQL expert. Given this database schema:

{SCHEMA}

Convert the following question into a single valid PostgreSQL query.
Rules:
- Return ONLY the SQL query, no explanation, no markdown, no code fences.
- The query must be read-only (SELECT only). Never generate INSERT, UPDATE, DELETE, or DROP.
- Use proper JOINs where needed based on the relationships given.

Question: {question}

SQL:"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}]
    )
    sql = response.choices[0].message.content.strip()
    sql = sql.replace("```sql", "").replace("```", "").strip()
    return sql

def is_safe_query(sql):
    sql_upper = sql.strip().upper()
    forbidden = ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "TRUNCATE"]
    if not sql_upper.startswith("SELECT"):
        return False
    if any(word in sql_upper for word in forbidden):
        return False
    return True

class QuestionRequest(BaseModel):
    question: str
@app.get("/")
def root():
    return {"message": "Ask Your Database API is running. Visit /docs for the API documentation."}
@app.post("/ask")
def ask(request: QuestionRequest):
    question = request.question
    sql = generate_sql(question)

    if not is_safe_query(sql):
        return {"error": "Unsafe query blocked", "sql": sql}

    try:
        cols, rows = run_query(sql)
        results = [dict(zip(cols, row)) for row in rows]
        return {
            "question": question,
            "sql": sql,
            "results": results
        }
    except Exception as e:
        return {"error": str(e), "sql": sql}
