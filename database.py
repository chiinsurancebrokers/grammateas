"""
Database Operations Module
Όλες οι database λειτουργίες σε ένα module
"""

import sqlite3
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime

class Database:
    """Διαχείριση βάσης δεδομένων"""
    
    def __init__(self, db_path: str = 'lodge_members.db'):
        self.db_path = db_path
        self._init_tables()
    
    def _init_tables(self):
        """Δημιουργία πινάκων αν δεν υπάρχουν"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tasks table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                task_id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                due_date TEXT,
                priority TEXT DEFAULT 'Μεσαία',
                status TEXT DEFAULT 'Εκκρεμής',
                category TEXT,
                assigned_to TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                completed_at TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    # ==================== MEMBERS ====================
    
    def get_all_members(self) -> pd.DataFrame:
        """Λήψη όλων των μελών"""
        conn = self.get_connection()
        df = pd.read_sql_query("""
            SELECT 
                member_id, last_name, first_name, fathers_name,
                birth_date, mobile_phone, email,
                initiation_date, current_degree, member_status,
                financial_status
            FROM members
            ORDER BY last_name, first_name
        """, conn)
        conn.close()
        return df
    
    def get_member_by_id(self, member_id: int) -> Optional[Dict]:
        """Λήψη μέλους με ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM members WHERE member_id = ?", (member_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, row))
        return None
    
    def update_member(self, member_id: int, data: Dict):
        """Ενημέρωση μέλους"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Build UPDATE query
        fields = ', '.join([f"{k} = ?" for k in data.keys()])
        values = list(data.values()) + [member_id]
        
        query = f"UPDATE members SET {fields} WHERE member_id = ?"
        cursor.execute(query, values)
        
        conn.commit()
        conn.close()
    
    def search_members(self, search_term: str) -> pd.DataFrame:
        """Αναζήτηση μελών"""
        conn = self.get_connection()
        query = """
            SELECT * FROM members
            WHERE last_name LIKE ? OR first_name LIKE ? OR mobile_phone LIKE ?
            ORDER BY last_name, first_name
        """
        search_pattern = f"%{search_term}%"
        df = pd.read_sql_query(query, conn, params=(search_pattern, search_pattern, search_pattern))
        conn.close()
        return df
    
    def get_member_statistics(self) -> Dict:
        """Στατιστικά μελών"""
        conn = self.get_connection()
        
        stats = {}
        
        # Total members
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM members")
        stats['total'] = cursor.fetchone()[0]
        
        # By status
        cursor.execute("SELECT member_status, COUNT(*) FROM members GROUP BY member_status")
        stats['by_status'] = dict(cursor.fetchall())
        
        # By degree
        cursor.execute("SELECT current_degree, COUNT(*) FROM members GROUP BY current_degree")
        stats['by_degree'] = dict(cursor.fetchall())
        
        # Active members
        cursor.execute("SELECT COUNT(*) FROM members WHERE member_status = 'Ενεργό'")
        stats['active'] = cursor.fetchone()[0]
        
        conn.close()
        return stats
    
    # ==================== TASKS ====================
    
    def add_task(self, title: str, description: str, due_date: str, 
                 priority: str = 'Μεσαία', category: str = 'Γενικά'):
        """Προσθήκη εργασίας"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO tasks (title, description, due_date, priority, category)
            VALUES (?, ?, ?, ?, ?)
        ''', (title, description, due_date, priority, category))
        conn.commit()
        conn.close()
    
    def get_all_tasks(self, status_filter: Optional[str] = None) -> pd.DataFrame:
        """Λήψη όλων των εργασιών"""
        conn = self.get_connection()
        query = "SELECT * FROM tasks"
        params = []
        
        if status_filter and status_filter != "Όλες":
            query += " WHERE status = ?"
            params.append(status_filter)
        
        query += " ORDER BY due_date ASC"
        df = pd.read_sql_query(query, conn, params=params if params else None)
        conn.close()
        return df
    
    def update_task_status(self, task_id: int, new_status: str):
        """Ενημέρωση κατάστασης εργασίας"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        completed_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S') if new_status == 'Ολοκληρωμένη' else None
        
        cursor.execute('''
            UPDATE tasks 
            SET status = ?, completed_at = ?
            WHERE task_id = ?
        ''', (new_status, completed_at, task_id))
        conn.commit()
        conn.close()
    
    def delete_task(self, task_id: int):
        """Διαγραφή εργασίας"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tasks WHERE task_id = ?", (task_id,))
        conn.commit()
        conn.close()
    
    def get_upcoming_tasks(self, days: int = 7) -> pd.DataFrame:
        """Εργασίες που πλησιάζουν"""
        from datetime import timedelta
        conn = self.get_connection()
        today = datetime.now().date()
        future = today + timedelta(days=days)
        
        query = '''
            SELECT * FROM tasks 
            WHERE status != 'Ολοκληρωμένη' 
            AND due_date BETWEEN ? AND ?
            ORDER BY due_date ASC
        '''
        df = pd.read_sql_query(query, conn, params=(str(today), str(future)))
        conn.close()
        return df
    
    def get_overdue_tasks(self) -> pd.DataFrame:
        """Εργασίες που καθυστερούν"""
        conn = self.get_connection()
        today = datetime.now().date()
        
        query = '''
            SELECT * FROM tasks 
            WHERE status != 'Ολοκληρωμένη' 
            AND due_date < ?
            ORDER BY due_date ASC
        '''
        df = pd.read_sql_query(query, conn, params=(str(today),))
        conn.close()
        return df

# Singleton instance
_db_instance = None

def get_database() -> Database:
    """Get or create database instance"""
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance
