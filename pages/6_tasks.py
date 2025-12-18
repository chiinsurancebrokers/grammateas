import streamlit as st
import sys
sys.path.append('..')
from modules.database import get_database
from datetime import datetime, timedelta

st.set_page_config(page_title="Εργασίες", page_icon="📋", layout="wide")

st.markdown("""
<style>
.main-header {font-size: 2.5rem; font-weight: bold; color: #1f4788; padding: 1rem; background: linear-gradient(90deg, #f0f2f6 0%, #ffffff 100%); border-radius: 10px; margin-bottom: 2rem;}
</style>
""", unsafe_allow_html=True)

db = get_database()

st.markdown('<div class="main-header">📋 Εργασίες & Υπενθυμίσεις</div>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📝 Όλες οι Εργασίες", "➕ Νέα Εργασία", "⚠️ Προσεχείς & Καθυστερημένες"])

# Tab 1: All tasks
with tab1:
    st.subheader("Διαχείριση Εργασιών")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        status_filter = st.selectbox("Φίλτρο Κατάστασης", ["Όλες", "Εκκρεμής", "Σε Εξέλιξη", "Ολοκληρωμένη"], key="task_status_filter")
    
    tasks_df = db.get_all_tasks(status_filter)
    
    if len(tasks_df) > 0:
        display_df = tasks_df.rename(columns={
            'task_id': 'ID',
            'title': 'Τίτλος',
            'description': 'Περιγραφή',
            'due_date': 'Προθεσμία',
            'priority': 'Προτεραιότητα',
            'status': 'Κατάσταση',
            'category': 'Κατηγορία'
        })
        
        st.dataframe(
            display_df[['ID', 'Τίτλος', 'Προθεσμία', 'Προτεραιότητα', 'Κατάσταση', 'Κατηγορία']],
            use_container_width=True,
            hide_index=True
        )
        
        st.markdown("---")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            task_id = st.number_input("ID Εργασίας", min_value=1, step=1, key="task_id_action")
        
        with col2:
            new_status = st.selectbox("Νέα Κατάσταση", ["Εκκρεμής", "Σε Εξέλιξη", "Ολοκληρωμένη"], key="new_task_status")
            
            if st.button("🔄 Ενημέρωση Κατάστασης"):
                db.update_task_status(task_id, new_status)
                st.success("✅ Ενημερώθηκε!")
                st.rerun()
        
        with col3:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🗑️ Διαγραφή Εργασίας", type="secondary"):
                db.delete_task(task_id)
                st.success("✅ Διαγράφηκε!")
                st.rerun()
    else:
        st.info("📭 Δεν υπάρχουν εργασίες με αυτό το φίλτρο")

# Tab 2: New task
with tab2:
    st.subheader("Προσθήκη Νέας Εργασίας")
    
    with st.form("new_task_form"):
        title = st.text_input("Τίτλος*", placeholder="π.χ. Προετοιμασία Συνεδρίας")
        description = st.text_area("Περιγραφή", height=100)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            due_date = st.date_input("Προθεσμία*", value=datetime.now() + timedelta(days=7))
        
        with col2:
            priority = st.selectbox("Προτεραιότητα", ["Χαμηλή", "Μεσαία", "Υψηλή", "Επείγουσα"])
        
        with col3:
            category = st.selectbox("Κατηγορία", ["Γενικά", "Συνεδρίες", "Διοικητικά", "Οικονομικά", "Εκδηλώσεις", "Άλλο"])
        
        submitted = st.form_submit_button("➕ Προσθήκη Εργασίας", type="primary")
        
        if submitted:
            if title:
                db.add_task(title, description, str(due_date), priority, category)
                st.success("✅ Η εργασία προστέθηκε!")
                st.rerun()
            else:
                st.error("❌ Ο τίτλος είναι υποχρεωτικός!")

# Tab 3: Upcoming & Overdue
with tab3:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("⚠️ Καθυστερημένες")
        overdue = db.get_overdue_tasks()
        
        if len(overdue) > 0:
            st.error(f"**{len(overdue)} εργασίες καθυστερούν!**")
            for _, task in overdue.iterrows():
                with st.expander(f"🔴 {task['title']}"):
                    st.write(f"**Προθεσμία:** {task['due_date']}")
                    st.write(f"**Προτεραιότητα:** {task['priority']}")
                    if task['description']:
                        st.write(f"**Περιγραφή:** {task['description']}")
        else:
            st.success("✅ Δεν υπάρχουν καθυστερημένες εργασίες!")
    
    with col2:
        st.subheader("📅 Προσεχείς 7 Ημέρες")
        upcoming = db.get_upcoming_tasks(days=7)
        
        if len(upcoming) > 0:
            st.info(f"**{len(upcoming)} εργασίες πλησιάζουν**")
            for _, task in upcoming.iterrows():
                with st.expander(f"🟡 {task['title']}"):
                    st.write(f"**Προθεσμία:** {task['due_date']}")
                    st.write(f"**Προτεραιότητα:** {task['priority']}")
                    if task['description']:
                        st.write(f"**Περιγραφή:** {task['description']}")
        else:
            st.info("📭 Δεν υπάρχουν προσεχείς εργασίες")

st.markdown("---")
st.info("""
**Συμβουλές:**
- Χρησιμοποιήστε προτεραιότητες για να οργανώσετε τις εργασίες
- Ελέγχετε τακτικά τις καθυστερημένες εργασίες
- Οι εργασίες με status "Ολοκληρωμένη" καταγράφουν την ημερομηνία ολοκλήρωσης
""")
