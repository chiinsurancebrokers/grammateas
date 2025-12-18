import streamlit as st
import sys
sys.path.append('..')
from modules.database import get_database
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

st.set_page_config(page_title="Στατιστικά", page_icon="📈", layout="wide")

st.markdown("""
<style>
.main-header {font-size: 2.5rem; font-weight: bold; color: #1f4788; padding: 1rem; background: linear-gradient(90deg, #f0f2f6 0%, #ffffff 100%); border-radius: 10px; margin-bottom: 2rem;}
.metric-card {background-color: #f8f9fa; padding: 1.5rem; border-radius: 10px; border-left: 4px solid #1f4788; margin: 1rem 0;}
</style>
""", unsafe_allow_html=True)

db = get_database()

st.markdown('<div class="main-header">📈 Στατιστικά & Αναλύσεις</div>', unsafe_allow_html=True)

# Get statistics
stats = db.get_member_statistics()
df = db.get_all_members()

# Key metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Σύνολο Μελών", stats['total'], delta=None)
with col2:
    st.metric("Ενεργά Μέλη", stats['active'], delta=f"{stats['active']/stats['total']*100:.0f}%")
with col3:
    inactive = stats['total'] - stats['active']
    st.metric("Ανενεργά", inactive)
with col4:
    degrees = stats.get('by_degree', {})
    st.metric("Δάσκαλοι", degrees.get('Δάσκαλος', 0))

st.markdown("---")

# Charts
col1, col2 = st.columns(2)

with col1:
    st.subheader("📊 Κατανομή Βαθμών")
    
    degrees_df = pd.DataFrame(list(degrees.items()), columns=['Βαθμός', 'Αριθμός'])
    
    fig_degrees = px.pie(
        degrees_df, 
        values='Αριθμός', 
        names='Βαθμός',
        color_discrete_sequence=['#1f4788', '#4a90e2', '#87ceeb']
    )
    fig_degrees.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig_degrees, use_container_width=True)
    
    st.dataframe(degrees_df, use_container_width=True, hide_index=True)

with col2:
    st.subheader("📊 Κατάσταση Μελών")
    
    by_status = stats.get('by_status', {})
    status_df = pd.DataFrame(list(by_status.items()), columns=['Κατάσταση', 'Αριθμός'])
    
    fig_status = px.bar(
        status_df,
        x='Κατάσταση',
        y='Αριθμός',
        color='Κατάσταση',
        color_discrete_sequence=['#28a745', '#ffc107', '#dc3545']
    )
    fig_status.update_layout(showlegend=False)
    st.plotly_chart(fig_status, use_container_width=True)
    
    st.dataframe(status_df, use_container_width=True, hide_index=True)

st.markdown("---")

# Financial status
st.subheader("💰 Οικονομική Τακτοποίηση")

financial_counts = df['financial_status'].value_counts()
fin_df = pd.DataFrame({
    'Κατάσταση': financial_counts.index,
    'Αριθμός': financial_counts.values
})

col1, col2 = st.columns([2, 1])

with col1:
    fig_financial = go.Figure(data=[
        go.Bar(
            x=fin_df['Κατάσταση'],
            y=fin_df['Αριθμός'],
            text=fin_df['Αριθμός'],
            textposition='auto',
            marker_color=['#28a745' if x == 'Ναι' else '#dc3545' for x in fin_df['Κατάσταση']]
        )
    ])
    fig_financial.update_layout(
        title="Κατανομή Οικονομικής Τακτοποίησης",
        xaxis_title="",
        yaxis_title="Αριθμός Μελών"
    )
    st.plotly_chart(fig_financial, use_container_width=True)

with col2:
    st.markdown("<br><br>", unsafe_allow_html=True)
    for _, row in fin_df.iterrows():
        percentage = (row['Αριθμός'] / stats['total'] * 100)
        st.metric(row['Κατάσταση'], row['Αριθμός'], delta=f"{percentage:.1f}%")

st.markdown("---")

# Detailed breakdown
st.subheader("📋 Λεπτομερής Ανάλυση")

tab1, tab2 = st.tabs(["Βαθμοί × Κατάσταση", "Οικονομικά × Βαθμός"])

with tab1:
    cross_tab = pd.crosstab(df['current_degree'], df['member_status'])
    st.dataframe(cross_tab, use_container_width=True)
    
    fig_cross = px.bar(
        cross_tab.reset_index().melt(id_vars='current_degree'),
        x='current_degree',
        y='value',
        color='member_status',
        barmode='group',
        labels={'current_degree': 'Βαθμός', 'value': 'Αριθμός', 'member_status': 'Κατάσταση'}
    )
    st.plotly_chart(fig_cross, use_container_width=True)

with tab2:
    cross_tab2 = pd.crosstab(df['current_degree'], df['financial_status'])
    st.dataframe(cross_tab2, use_container_width=True)
    
    fig_cross2 = px.bar(
        cross_tab2.reset_index().melt(id_vars='current_degree'),
        x='current_degree',
        y='value',
        color='financial_status',
        barmode='group',
        labels={'current_degree': 'Βαθμός', 'value': 'Αριθμός', 'financial_status': 'Οικονομική Τακτοποίηση'}
    )
    st.plotly_chart(fig_cross2, use_container_width=True)

st.markdown("---")

# Summary table
st.subheader("📊 Συγκεντρωτικός Πίνακας")

summary_data = {
    'Κατηγορία': ['Σύνολο', 'Ενεργά', 'Ανενεργά', 'Μαθητές', 'Εταίροι', 'Δάσκαλοι'],
    'Αριθμός': [
        stats['total'],
        stats['active'],
        stats['total'] - stats['active'],
        degrees.get('Μαθητής', 0),
        degrees.get('Εταίρος', 0),
        degrees.get('Δάσκαλος', 0)
    ]
}

summary_df = pd.DataFrame(summary_data)
st.dataframe(summary_df, use_container_width=True, hide_index=True)
