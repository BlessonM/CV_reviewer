import streamlit as st
import pymongo
import os
import PyPDF2
import pandas as pd
from google import genai

def keywords_list_api(text):
    client = genai.Client(api_key="AIzaSyCqq5SZhuK3YtvnH1joGUSmdTtqep7qK10")
    response = client.models.generate_content(
        model="gemini-2.0-flash", contents=f"Extract the keywords and provide a json object with just a single key value {text}"
    )
    list = response.text
    start = list.find("[")
    last = list.rfind("]")
    list = list[start+1:last]
    list = list.split(",")
    return list

def rescore(searchwords, cv):
    extra_score = 0
    weight = 2  # Weight for each keyword match
    for i in searchwords:
        for j in cv['keywords']:
            if i.lower() in j.lower() or j.lower() in i.lower():
                extra_score += weight
    # Update the CV dictionary with the new extra_score
    cv["extra_score"] = extra_score
    return cv  # Return the updated CV dictionary

def update_extra_scores(keywords):
    # Fetch all CV documents from the collection
    cv_documents = list(cv_col.find({}))
    
    for cv in cv_documents:
        # Rescore the CV based on the updated keywords
        updated_cv = rescore(keywords, cv)
        
        # Update the document in the collection with the new extra_score
        cv_col.update_one(
            {"_id": cv["_id"]},
            {"$set": {"extra_score": updated_cv["extra_score"]}}
        )

# Function to truncate text
def truncate_text(text, max_length=100):
    return text[:max_length] + "..." if len(text) > max_length else text

def display_cvs(cv_documents):
    if cv_documents:
        cv_df = pd.DataFrame(cv_documents)

        # CSS styling to prevent text wrapping in the 'text' column
        st.write(
            """
            <style>
            .dataframe td {
                white-space: nowrap; /* Prevent text wrapping */
                overflow: hidden;    /* Hide overflowing text */
                text-overflow: ellipsis; /* Add ellipsis (...) for overflow */
                max-width: 200px;  /* Set a maximum width for the column */
            }
            .dataframe th {
                white-space: nowrap; /* Prevent text wrapping in header */
            }

            </style>
            """,
            unsafe_allow_html=True,
        )
        st.dataframe(cv_df)  # Use st.dataframe for better interactivity

    else:
        st.info("No CVs found.")

def display_jds(jd_documents):
    if jd_documents:
        jd_df = pd.DataFrame(jd_documents)

        st.write(
            """
            <style>
            .dataframe td {
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
                max-width: 200px; /* Adjust as needed */
            }
            .dataframe th {
                white-space: nowrap; /* Prevent wrapping in headers */
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
        st.dataframe(jd_df)  # Use st.dataframe

    else:
        st.info("No job descriptions found.")        

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
        keywords_jd = keywords_list_api(jd)
        jd_data = {"job_description": jd, "keywords": keywords_jd}
        jd_col.insert_one(jd_data)
        st.success("Job description saved to MongoDB!")
        
    else:
        st.warning("Please enter a job description.")

    if uploaded_files:
        for uploaded_file in uploaded_files:
            try:
                pdf_reader = PyPDF2.PdfReader(uploaded_file)
                pdf_text = ""
                for page in pdf_reader.pages:
                    pdf_text += page.extract_text()

                base_score = 0    
                keywords_cv = keywords_list_api(pdf_text)

                for i in jd_data['keywords']:
                    for j in keywords_cv:
                        if i.lower() in j.lower() or j.lower() in i.lower():
                            base_score += 1

                # Save CV text and file name to MongoDB
                cv_data = {
                    "file_name": uploaded_file.name,
                    "text": pdf_text,
                    "keywords": keywords_cv,
                    "base_score": base_score,
                    "extra_score": 0  # Initialize extra_score to 0
                }
                cv_col.insert_one(cv_data)
                st.success(f"CV '{uploaded_file.name}' saved to MongoDB!")
                
            except Exception as e:
                st.error(f"Error processing {uploaded_file.name}: {e}")
    else:
        st.warning("No PDF files uploaded.")

if st.button("clear"):
    # Clear collections initially
    jd_col.delete_many({})  # Delete all documents in jd_col
    cv_col.delete_many({})  # Delete all documents in cv_col
    st.info("Cleared existing data in 'jd_col' and 'cv_col' collections.")        

jd_documents = list(jd_col.find({}, {"_id": 0, "keywords": 0}))
      
display_jds(jd_documents)  # Call the display function

st.title("Keyword Input")

# Initialize keywords list in session state
if "keywords" not in st.session_state:
    st.session_state.keywords = []

# Input box for keywords
keyword = st.text_input("Enter a keyword:")

# Add keyword to list if entered and not already present
if keyword:
    if keyword not in st.session_state.keywords:
        st.session_state.keywords.append(keyword)
        st.success(f"Keyword '{keyword}' added!")
        
        # Update extra_scores in the database
        update_extra_scores(st.session_state.keywords)
    else:
        st.warning(f"Keyword '{keyword}' is already in the list.")

# Display the list of keywords with delete buttons
if st.session_state.keywords:
    st.write("**Keywords List:**")
    for i, kw in enumerate(st.session_state.keywords):
        col1, col2 = st.columns([4, 1])  # Create two columns for keyword and button
        with col1:
            st.write(kw)  # Display the keyword
        with col2:
            if st.button("Delete", key=f"delete_{i}"):  # Unique key for each button
                del st.session_state.keywords[i]  # Remove from list
                
                # Update extra_scores in the database after deletion
                update_extra_scores(st.session_state.keywords)
                #st.experimental_rerun()  # Rerun the app to reflect changes immediately
else:
    st.info("No keywords added yet.")

# Fetch and display the updated CVs
cv_documents = list(cv_col.find({}, {"_id": 0}))
display_cvs(cv_documents)

# Close MongoDB connection
if client:
    client.close()