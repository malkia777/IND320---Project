import streamlit as st


st.set_page_config(
    page_title="IND320 - Reservoirs Project",
    page_icon="💧",
    layout="wide",
)

st.title("IND320 - Reservoirs Project")

st.write(
    """
     Use the sidebar to navigate between pages:
    - **Data table**: the imported data with a sparkline of the first
      month for each column.
    - **Plot**: an interactive plot of the data, with column and month
      selection.
    """
)

st.markdown("---")
st.markdown(
    "GitHub repository: "
    "[malkia777/IND320---Project](https://github.com/malkia777/IND320---Project)"
)
st.markdown("Streamlit app: https://share.streamlit.io/user/malkia777")
