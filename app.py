"""
Σύστημα Διαχείρισης Στοάς ΑΚΡΟΠΟΛΙΣ
Multi-Page Application - Main Entry Point

Version: 2.0
Author: Χρήστος Ιατρόπουλος
"""

import streamlit as st
from modules.config import get_config

# Page configuration
st.set_page_config(
    page_title="Στοά ΑΚΡΟΠΟΛΙΣ",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f4788;
        text-align: center;
        padding: 1rem;
        background: linear-gradient(90deg, #f0f2f6 0%, #ffffff 100%);
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    
    .stat-card {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #1f4788;
        margin: 1rem 0;
    }
    
    .stat-number {
        font-size: 2rem;
        font-weight: bold;
        color: #1f4788;
    }
    
    .stat-label {
        font-size: 1rem;
        color: #666;
        margin-top: 0.5rem;
    }
    
    .feature-badge {
        display: inline-block;
        padding: 0.3rem 0.8rem;
        border-radius: 15px;
        font-size: 0.85rem;
        font-weight: 500;
        margin: 0.2rem;
    }
    
    .feature-enabled {
        background-color: #d4edda;
        color: #155724;
    }
    
    .feature-disabled {
        background-color: #f8d7da;
        color: #721c24;
    }
    
    .stButton>button {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# Initialize config
config = get_config()

# Sidebar
with st.sidebar:
    st.markdown(f"""
    <div style='text-align: center; padding: 1rem;'>
        <h1 style='color: #1f4788;'>🏛️</h1>
        <h2 style='margin: 0;'>{config.app_name}</h2>
        <p style='color: #666; font-size: 0.9rem;'>Σύστημα Διαχείρισης Μελών</p>
        <p style='color: #999; font-size: 0.75rem;'>v{config.app_version}</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Feature status
    st.subheader("📊 Κατάσταση Συστήματος")
    
    features_display = {
        'core': ('Βασικές Λειτουργίες', True),
        'tasks': ('Εργασίες & Υπενθυμίσεις', True),
        'email': ('Email Notifications', config.is_feature_enabled('email')),
        'ai': ('AI Assistant', config.is_feature_enabled('ai'))
    }
    
    for feature, (label, enabled) in features_display.items():
        badge_class = 'feature-enabled' if enabled else 'feature-disabled'
        status_icon = '✅' if enabled else '⚪'
        st.markdown(f"""
        <div class='feature-badge {badge_class}'>
            {status_icon} {label}
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Quick info
    from modules.database import get_database
    db = get_database()
    stats = db.get_member_statistics()
    
    st.metric("Σύνολο Μελών", stats['total'])
    st.metric("Ενεργά Μέλη", stats['active'])
    
    st.markdown("---")
    
    # Help section
    with st.expander("ℹ️ Βοήθεια"):
        st.markdown("""
        **Πλοήγηση:**
        - Χρησιμοποίησε το μενού αριστερά
        - Κάθε σελίδα έχει συγκεκριμένη λειτουργία
        
        **Features:**
        - 🟢 Ενεργό: Διαθέσιμο προς χρήση
        - ⚪ Ανενεργό: Χρειάζεται configuration
        
        **Υποστήριξη:**
        - Email: xiatropoulos@gmail.com
        """)

# Main content
st.markdown('<div class="main-header">🏛️ Σύστημα Διαχείρισης Στοάς ΑΚΡΟΠΟΛΙΣ</div>', unsafe_allow_html=True)

# Welcome message
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class='stat-card'>
        <div class='stat-number'>📋</div>
        <div class='stat-label'>Πλήρες Μητρώο Μελών</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class='stat-card'>
        <div class='stat-number'>✏️</div>
        <div class='stat-label'>Μαζική Επεξεργασία</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class='stat-card'>
        <div class='stat-number'>📄</div>
        <div class='stat-label'>Δημιουργία Καρτελών</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# Overview
st.subheader("📊 Σύνοψη Συστήματος")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 🎯 Διαθέσιμες Λειτουργίες")
    
    st.markdown("""
    #### Core Features (Πάντα Διαθέσιμα)
    - **Μητρώο Μελών**: Πλήρης διαχείριση 40 μελών
    - **Επεξεργασία**: Ενημέρωση στοιχείων μέλους
    - **Μαζική Επεξεργασία**: Excel import/export, bulk updates
    - **Καρτέλες PDF**: Δημιουργία επαγγελματικών καρτελών
    - **Στατιστικά**: Αναλυτικά charts και reports
    - **Εργασίες**: Task management & reminders
    """)
    
    if config.is_feature_enabled('email'):
        st.markdown("""
        #### Email Features (Ενεργοποιημένα ✅)
        - Αποστολή ειδοποιήσεων
        - Υπενθυμίσεις συνεδριών
        - Task notifications
        """)
    else:
        st.info("💡 **Email features**: Προσθέστε SMTP credentials για ενεργοποίηση")
    
    if config.is_feature_enabled('ai'):
        st.markdown("""
        #### AI Features (Ενεργοποιημένα ✅)
        - AI Assistant για βοήθεια
        - Γενικές ερωτήσεις
        - Document generation
        """)
    else:
        st.info("💡 **AI features**: Προσθέστε Anthropic API key για ενεργοποίηση")

with col2:
    st.markdown("### 📈 Στατιστικά Συστήματος")
    
    # Display statistics
    st.metric("Συνολικά Μέλη", stats['total'])
    st.metric("Ενεργά Μέλη", stats['active'], 
              delta=f"{stats['active']/stats['total']*100:.0f}% του συνόλου")
    
    # Degrees breakdown
    st.markdown("#### Κατανομή Βαθμών")
    degrees = stats.get('by_degree', {})
    for degree, count in degrees.items():
        percentage = (count / stats['total'] * 100)
        st.progress(percentage / 100, text=f"{degree}: {count} ({percentage:.0f}%)")
    
    # Status breakdown
    st.markdown("#### Κατάσταση Μελών")
    statuses = stats.get('by_status', {})
    for status, count in statuses.items():
        st.write(f"**{status}**: {count}")

st.markdown("---")

# Quick actions
st.subheader("⚡ Γρήγορες Ενέργειες")

col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("📋 Προβολή Μητρώου", use_container_width=True):
        st.switch_page("pages/1_📋_Μητρώο.py")

with col2:
    if st.button("✏️ Μαζική Επεξεργασία", use_container_width=True):
        st.switch_page("pages/3_✏️_Μαζική_Επεξεργασία.py")

with col3:
    if st.button("📄 Δημιουργία Καρτελών", use_container_width=True):
        st.switch_page("pages/4_📄_Καρτέλες.py")

with col4:
    if st.button("📊 Στατιστικά", use_container_width=True):
        st.switch_page("pages/5_📈_Στατιστικά.py")

st.markdown("---")

# System info
with st.expander("ℹ️ Πληροφορίες Συστήματος"):
    st.markdown(f"""
    **Όνομα Συστήματος:** {config.app_name}  
    **Έκδοση:** {config.app_version}  
    **Database:** {config.db_path}  
    **Κατάσταση:** Λειτουργικό ✅
    
    ---
    
    **Ενεργά Features:**
    {config.get_feature_status_message()}
    
    ---
    
    **Τελευταία Ενημέρωση:** Δεκέμβριος 2025  
    **Maintainer:** Χρήστος Ιατρόπουλος  
    **Email:** xiatropoulos@gmail.com
    """)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 2rem;'>
    <p>🏛️ <strong>Στοά ΑΚΡΟΠΟΛΙΣ Υπ ΑΡΙΘΜ 84</strong></p>
    <p style='font-size: 0.85rem;'>Σύστημα Διαχείρισης Μελών v2.0</p>
</div>
""", unsafe_allow_html=True)
