import streamlit as st
 
st.set_page_config(
    page_title="IND320 - Reservoirs Project",
    layout="wide",
)
 

pages = [
    st.Page("Pages/2_Data_Table.py", title="Data Table"),
    st.Page("Pages/3_Plots.py", title="Plots"),
    st.Page("Pages/4_Page_Four.py", title="Page 4"),
]

navigation = st.navigation(pages, position="sidebar")
 

st.title("IND320 - Reservoirs Project")
 
st.write(

    """
    Welcome to the IND320 Reservoirs Project.
 
    Use the sidebar to navigate between pages:
 
    - **Data Table**: View reservoir data with sparklines.
    - **Plots**: Explore reservoir data by column and month.
    - **Page 4**: Additional project content.
    """
)
 
st.markdown("---")
 
st.markdown(
    "GitHub repository: "
    "[malkia777/IND320---Project]"
    "(https://github.com/malkia777/IND320---Project)"
)
 
navigation.run()