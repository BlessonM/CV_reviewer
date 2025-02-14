import streamlit as st

st.title("Test app")

st.text('Hello')

st.header("Heading")
          
st.subheader("sub")

st.markdown("## mark")

st.success('yeah')

exp = ZeroDivisionError("Divide by zero")
st.exception(exp)

st.write("Text to display")

st.write(range(10))