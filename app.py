import streamlit as st
import fitz  # PyMuPDF for handling PDFs
from PIL import Image
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
import pyodbc
import pandas as pd


# -----------------------------------------------------
# 1. Configure Streamlit Page and Hide Default Menu
# -----------------------------------------------------
st.set_page_config(
    page_title="Chatbot",
    layout="wide",
    initial_sidebar_state="expanded"
)

hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# -----------------------------------------------------
# 2. Load Environment Variables and Initialize ChatGroq
# -----------------------------------------------------
load_dotenv()
chatbot = ChatGroq(
    groq_api_key=os.getenv("GROQ_API_KEY"),
    model_name="llama-3.2-11b-vision-preview"
    # model_name="llama-3.2-11b-vision-preview"   
)

# -----------------------------------------------------
# 3. Helper Function for Chat Interaction
# -----------------------------------------------------
def ask_chatbot(prompt: str) -> str:
    response = chatbot.invoke(prompt)
    return response.content


# -----------------------------------------------------
# 3. Helper Function for db_connection
# -----------------------------------------------------
def get_db_connection():
    """Establish connection to SQL Server."""
    try:
        conn = pyodbc.connect(
            'DRIVER={SQL Server};'
            'SERVER=MAHEND-VERMA;'  # Change to your server name
            'DATABASE=chatbot;'  # Change to your database name
            'UID=mahendv;'  # Change to your SQL username
            'PWD=mkm05102000;'  # Change to your SQL password
            'TrustServerCertificate=yes;'  # Prevent SSL errors
        )
        print("✅ Connection successful!")
        return conn
    except Exception as e:
        print("❌ Error connecting to database:", str(e))
        return None


# -----------------------------------------------------
# 4. Helper Function for run sql query 
# -----------------------------------------------------
def run_query(query):
    """Run SQL query and return results."""
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute(query)
            results = cursor.fetchall()  # Fetch all rows
            columns = [column[0] for column in cursor.description]  # Get column names
            
            # Convert results to list of dictionaries
            data = [dict(zip(columns, row)) for row in results]
            
            conn.close()  # Close the connection
            return data
        except Exception as e:
            print("❌ Error running query:", str(e))
            return None
    else:
        return None


# -----------------------------------------------------
# 5. Main UI Layout
# -----------------------------------------------------
st.title("Chatbot with LLM")
st.markdown("---")
  

st.subheader("Ask about the Current Page")
# Extract text from the current page.
sql_query = "SELECT * FROM INFORMATION_SCHEMA.COLUMNS where TABLE_CATALOG = 'chatbot';"  # Change to your table
Database_Schema = run_query(sql_query)

user_input = st.text_input("Enter your question:")

# Function to process user input and generate SQL query
if user_input:
    with st.spinner("Thinking..."):
        prompt = (
                f"You are an expert SQL assistant. Generate an optimized SQL query for SQL Server (MSSQL) based on the provided database schema."
                f"Use the format: databasename.table_name for all table references."
                f"Database Schema:{Database_Schema}"
                f"User Question:{user_input}"
                f"Output only the SQL query—no additional text or explanation."
            )  
        answer = ask_chatbot(prompt)
        prompt1 = (
                f"You are an expert SQL assistant. Generate an optimized SQL query for SQL Server (MSSQL) based on the provided database schema.\n"
                f"Use the format: databasename.table_name for all table references.\n"
                f"Ensure the query follows correct SQL Server syntax and avoid using backticks (`).\n"
                # f"Terminate common table expressions (CTEs) or change tracking clauses with a semicolon if necessary.\n"
                f"Database Schema:\n{Database_Schema}\n"
                f"User Query:\n{answer}\n"
                f"dont give me query start with this ```sql and any other"
                f"Return only the SQL query with no additional text, explanations, or formatting markers."
                f'''Guidelines:
                - Do **not** include extra text like "Here is the sql query ."
                - Do **not** wrap the response inside code blocks (`json`, `python`, etc.).
                - Do **not** provide explanations—only the SQL query response.'''
            )
        answer1 = ask_chatbot(prompt1)
        result = run_query(answer1)  


    # Streamlit UI
    st.title("Database chatbot")  

    # Display the SQL query in an expandable section
    with st.expander("Generated SQL Query", expanded=True):
        st.code(answer1, language="sql")

    # Display the DataFrame if results exist
    if result and len(result) > 0:
        df = pd.DataFrame(result)
        st.dataframe(df)  # Display interactive table
    else:
        st.warning("⚠ No results found for the generated query.")

    




