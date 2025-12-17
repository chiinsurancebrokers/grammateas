#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🏛️ ΠΛΗΡΕΣ ΣΥΣΤΗΜΑ ΓΡΑΜΜΑΤΕΑ-ΣΦΡΑΓΙΔΟΦΥΛΑΚΑ
Με Reminders, Deadline Tracking, Email Notifications & AI Assistant
Εκτέλεση: streamlit run complete_stoa_system.py
"""

import streamlit as st
import sqlite3
import pandas as pd
import datetime
import json
import plotly.express as px
from dataclasses import dataclass
import io
import base64
from pathlib import Path
import zipfile
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from typing import List, Dict, Optional
import threading
import time
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import anthropic
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


# ================== CONFIGURATION ==================

@dataclass
class SystemConfig:
    """Ρυθμίσεις συστήματος"""
    admin_email: str = os.getenv("ADMIN_EMAIL", "")
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    smtp_server: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    sender_email: str = os.getenv("SENDER_EMAIL", "")
    sender_password: str = os.getenv("SENDER_PASSWORD", "")
    reminder_days_before: int = int(os.getenv("REMINDER_DAYS_BEFORE", "7"))
    grand_lodge_email: str = os.getenv("GRAND_LODGE_EMAIL", "")
    grand_inspector_email: str = os.getenv("GRAND_INSPECTOR_EMAIL", "")


# ================== TASK TYPES ==================

class TaskType:
    """Τύποι εργασιών"""
    SEND_INVITATIONS = "send_invitations"
    NOTIFY_GRAND_LODGE = "notify_grand_lodge"
    COMPLETE_MINUTES = "complete_minutes"
    CLOSE_ATTENDANCE = "close_attendance"
    ISSUE_ORDER = "issue_order"
    UPDATE_REGISTRY = "update_registry"
    GENERAL_REMINDER = "general_reminder"


# ================== DATABASE WITH TASKS ==================

@st.cache_resource
def init_complete_database():
    """Αρχικοποίηση πλήρους βάσης δεδομένων"""
    conn = sqlite3.connect('stoa_complete.db', check_same_thread=False)

    # Πίνακας μελών
    conn.execute('''
        CREATE TABLE IF NOT EXISTS μέλη (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ονοματεπώνυμο TEXT NOT NULL,
            όνομα_πατρός TEXT,
            τόπος_γέννησης TEXT,
            χρόνος_γέννησης TEXT,
            επάγγελμα TEXT,
            τόπος_διαμονής TEXT,
            τεκτονικός_βαθμός TEXT,
            χρονολογία_μύησης TEXT,
            αύξων_αριθμός_μεγάλης_στοάς TEXT,
            κατάσταση TEXT DEFAULT 'Ενεργός',
            παρατηρήσεις TEXT,
            email TEXT DEFAULT '',
            τηλέφωνο TEXT DEFAULT '',
            ημερομηνία_εγγραφής TEXT DEFAULT CURRENT_TIMESTAMP,
            notified_grand_lodge INTEGER DEFAULT 0
        )
    ''')

    # Πίνακας συνεδριάσεων
    conn.execute('''
        CREATE TABLE IF NOT EXISTS συνεδριάσεις (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ημερομηνία TEXT NOT NULL,
            ώρα TEXT,
            βαθμός TEXT NOT NULL,
            τόπος TEXT,
            αλληλογραφία TEXT,
            ομιλίες TEXT,
            αποφάσεις TEXT,
            κορμός_αγαθοεργίας REAL DEFAULT 0,
            invitations_sent INTEGER DEFAULT 0,
            minutes_completed INTEGER DEFAULT 0,
            attendance_closed INTEGER DEFAULT 0,
            grand_lodge_notified INTEGER DEFAULT 0
        )
    ''')

    # Πίνακας εντυπών
    conn.execute('''
        CREATE TABLE IF NOT EXISTS εντάλματα (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ημερομηνία TEXT NOT NULL,
            ποσό REAL NOT NULL,
            αιτιολογία TEXT NOT NULL,
            δικαιολογητικά TEXT,
            τύπος TEXT NOT NULL,
            κατάσταση TEXT DEFAULT 'Εκκρεμές',
            approved_by_sevασμιος INTEGER DEFAULT 0,
            documents_attached INTEGER DEFAULT 0
        )
    ''')

    # Πίνακας εργασιών (TASKS)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_type TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            due_date TEXT NOT NULL,
            priority TEXT DEFAULT 'medium',
            status TEXT DEFAULT 'pending',
            related_id INTEGER,
            related_type TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            completed_at TEXT,
            reminder_sent INTEGER DEFAULT 0
        )
    ''')

    # Πίνακας ρυθμίσεων
    conn.execute('''
        CREATE TABLE IF NOT EXISTS system_config (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')

    # Πίνακας ιστορικού ενεργειών
    conn.execute('''
        CREATE TABLE IF NOT EXISTS activity_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action_type TEXT NOT NULL,
            description TEXT,
            user TEXT DEFAULT 'Secretary',
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            details TEXT
        )
    ''')

    conn.commit()
    return conn


# ================== TASK MANAGER ==================

class TaskManager:
    """Διαχειριστής εργασιών και deadlines"""

    def __init__(self, db_connection):
        self.conn = db_connection

    def create_task(self, task_type: str, title: str, description: str,
                    due_date: str, priority: str = 'medium',
                    related_id: int = None, related_type: str = None):
        """Δημιουργία νέας εργασίας"""
        self.conn.execute('''
            INSERT INTO tasks (task_type, title, description, due_date, priority, 
                             related_id, related_type)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (task_type, title, description, due_date, priority, related_id, related_type))
        self.conn.commit()

    def get_pending_tasks(self, days_ahead: int = 7) -> pd.DataFrame:
        """Λήψη εκκρεμών εργασιών"""
        query = '''
            SELECT * FROM tasks 
            WHERE status = 'pending' 
            AND date(due_date) <= date('now', '+' || ? || ' days')
            ORDER BY due_date ASC, priority DESC
        '''
        return pd.read_sql_query(query, self.conn, params=(days_ahead,))

    def get_overdue_tasks(self) -> pd.DataFrame:
        """Λήψη ληξιπρόθεσμων εργασιών"""
        query = '''
            SELECT * FROM tasks 
            WHERE status = 'pending' 
            AND date(due_date) < date('now')
            ORDER BY due_date ASC
        '''
        return pd.read_sql_query(query, self.conn)

    def complete_task(self, task_id: int):
        """Ολοκλήρωση εργασίας"""
        self.conn.execute('''
            UPDATE tasks 
            SET status = 'completed', completed_at = datetime('now')
            WHERE id = ?
        ''', (task_id,))
        self.conn.commit()

    def mark_reminder_sent(self, task_id: int):
        """Σήμανση ότι στάλθηκε υπενθύμιση"""
        self.conn.execute('''
            UPDATE tasks 
            SET reminder_sent = 1
            WHERE id = ?
        ''', (task_id,))
        self.conn.commit()

    def auto_create_session_tasks(self, session_id: int, session_date: str):
        """Αυτόματη δημιουργία εργασιών για συνεδρίαση"""
        session_datetime = datetime.datetime.strptime(session_date, '%Y-%m-%d')

        # 1. Αποστολή προσκλήσεων (7 μέρες πριν)
        invitation_date = (session_datetime - datetime.timedelta(days=7)).strftime('%Y-%m-%d')
        self.create_task(
            TaskType.SEND_INVITATIONS,
            f"Αποστολή προσκλήσεων για συνεδρίαση #{session_id}",
            "Αποστολή προσκλήσεων σε μέλη, Μεγάλη Στοά, Μεγάλο Επιθεωρητή",
            invitation_date,
            'high',
            session_id,
            'session'
        )

        # 2. Ολοκλήρωση πρακτικών (7 μέρες μετά)
        minutes_date = (session_datetime + datetime.timedelta(days=7)).strftime('%Y-%m-%d')
        self.create_task(
            TaskType.COMPLETE_MINUTES,
            f"Ολοκλήρωση πρακτικών συνεδρίασης #{session_id}",
            "Συγγραφή και συνυπογραφή πρακτικών με Σεβάσμιο",
            minutes_date,
            'high',
            session_id,
            'session'
        )

        # 3. Κλείσιμο βιβλίου παρουσιών (ίδια μέρα)
        self.create_task(
            TaskType.CLOSE_ATTENDANCE,
            f"Κλείσιμο βιβλίου παρουσιών συνεδρίασης #{session_id}",
            "Κλείσιμο βιβλίου παρουσιών μετά το τέλος της συνεδρίασης",
            session_date,
            'high',
            session_id,
            'session'
        )

    def auto_create_member_tasks(self, member_id: int):
        """Αυτόματη δημιουργία εργασιών για νέο μέλος"""
        # Ανακοίνωση στη Μεγάλη Στοά (άμεσα)
        self.create_task(
            TaskType.NOTIFY_GRAND_LODGE,
            f"Ανακοίνωση νέου μέλους #{member_id} στη Μεγάλη Στοά",
            "Ανακοίνωση χρονολογίας μύησης και αύξοντα αριθμού",
            datetime.date.today().strftime('%Y-%m-%d'),
            'high',
            member_id,
            'member'
        )


# ================== REMINDER SYSTEM ==================

class ReminderSystem:
    """Σύστημα υπενθυμίσεων"""

    def __init__(self, db_connection, config: SystemConfig):
        self.conn = db_connection
        self.config = config
        self.task_manager = TaskManager(db_connection)

    def send_reminder_email(self, task: Dict, recipient_email: str):
        """Αποστολή email υπενθύμισης"""
        if not self.config.sender_email or not recipient_email:
            return False

        try:
            msg = MIMEMultipart()
            msg['From'] = self.config.sender_email
            msg['To'] = recipient_email
            msg['Subject'] = f"🔔 Υπενθύμιση: {task['title']}"

            # Priority badge
            priority_emoji = {
                'high': '🔴',
                'medium': '🟡',
                'low': '🟢'
            }.get(task['priority'], '⚪')

            html_body = f"""
            <html>
                <body style="font-family: Arial, sans-serif;">
                    <h2 style="color: #1f2937;">🏛️ Σύστημα Γραμματέα-Σφραγιδοφύλακα</h2>

                    <div style="background: #f3f4f6; padding: 20px; border-radius: 8px; margin: 20px 0;">
                        <h3>{priority_emoji} {task['title']}</h3>
                        <p><strong>Προθεσμία:</strong> {task['due_date']}</p>
                        <p><strong>Προτεραιότητα:</strong> {task['priority'].upper()}</p>
                        <p><strong>Περιγραφή:</strong></p>
                        <p>{task['description']}</p>
                    </div>

                    <p style="color: #666;">
                        <i>Αυτόματη υπενθύμιση από το Σύστημα Γραμματέα</i>
                    </p>
                </body>
            </html>
            """

            msg.attach(MIMEText(html_body, 'html', 'utf-8'))

            # Αποστολή
            context = ssl.create_default_context()
            with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.config.sender_email, self.config.sender_password)
                server.sendmail(self.config.sender_email, recipient_email, msg.as_string())

            return True

        except Exception as e:
            print(f"Email error: {e}")
            return False

    def check_and_send_reminders(self):
        """Έλεγχος και αποστολή υπενθυμίσεων"""
        # Λήψη εργασιών που χρειάζονται υπενθύμιση
        pending_tasks = self.task_manager.get_pending_tasks(days_ahead=3)

        for _, task in pending_tasks.iterrows():
            if not task['reminder_sent']:
                # Αποστολή υπενθύμισης
                if self.send_reminder_email(task.to_dict(), self.config.admin_email):
                    self.task_manager.mark_reminder_sent(task['id'])

        # Έλεγχος ληξιπρόθεσμων
        overdue_tasks = self.task_manager.get_overdue_tasks()
        if not overdue_tasks.empty:
            self.send_overdue_alert(overdue_tasks)

    def send_overdue_alert(self, overdue_tasks: pd.DataFrame):
        """Αποστολή ειδοποίησης για ληξιπρόθεσμες εργασίες"""
        if not self.config.admin_email:
            return

        msg = MIMEMultipart()
        msg['From'] = self.config.sender_email
        msg['To'] = self.config.admin_email
        msg['Subject'] = "🚨 ΠΡΟΣΟΧΗ: Ληξιπρόθεσμες Εργασίες"

        tasks_html = ""
        for _, task in overdue_tasks.iterrows():
            tasks_html += f"""
            <li>
                <strong>{task['title']}</strong><br>
                Προθεσμία: {task['due_date']}<br>
                Προτεραιότητα: {task['priority']}<br>
            </li>
            """

        html_body = f"""
        <html>
            <body>
                <h2 style="color: #dc2626;">🚨 ΠΡΟΣΟΧΗ: Ληξιπρόθεσμες Εργασίες</h2>
                <p>Υπάρχουν {len(overdue_tasks)} ληξιπρόθεσμες εργασίες:</p>
                <ul>{tasks_html}</ul>
                <p><strong>Παρακαλώ ολοκληρώστε τις άμεσα!</strong></p>
            </body>
        </html>
        """

        msg.attach(MIMEText(html_body, 'html', 'utf-8'))

        try:
            context = ssl.create_default_context()
            with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.config.sender_email, self.config.sender_password)
                server.sendmail(self.config.sender_email, self.config.admin_email, msg.as_string())
        except Exception as e:
            print(f"Overdue alert error: {e}")


# ================== AI ASSISTANT ==================

class AIAssistant:
    """AI Assistant με Claude API"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = anthropic.Anthropic(api_key=api_key) if api_key else None

    def check_compliance(self, action_type: str, data: Dict) -> Dict:
        """Έλεγχος συμμόρφωσης με κανονισμό"""
        if not self.client:
            return {"compliant": True, "warnings": [], "suggestions": []}

        prompt = f"""
Είσαι AI assistant για Γραμματέα-Σφραγιδοφύλακα Μασονικής Στοάς.

Ενέργεια: {action_type}
Δεδομένα: {json.dumps(data, ensure_ascii=False)}

Κανονισμός (Άρθρα 35-41):
- Προσκλήσεις 7-10 μέρες πριν τη συνεδρίαση
- Πρακτικά εντός 7 ημερών
- Άμεση ανακοίνωση νέων μελών στη Μεγάλη Στοά
- Εντάλματα με υπογραφή Σεβασμίου και δικαιολογητικά
- Κλείσιμο βιβλίου παρουσιών μετά τη συνεδρίαση

Έλεγξε αν η ενέργεια συμμορφώνεται με τον κανονισμό.
Απάντησε σε JSON format:
{{
  "compliant": true/false,
  "warnings": ["προειδοποίηση1", "προειδοποίηση2"],
  "suggestions": ["πρόταση1", "πρόταση2"]
}}
"""

        try:
            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = message.content[0].text
            return json.loads(response_text)

        except Exception as e:
            print(f"AI Assistant error: {e}")
            return {"compliant": True, "warnings": [], "suggestions": []}

    def get_task_suggestions(self, context: str) -> List[str]:
        """Λήψη προτάσεων για εργασίες"""
        if not self.client:
            return []

        prompt = f"""
Είσαι AI assistant για Γραμματέα-Σφραγιδοφύλακα.

Κατάσταση: {context}

Πρότεινε 3-5 επόμενες ενέργειες που πρέπει να κάνει ο Γραμματέας.
Απάντησε με λίστα, μια ενέργεια ανά γραμμή.
"""

        try:
            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )

            suggestions = message.content[0].text.strip().split('\n')
            return [s.strip('- ') for s in suggestions if s.strip()]

        except Exception as e:
            print(f"AI suggestions error: {e}")
            return []


# ================== SCHEDULER ==================

def start_scheduler(db_connection, config: SystemConfig):
    """Εκκίνηση scheduler για αυτόματες εργασίες"""
    scheduler = BackgroundScheduler()
    reminder_system = ReminderSystem(db_connection, config)

    # Έλεγχος κάθε πρωί στις 9:00
    scheduler.add_job(
        reminder_system.check_and_send_reminders,
        CronTrigger(hour=9, minute=0),
        id='daily_reminder_check'
    )

    # Έλεγχος για overdue κάθε απόγευμα στις 17:00
    scheduler.add_job(
        lambda: reminder_system.send_overdue_alert(
            TaskManager(db_connection).get_overdue_tasks()
        ),
        CronTrigger(hour=17, minute=0),
        id='overdue_check'
    )

    scheduler.start()
    return scheduler


# ================== MAIN APPLICATION ==================

def main():
    """Κύρια εφαρμογή"""

    st.set_page_config(
        page_title="Πλήρες Σύστημα Γραμματέα",
        page_icon="🏛️",
        layout="wide"
    )

    # Custom CSS
    st.markdown("""
    <style>
        .task-card {
            background: white;
            padding: 1rem;
            border-radius: 8px;
            border-left: 4px solid #3b82f6;
            margin: 0.5rem 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .overdue-task {
            border-left: 4px solid #dc2626;
            background: #fef2f2;
        }
        .high-priority {
            border-left: 4px solid #dc2626;
        }
        .medium-priority {
            border-left: 4px solid #f59e0b;
        }
        .low-priority {
            border-left: 4px solid #10b981;
        }
    </style>
    """, unsafe_allow_html=True)

    # Αρχικοποίηση
    if 'db_connection' not in st.session_state:
        st.session_state.db_connection = init_complete_database()

    if 'task_manager' not in st.session_state:
        st.session_state.task_manager = TaskManager(st.session_state.db_connection)

    if 'config' not in st.session_state:
        st.session_state.config = SystemConfig()

    if 'ai_assistant' not in st.session_state:
        st.session_state.ai_assistant = AIAssistant(st.session_state.config.anthropic_api_key)

    if 'reminder_system' not in st.session_state:
        st.session_state.reminder_system = ReminderSystem(
            st.session_state.db_connection,
            st.session_state.config
        )

    # Scheduler (μόνο μία φορά)
    if 'scheduler' not in st.session_state:
        st.session_state.scheduler = start_scheduler(
            st.session_state.db_connection,
            st.session_state.config
        )

    # Τίτλος
    st.markdown("""
    <div style="background: linear-gradient(90deg, #1f2937 0%, #3b82f6 100%); 
                color: white; padding: 1rem; border-radius: 10px; text-align: center;">
        <h1>🏛️ Πλήρες Σύστημα Γραμματέα-Σφραγιδοφύλακα</h1>
        <p>Με Reminders, Deadline Tracking & AI Assistant</p>
    </div>
    """, unsafe_allow_html=True)

    # Sidebar
    st.sidebar.title("📋 Μενού")

    menu = {
        "🏠 Dashboard & Tasks": "dashboard",
        "👥 Μητρώο Μελών": "members",
        "📝 Συνεδριάσεις": "sessions",
        "💰 Εντάλματα": "orders",
        "🔔 Reminders": "reminders",
        "🤖 AI Assistant": "ai",
        "⚙️ Ρυθμίσεις": "settings"
    }

    selected = st.sidebar.radio("Επιλέξτε:", list(menu.keys()))
    page = menu[selected]

    # Σύντομη προβολή εκκρεμών
    pending_count = len(st.session_state.task_manager.get_pending_tasks(days_ahead=7))
    overdue_count = len(st.session_state.task_manager.get_overdue_tasks())

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📊 Γρήγορη Επισκόπηση")
    st.sidebar.metric("Εκκρεμείς Εργασίες", pending_count)
    if overdue_count > 0:
        st.sidebar.metric("🚨 Ληξιπρόθεσμες", overdue_count, delta=f"-{overdue_count}")

    # Σελίδες
    if page == "dashboard":
        show_dashboard_with_tasks()
    elif page == "members":
        show_members_page_with_tasks()
    elif page == "sessions":
        show_sessions_page_with_tasks()
    elif page == "orders":
        show_orders_page_with_tasks()
    elif page == "reminders":
        show_reminders_page()
    elif page == "ai":
        show_ai_assistant_page()
    elif page == "settings":
        show_settings_page_complete()


def show_dashboard_with_tasks():
    """Dashboard με εργασίες"""
    st.header("🏠 Dashboard & Εργασίες")

    task_manager = st.session_state.task_manager

    # Εκκρεμείς εργασίες
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("📋 Εκκρεμείς Εργασίες (7 ημέρες)")

        pending_tasks = task_manager.get_pending_tasks(days_ahead=7)

        if not pending_tasks.empty:
            for _, task in pending_tasks.iterrows():
                priority_class = f"{task['priority']}-priority"

                st.markdown(f"""
                <div class="task-card {priority_class}">
                    <h4>{task['title']}</h4>
                    <p><strong>Προθεσμία:</strong> {task['due_date']}</p>
                    <p><strong>Προτεραιότητα:</strong> {task['priority'].upper()}</p>
                    <p>{task['description']}</p>
                </div>
                """, unsafe_allow_html=True)

                col1, col2 = st.columns([3, 1])
                with col2:
                    if st.button(f"✅ Ολοκλήρωση", key=f"complete_{task['id']}"):
                        task_manager.complete_task(task['id'])
                        st.success("Εργασία ολοκληρώθηκε!")
                        st.rerun()
        else:
            st.success("🎉 Δεν υπάρχουν εκκρεμείς εργασίες!")

    with col2:
        st.subheader("🚨 Ληξιπρόθεσμες")

        overdue_tasks = task_manager.get_overdue_tasks()

        if not overdue_tasks.empty:
            for _, task in overdue_tasks.iterrows():
                st.markdown(f"""
                <div class="task-card overdue-task">
                    <h4>⚠️ {task['title']}</h4>
                    <p>Προθεσμία: {task['due_date']}</p>
                </div>
                """, unsafe_allow_html=True)

                if st.button(f"✅ Ολοκλήρωση", key=f"overdue_{task['id']}"):
                    task_manager.complete_task(task['id'])
                    st.rerun()
        else:
            st.success("✅ Καμία ληξιπρόθεσμη εργασία!")

    # Στατιστικά
    st.markdown("---")
    st.subheader("📊 Στατιστικά")

    conn = st.session_state.db_connection

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        members_count = conn.execute("SELECT COUNT(*) FROM μέλη WHERE κατάσταση='Ενεργός'").fetchone()[0]
        st.metric("👥 Ενεργά Μέλη", members_count)

    with col2:
        sessions_count = conn.execute("SELECT COUNT(*) FROM συνεδριάσεις").fetchone()[0]
        st.metric("📝 Συνεδριάσεις", sessions_count)

    with col3:
        pending_orders = conn.execute("SELECT COUNT(*) FROM εντάλματα WHERE κατάσταση='Εκκρεμές'").fetchone()[0]
        st.metric("💰 Εκκρεμή Εντάλματα", pending_orders)

    with col4:
        tasks_completed_today = conn.execute(
            "SELECT COUNT(*) FROM tasks WHERE status='completed' AND date(completed_at) = date('now')"
        ).fetchone()[0]
        st.metric("✅ Ολοκληρώθηκαν Σήμερα", tasks_completed_today)


def show_members_page_with_tasks():
    """Σελίδα μελών με αυτόματη δημιουργία tasks"""
    st.header("👥 Μητρώο Μελών")

    tab1, tab2 = st.tabs(["📋 Λίστα", "➕ Προσθήκη"])

    with tab1:
        # Λίστα μελών (απλοποιημένη)
        conn = st.session_state.db_connection
        df = pd.read_sql_query("SELECT * FROM μέλη", conn)

        if not df.empty:
            st.dataframe(df[['id', 'ονοματεπώνυμο', 'τεκτονικός_βαθμός', 'κατάσταση']],
                         use_container_width=True)
        else:
            st.info("Δεν υπάρχουν μέλη")

    with tab2:
        with st.form("add_member"):
            col1, col2 = st.columns(2)

            with col1:
                name = st.text_input("Ονοματεπώνυμο *")
                degree = st.selectbox("Βαθμός", ["Μαθητής", "Εταίρος", "Διδάσκαλος"])
                email = st.text_input("Email")

            with col2:
                initiation = st.date_input("Μύηση")
                grand_lodge_num = st.text_input("Αριθμός Μεγάλης Στοάς")
                status = st.selectbox("Κατάσταση", ["Ενεργός", "Ανενεργός"])

            submitted = st.form_submit_button("💾 Αποθήκευση")

            if submitted and name:
                conn = st.session_state.db_connection

                cursor = conn.execute('''
                    INSERT INTO μέλη (ονοματεπώνυμο, τεκτονικός_βαθμός, χρονολογία_μύησης,
                                     αύξων_αριθμός_μεγάλης_στοάς, κατάσταση, email)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (name, degree, str(initiation), grand_lodge_num, status, email))
                conn.commit()

                member_id = cursor.lastrowid

                # Αυτόματη δημιουργία task για ανακοίνωση
                st.session_state.task_manager.auto_create_member_tasks(member_id)

                # AI Check
                if st.session_state.config.anthropic_api_key:
                    compliance = st.session_state.ai_assistant.check_compliance(
                        "new_member",
                        {"name": name, "degree": degree, "grand_lodge_num": grand_lodge_num}
                    )

                    if compliance['warnings']:
                        for warning in compliance['warnings']:
                            st.warning(f"⚠️ {warning}")

                st.success(f"✅ {name} προστέθηκε! Δημιουργήθηκε task για ανακοίνωση στη Μεγάλη Στοά.")
                st.rerun()


def show_sessions_page_with_tasks():
    """Σελίδα συνεδριάσεων με αυτόματα tasks"""
    st.header("📝 Συνεδριάσεις")

    tab1, tab2 = st.tabs(["📋 Λίστα", "➕ Νέα"])

    with tab1:
        conn = st.session_state.db_connection
        df = pd.read_sql_query("SELECT * FROM συνεδριάσεις ORDER BY ημερομηνία DESC", conn)

        if not df.empty:
            st.dataframe(df[['id', 'ημερομηνία', 'βαθμός', 'invitations_sent', 'minutes_completed']],
                         use_container_width=True)
        else:
            st.info("Δεν υπάρχουν συνεδριάσεις")

    with tab2:
        with st.form("add_session"):
            col1, col2 = st.columns(2)

            with col1:
                date = st.date_input("Ημερομηνία")
                time = st.time_input("Ώρα")
                degree = st.selectbox("Βαθμός", ["Μαθητής", "Εταίρος", "Διδάσκαλος"])

            with col2:
                location = st.text_input("Τόπος")
                charity = st.number_input("Κορμός (€)", min_value=0.0)

            submitted = st.form_submit_button("💾 Δημιουργία Συνεδρίασης")

            if submitted:
                conn = st.session_state.db_connection

                cursor = conn.execute('''
                    INSERT INTO συνεδριάσεις (ημερομηνία, ώρα, βαθμός, τόπος, κορμός_αγαθοεργίας)
                    VALUES (?, ?, ?, ?, ?)
                ''', (str(date), str(time), degree, location, charity))
                conn.commit()

                session_id = cursor.lastrowid

                # Αυτόματη δημιουργία tasks
                st.session_state.task_manager.auto_create_session_tasks(session_id, str(date))

                st.success(f"✅ Συνεδρίαση δημιουργήθηκε! Δημιουργήθηκαν 3 tasks αυτόματα:")
                st.info("• Αποστολή προσκλήσεων (7 μέρες πριν)")
                st.info("• Κλείσιμο βιβλίου παρουσιών (την ίδια μέρα)")
                st.info("• Ολοκλήρωση πρακτικών (7 μέρες μετά)")
                st.rerun()


def show_orders_page_with_tasks():
    """Σελίδα εντυπών με compliance check"""
    st.header("💰 Εντάλματα Πληρωμής")

    tab1, tab2 = st.tabs(["📋 Λίστα", "➕ Νέο"])

    with tab1:
        conn = st.session_state.db_connection
        df = pd.read_sql_query("SELECT * FROM εντάλματα ORDER BY ημερομηνία DESC", conn)

        if not df.empty:
            st.dataframe(df[['id', 'ημερομηνία', 'ποσό', 'αιτιολογία', 'κατάσταση']],
                         use_container_width=True)

    with tab2:
        with st.form("add_order"):
            col1, col2 = st.columns(2)

            with col1:
                date = st.date_input("Ημερομηνία")
                amount = st.number_input("Ποσό (€)", min_value=0.0)
                reason = st.text_input("Αιτιολογία")

            with col2:
                order_type = st.selectbox("Τύπος", ["Γενικό", "Ελεονομείο"])
                docs = st.text_area("Δικαιολογητικά (ένα ανά γραμμή)")

            approved = st.checkbox("✅ Εγκρίθηκε από Σεβάσμιο")

            submitted = st.form_submit_button("💾 Δημιουργία")

            if submitted and reason and amount > 0:
                # AI Compliance Check
                if st.session_state.config.anthropic_api_key and not approved:
                    st.warning("⚠️ Το ένταλμα δεν έχει εγκριθεί από τον Σεβάσμιο!")

                if not docs.strip():
                    st.error("❌ Απαιτούνται δικαιολογητικά έγγραφα (Άρθρο 36)")
                else:
                    conn = st.session_state.db_connection
                    docs_list = [d.strip() for d in docs.split('\n') if d.strip()]

                    conn.execute('''
                        INSERT INTO εντάλματα (ημερομηνία, ποσό, αιτιολογία, δικαιολογητικά, 
                                              τύπος, approved_by_sevασμιος, documents_attached)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (str(date), amount, reason, json.dumps(docs_list), order_type,
                          1 if approved else 0, 1))
                    conn.commit()

                    st.success("✅ Ένταλμα δημιουργήθηκε!")
                    st.rerun()


def show_reminders_page():
    """Σελίδα reminders & notifications"""
    st.header("🔔 Reminders & Ειδοποιήσεις")

    tab1, tab2, tab3 = st.tabs(["📅 Προγραμματισμένα", "🔔 Ρυθμίσεις", "📧 Ιστορικό"])

    with tab1:
        st.subheader("📅 Προγραμματισμένα Reminders")

        pending = st.session_state.task_manager.get_pending_tasks(days_ahead=30)

        if not pending.empty:
            for _, task in pending.iterrows():
                days_until = (datetime.datetime.strptime(task['due_date'], '%Y-%m-%d') -
                              datetime.datetime.now()).days

                col1, col2 = st.columns([4, 1])

                with col1:
                    st.write(f"**{task['title']}**")
                    st.write(f"Προθεσμία: {task['due_date']} ({days_until} μέρες)")

                with col2:
                    if st.button("📧 Στείλε Τώρα", key=f"send_{task['id']}"):
                        if st.session_state.reminder_system.send_reminder_email(
                                task.to_dict(),
                                st.session_state.config.admin_email
                        ):
                            st.success("✅ Εστάλη!")
        else:
            st.info("Δεν υπάρχουν προγραμματισμένα reminders")

    with tab2:
        st.subheader("🔔 Ρυθμίσεις Ειδοποιήσεων")

        with st.form("reminder_settings"):
            reminder_days = st.number_input(
                "Μέρες πριν την προθεσμία για υπενθύμιση:",
                min_value=1,
                max_value=30,
                value=st.session_state.config.reminder_days_before
            )

            email_frequency = st.selectbox(
                "Συχνότητα ελέγχου:",
                ["Καθημερινά (9:00)", "Κάθε 12 ώρες", "Κάθε 6 ώρες"]
            )

            send_overdue = st.checkbox("Αποστολή ειδοποίησης για ληξιπρόθεσμα", value=True)

            if st.form_submit_button("💾 Αποθήκευση"):
                st.session_state.config.reminder_days_before = reminder_days
                st.success("✅ Ρυθμίσεις αποθηκεύτηκαν!")

    with tab3:
        st.subheader("📧 Ιστορικό Αποστολών")
        st.info("🚧 Υπό κατασκευή - Ιστορικό email reminders")


def show_ai_assistant_page():
    """Σελίδα AI Assistant"""
    st.header("🤖 AI Assistant")

    if not st.session_state.config.anthropic_api_key:
        st.warning("⚠️ Παρακαλώ ρυθμίστε το Anthropic API Key στις ρυθμίσεις")
        return

    tab1, tab2 = st.tabs(["💬 Συζήτηση", "📋 Προτάσεις"])

    with tab1:
        st.subheader("💬 Ρωτήστε τον AI Assistant")

        user_question = st.text_area(
            "Ερώτηση:",
            placeholder="π.χ. Τι πρέπει να κάνω πριν τη συνεδρίαση του Σαββάτου;"
        )

        if st.button("🔍 Ρώτησε", use_container_width=True):
            if user_question:
                with st.spinner("Σκέφτομαι..."):
                    try:
                        client = st.session_state.ai_assistant.client
                        message = client.messages.create(
                            model="claude-sonnet-4-20250514",
                            max_tokens=2000,
                            system="""Είσαι AI assistant για Γραμματέα-Σφραγιδοφύλακα Μασονικής Στοάς.
Γνωρίζεις τον κανονισμό (Άρθρα 35-41) και βοηθάς με:
- Προθεσμίες και deadlines
- Διαδικασίες και υποχρεώσεις
- Έλεγχο συμμόρφωσης
- Προτάσεις για επόμενες ενέργειες""",
                            messages=[{"role": "user", "content": user_question}]
                        )

                        response = message.content[0].text
                        st.markdown("### 💡 Απάντηση:")
                        st.write(response)

                    except Exception as e:
                        st.error(f"Σφάλμα: {e}")

    with tab2:
        st.subheader("📋 Προτάσεις Ενεργειών")

        if st.button("🔄 Λήψη Προτάσεων", use_container_width=True):
            # Δημιουργία context
            conn = st.session_state.db_connection
            pending_tasks = st.session_state.task_manager.get_pending_tasks(days_ahead=7)

            context = f"""
Εκκρεμείς εργασίες: {len(pending_tasks)}
Ληξιπρόθεσμες: {len(st.session_state.task_manager.get_overdue_tasks())}
Προσεχείς συνεδριάσεις: {conn.execute("SELECT COUNT(*) FROM συνεδριάσεις WHERE date(ημερομηνία) > date('now')").fetchone()[0]}
"""

            suggestions = st.session_state.ai_assistant.get_task_suggestions(context)

            if suggestions:
                st.markdown("### 💡 Προτεινόμενες Ενέργειες:")
                for i, suggestion in enumerate(suggestions, 1):
                    st.markdown(f"{i}. {suggestion}")


def show_settings_page_complete():
    """Πλήρης σελίδα ρυθμίσεων"""
    st.header("⚙️ Ρυθμίσεις Συστήματος")

    tab1, tab2, tab3 = st.tabs(["📧 Email", "🤖 AI", "🏛️ Στοά"])

    with tab1:
        st.subheader("📧 Ρυθμίσεις Email")

        with st.form("email_config"):
            col1, col2 = st.columns(2)

            with col1:
                smtp_server = st.text_input("SMTP Server",
                                            value=st.session_state.config.smtp_server)
                smtp_port = st.number_input("Port", value=st.session_state.config.smtp_port)

            with col2:
                sender_email = st.text_input("Email Αποστολέα",
                                             value=st.session_state.config.sender_email)
                sender_password = st.text_input("Κωδικός",
                                                type="password",
                                                value=st.session_state.config.sender_password)

            admin_email = st.text_input("Email Γραμματέα (για reminders)",
                                        value=st.session_state.config.admin_email)

            if st.form_submit_button("💾 Αποθήκευση"):
                st.session_state.config.smtp_server = smtp_server
                st.session_state.config.smtp_port = smtp_port
                st.session_state.config.sender_email = sender_email
                st.session_state.config.sender_password = sender_password
                st.session_state.config.admin_email = admin_email

                st.success("✅ Ρυθμίσεις email αποθηκεύτηκαν!")

    with tab2:
        st.subheader("🤖 Ρυθμίσεις AI Assistant")

        with st.form("ai_config"):
            api_key = st.text_input(
                "Anthropic API Key",
                type="password",
                value=st.session_state.config.anthropic_api_key,
                help="Λάβετε το δωρεάν από https://console.anthropic.com"
            )

            if st.form_submit_button("💾 Αποθήκευση"):
                st.session_state.config.anthropic_api_key = api_key
                st.session_state.ai_assistant = AIAssistant(api_key)
                st.success("✅ API Key αποθηκεύτηκε!")

    with tab3:
        st.subheader("🏛️ Στοιχεία Στοάς")

        with st.form("lodge_config"):
            col1, col2 = st.columns(2)

            with col1:
                lodge_name = st.text_input("Όνομα Στοάς")
                grand_lodge_email = st.text_input("Email Μεγάλης Στοάς",
                                                  value=st.session_state.config.grand_lodge_email)

            with col2:
                lodge_orient = st.text_input("Ανατολή")
                grand_inspector_email = st.text_input("Email Μεγάλου Επιθεωρητή",
                                                      value=st.session_state.config.grand_inspector_email)

            if st.form_submit_button("💾 Αποθήκευση"):
                st.session_state.config.grand_lodge_email = grand_lodge_email
                st.session_state.config.grand_inspector_email = grand_inspector_email
                st.success("✅ Στοιχεία Στοάς αποθηκεύτηκαν!")


if __name__ == "__main__":
    main()