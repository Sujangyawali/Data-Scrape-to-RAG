import streamlit as st
import requests
import json

# Streamlit UI
st.title("Data Scrape to RAG - Document Assistant")

# API endpoint
api_url = "http://localhost:8000/ask"

# Get the question from the text input
question = st.text_input("Ask a question about the documents:").strip()

if st.button("Submit"):
    if question:  # Check if question is non-empty after stripping
        with st.spinner("Retrieving and generating answer..."):
            print("question:", question)
            # Send request to FastAPI
            response = requests.post(api_url, json={"question": question})
            
            if response.status_code == 200:
                result = response.json()
                if "error" in result:
                    st.error(result["error"])
                else:
                    st.success("Answer generated!")
                    st.write(f"**Question:** {result['question']}")
                    st.write(f"**Answer:** {result['answer']}")
                    st.write("**Sources:**")
                    for source in result['sources']:
                        st.write(f"- {source}")
            else:
                st.error(f"API Error: {response.status_code} - {response.text}")
    else:
        st.warning("Please enter a question.")