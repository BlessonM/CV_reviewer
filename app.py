import streamlit as st
import pymongo
import os
import PyPDF2
import pandas as pd  # For converting MongoDB documents to DataFrames

# --- MongoDB Configuration ---
MONGO_URI = "mongodb://localhost:27017/"  # Replace with your MongoDB URI
DB_NAME = "capstone"  # Database name

# Connect to MongoDB
try:
    client = pymongo.MongoClient(MONGO_URI)
    db = client[DB_NAME]
    jd_col = db['jd_col']  # Collection for job descriptions
    cv_col = db['cv_col']  # Collection for CVs
    st.success("Connected to MongoDB")
except Exception as e:
    st.error(f"Could not connect to MongoDB: {e}")
    st.stop()

# Clear collections initially
jd_col.delete_many({})  # Delete all documents in jd_col
cv_col.delete_many({})  # Delete all documents in cv_col
st.info("Cleared existing data in 'jd_col' and 'cv_col' collections.")

# --- Streamlit App ---
st.title("CV Reviewer")

# Input 1: Text (Job Description)
jd = st.text_area("Enter your job description:", height=150)

# Input 2: PDF files (CVs)
uploaded_files = st.file_uploader("Upload CVs (PDF files)", type="pdf", accept_multiple_files=True)

# Save Data Button
if st.button("Save Data"):
    if jd:
        # Save job description to MongoDB
        jd_data = {"job_description": jd}
        jd_col.insert_one(jd_data)
        st.success("Job description saved to MongoDB!")
    else:
        st.warning("Please enter a job description.")

    if uploaded_files:
        for uploaded_file in uploaded_files:
            # Extract text from PDF
            try:
                pdf_reader = PyPDF2.PdfReader(uploaded_file)
                pdf_text = ""
                for page in pdf_reader.pages:
                    pdf_text += page.extract_text()

                # Save CV text and file name to MongoDB
                cv_data = {
                    "file_name": uploaded_file.name,
                    "text": pdf_text
                }
                cv_col.insert_one(cv_data)
                st.success(f"CV '{uploaded_file.name}' saved to MongoDB!")
            except PyPDF2.errors.PdfReadError:
                st.error(f"Error reading PDF {uploaded_file.name}. Skipping text extraction.")
            except Exception as e:
                st.error(f"An error occurred while processing {uploaded_file.name}: {e}")
    else:
        st.warning("No PDF files uploaded.")






# Custom CSS to limit column height
st.markdown(
    """
    <style>
    .stDataFrame td {
        max-height: 100px;
        overflow-y: auto;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Display Data from MongoDB as Tables
st.header("Job Descriptions (jd_col)")
jd_documents = list(jd_col.find({}, {"_id": 0}))  # Exclude the "_id" field
if jd_documents:
    jd_df = pd.DataFrame(jd_documents)  # Convert to DataFrame
    st.dataframe(jd_df)  # Display as a table
else:
    st.info("No job descriptions found in 'jd_col'.")

st.header("CVs (cv_col)")
cv_documents = list(cv_col.find({}, {"_id": 0}))  # Exclude the "_id" field
if cv_documents:
    cv_df = pd.DataFrame(cv_documents)  # Convert to DataFrame
    st.dataframe(cv_df)  # Display as a table
else:
    st.info("No CVs found in 'cv_col'.")

# Close MongoDB connection
if client:
    client.close()