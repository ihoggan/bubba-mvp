"""Search Cases page — Find similar past investigations."""

import streamlit as st

from bubba.diagnosis.infrastructure.repository import InvestigationRepository

st.set_page_config(page_title="Search Cases", layout="wide")

st.title("🔍 Search Past Cases")
st.caption("Find similar incidents by symptom or root cause")

st.divider()

repo = InvestigationRepository()

search_type = st.radio("Search by:", ["Symptom", "Root Cause", "List All"])

# ============================================================================
# SEARCH BY SYMPTOM
# ============================================================================
if search_type == "Symptom":
    query = st.text_input("Enter symptom keyword:", placeholder="e.g., 'network', 'connectivity', 'policy'")
    
    if query:
        results = repo.search_by_symptom(query)
        st.write(f"**Found {len(results)} case(s)**")
        
        if results:
            for result in results:
                with st.container(border=True):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.write(f"**{result['title']}**")
                        st.write(f"*Symptom:* {result['symptom']}")
                        
                        if result['root_cause']:
                            st.write(f"*Root Cause:* {result['root_cause']}")
                        else:
                            st.write("*Root Cause:* Not yet identified")
                        
                        st.write(f"Status: `{result['status']}` | Confirmed: `{result['engineer_confirmed']}`")
                    
                    with col2:
                        if st.button("View", key=f"view_{result['id']}", use_container_width=True):
                            st.session_state.investigation_id = result['id']
                            st.switch_page("pages/03_view_investigation.py")
        else:
            st.info("No matching cases found.")

# ============================================================================
# SEARCH BY ROOT CAUSE
# ============================================================================
elif search_type == "Root Cause":
    query = st.text_input("Enter root cause keyword:", placeholder="e.g., 'policy', 'configuration', 'cable'")
    
    if query:
        results = repo.search_by_root_cause(query)
        st.write(f"**Found {len(results)} case(s)**")
        
        if results:
            for result in results:
                with st.container(border=True):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.write(f"**{result['title']}**")
                        st.write(f"*Symptom:* {result['symptom']}")
                        
                        if result['root_cause']:
                            st.write(f"*Root Cause:* {result['root_cause']}")
                        
                        st.write(f"Status: `{result['status']}` | Confirmed: `{result['engineer_confirmed']}`")
                    
                    with col2:
                        if st.button("View", key=f"view_{result['id']}", use_container_width=True):
                            st.session_state.investigation_id = result['id']
                            st.switch_page("pages/03_view_investigation.py")
        else:
            st.info("No matching cases found.")

# ============================================================================
# LIST ALL
# ============================================================================
else:
    results = repo.list_all()
    st.write(f"**Total cases: {len(results)}**")
    
    if results:
        for result in results:
            with st.container(border=True):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**{result['title']}**")
                    st.write(f"*Symptom:* {result['symptom']}")
                    
                    if result['root_cause']:
                        st.write(f"*Root Cause:* {result['root_cause']}")
                    else:
                        st.write("*Root Cause:* Not yet identified")
                    
                    st.write(f"Status: `{result['status']}` | Confirmed: `{result['engineer_confirmed']}`")
                
                with col2:
                    if st.button("View", key=f"view_{result['id']}", use_container_width=True):
                        st.session_state.investigation_id = result['id']
                        st.switch_page("pages/03_view_investigation.py")
    else:
        st.info("No cases stored yet. Create a new investigation to begin.")

st.divider()

if st.button("🏠 Home"):
    st.switch_page("app.py")
