import streamlit as st
import requests

st.set_page_config(page_title="Ask Your Database", page_icon="🗃️")
st.title("🗃️ Ask Your Database")
st.write("Ask questions about your sales data in plain English.")

API_URL = "https://sales-genai-project.onrender.com/ask"
question = st.text_input("Your question:", placeholder="e.g. What are the total sales by region?")

if st.button("Ask") and question:
    with st.spinner("Thinking..."):
        try:
            response = requests.post(API_URL, json={"question": question}, timeout=60)
            data = response.json()

            if "error" in data:
                st.error(f"Error: {data['error']}")
                st.code(data.get("sql", ""), language="sql")
            else:
                st.subheader("Generated SQL")
                st.code(data["sql"], language="sql")

                st.subheader("Results")
                if data["results"]:
                    st.dataframe(data["results"])
                else:
                    st.info("Query ran successfully but returned no rows.")
        except requests.exceptions.ConnectionError:
            st.error("Could not connect to the API. Make sure your FastAPI server (uvicorn) is running.")
