import os
import json
from datetime import datetime
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QFileDialog, QFrame,
    QTabWidget, QTextEdit, QWidget
)
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QHeaderView


def _check_admin_credentials(username: str, password: str) -> bool:
    expected_user = os.getenv('ADMIN_USERNAME', 'admin')
    expected_pass = os.getenv('ADMIN_PASSWORD', 'admin')
    return username == expected_user and password == expected_pass


class AdminLoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Admin Login")
        self.setModal(True)
        layout = QVBoxLayout(self)

        self.user_edit = QLineEdit(self)
        self.pass_edit = QLineEdit(self)
        self.pass_edit.setEchoMode(QLineEdit.Password)

        layout.addWidget(QLabel("Username"))
        layout.addWidget(self.user_edit)
        layout.addWidget(QLabel("Password"))
        layout.addWidget(self.pass_edit)

        btns = QHBoxLayout()
        self.login_btn = QPushButton("Login")
        self.cancel_btn = QPushButton("Cancel")
        btns.addWidget(self.login_btn)
        btns.addWidget(self.cancel_btn)
        layout.addLayout(btns)

        self.login_btn.clicked.connect(self.try_login)
        self.cancel_btn.clicked.connect(self.reject)

    def try_login(self):
        if _check_admin_credentials(self.user_edit.text().strip(), self.pass_edit.text().strip()):
            self.accept()
        else:
            QMessageBox.critical(self, "Access Denied", "Invalid admin credentials")


class AdminReportsDialog(QDialog):
    def __init__(self, cloud_uploader, parent=None):
        super().__init__(parent)
        self.cloud_uploader = cloud_uploader
        self.setWindowTitle("Admin Dashboard - Reports & Users (S3)")
        self.resize(1200, 750)

        layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #ddd;
                border-radius: 8px;
                background: white;
            }
            QTabBar::tab {
                background: #f0f0f0;
                color: #333;
                padding: 10px 20px;
                margin-right: 4px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background: #ff6600;
                color: white;
            }
            QTabBar::tab:hover {
                background: #ff7a26;
                color: white;
            }
        """)
        
        # Create Reports tab
        self.reports_tab = self.create_reports_tab()
        self.tabs.addTab(self.reports_tab, "📄 Reports")
        
        # Create Users tab
        self.users_tab = self.create_users_tab()
        self.tabs.addTab(self.users_tab, "👥 Users")
        
        layout.addWidget(self.tabs)

    def create_reports_tab(self):
        """Create the Reports tab widget"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # App-style header actions
        header = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("🔍 Search filename…")
        self.search_edit.setClearButtonEnabled(True)
        self.search_edit.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                border: 2px solid #ddd;
                border-radius: 8px;
                font-size: 13px;
                background: white;
            }
            QLineEdit:focus {
                border: 2px solid #ff6600;
            }
        """)
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.download_btn = QPushButton("⬇️ Download")
        self.copy_url_btn = QPushButton("🔗 Copy Link")
        for b in (self.refresh_btn, self.download_btn, self.copy_url_btn):
            b.setStyleSheet("""
                QPushButton {
                    background: #ff6600;
                    color: #fff;
                    border-radius: 10px;
                    padding: 8px 16px;
                    font-weight: bold;
                    font-size: 13px;
                    border: none;
                }
                QPushButton:hover {
                    background: #ff7a26;
                }
                QPushButton:pressed {
                    background: #e65c00;
                }
                QPushButton:disabled {
                    background: #ccc;
                    color: #666;
                }
            """)
        header.addWidget(self.search_edit, 3)
        header.addStretch(1)
        header.addWidget(self.refresh_btn)
        header.addWidget(self.download_btn)
        header.addWidget(self.copy_url_btn)
        layout.addLayout(header)

        # Summary cards
        cards = QHBoxLayout()
        self.count_card = self._metric_card("Total Files", "0")
        self.size_card = self._metric_card("Total Size", "0 KB")
        self.latest_card = self._metric_card("Latest Upload", "–")
        cards.addWidget(self.count_card)
        cards.addWidget(self.size_card)
        cards.addWidget(self.latest_card)
        layout.addLayout(cards)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["File", "Type", "Date", "Size (KB)", "S3 Key"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setAlternatingRowColors(True)
        self.table.setWordWrap(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setShowGrid(True)
        # Performance optimizations
        self.table.verticalHeader().setDefaultSectionSize(40)  # Fixed row height
        self.table.verticalHeader().setVisible(False)  # Hide row numbers
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)  # Read-only
        
        # Modern table styling matching Users tab
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                alternate-background-color: #f9f9f9;
                gridline-color: #e0e0e0;
                border: 1px solid #ddd;
                border-radius: 8px;
                font-size: 13px;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f0f0f0;
            }
            QTableWidget::item:selected {
                background-color: #ffe6cc;
                color: #333;
            }
            QTableWidget::item:hover {
                background-color: #fff5e6;
            }
            QHeaderView::section {
                background-color: #ff6600;
                color: white;
                padding: 10px;
                font-weight: bold;
                font-size: 13px;
                border: none;
                border-right: 1px solid #ff7a26;
            }
            QHeaderView::section:first {
                border-top-left-radius: 8px;
            }
            QHeaderView::section:last {
                border-top-right-radius: 8px;
                border-right: none;
            }
        """)
        
        # Make filename and key readable
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # File
        hh.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Type
        hh.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Date
        hh.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Size
        hh.setSectionResizeMode(4, QHeaderView.Stretch)           # S3 Key
        layout.addWidget(self.table)

        self.refresh_btn.clicked.connect(self.load_items)
        self.download_btn.clicked.connect(self.download_selected)
        self.copy_url_btn.clicked.connect(self.copy_link)
        self.search_edit.textChanged.connect(self.apply_filter)
        self.table.cellDoubleClicked.connect(lambda r,c: self.download_selected())

        self.load_items()
        
        return tab
    
    def create_users_tab(self):
        """Create the Users tab widget"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Header actions for users
        header = QHBoxLayout()
        self.user_search_edit = QLineEdit()
        self.user_search_edit.setPlaceholderText("🔍 Search username, phone, or name…")
        self.user_search_edit.setClearButtonEnabled(True)
        self.user_search_edit.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                border: 2px solid #ddd;
                border-radius: 8px;
                font-size: 13px;
                background: white;
            }
            QLineEdit:focus {
                border: 2px solid #ff6600;
            }
        """)
        self.user_refresh_btn = QPushButton("🔄 Refresh")
        self.link_report_btn = QPushButton("🔗 Link to Reports")
        for b in (self.user_refresh_btn, self.link_report_btn):
            b.setStyleSheet("""
                QPushButton {
                    background: #ff6600;
                    color: #fff;
                    border-radius: 10px;
                    padding: 8px 16px;
                    font-weight: bold;
                    font-size: 13px;
                    border: none;
                }
                QPushButton:hover {
                    background: #ff7a26;
                }
                QPushButton:pressed {
                    background: #e65c00;
                }
                QPushButton:disabled {
                    background: #ccc;
                    color: #666;
                }
            """)
        header.addWidget(self.user_search_edit, 3)
        header.addStretch(1)
        header.addWidget(self.user_refresh_btn)
        header.addWidget(self.link_report_btn)
        layout.addLayout(header)
        
        # Summary cards for users
        cards = QHBoxLayout()
        self.users_count_card = self._metric_card("Total Users", "0")
        self.latest_user_card = self._metric_card("Latest Registration", "–")
        cards.addWidget(self.users_count_card)
        cards.addWidget(self.latest_user_card)
        cards.addStretch()
        layout.addLayout(cards)
        
        # Users table with improved styling
        self.users_table = QTableWidget(0, 7)
        self.users_table.setHorizontalHeaderLabels(["Username", "Full Name", "Phone", "Age", "Gender", "Serial Number", "Registered"])
        self.users_table.horizontalHeader().setStretchLastSection(True)
        self.users_table.setAlternatingRowColors(True)
        self.users_table.setWordWrap(False)
        self.users_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.users_table.setSelectionMode(QTableWidget.SingleSelection)
        self.users_table.setShowGrid(True)
        # Performance optimizations
        self.users_table.verticalHeader().setDefaultSectionSize(40)  # Fixed row height
        self.users_table.verticalHeader().setVisible(False)  # Hide row numbers
        self.users_table.setEditTriggers(QTableWidget.NoEditTriggers)  # Read-only
        
        # Modern table styling
        self.users_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                alternate-background-color: #f9f9f9;
                gridline-color: #e0e0e0;
                border: 1px solid #ddd;
                border-radius: 8px;
                font-size: 13px;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f0f0f0;
            }
            QTableWidget::item:selected {
                background-color: #ffe6cc;
                color: #333;
            }
            QTableWidget::item:hover {
                background-color: #fff5e6;
            }
            QHeaderView::section {
                background-color: #ff6600;
                color: white;
                padding: 10px;
                font-weight: bold;
                font-size: 13px;
                border: none;
                border-right: 1px solid #ff7a26;
            }
            QHeaderView::section:first {
                border-top-left-radius: 8px;
            }
            QHeaderView::section:last {
                border-top-right-radius: 8px;
                border-right: none;
            }
        """)
        
        hh = self.users_table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(1, QHeaderView.Stretch)
        hh.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        layout.addWidget(self.users_table)
        
        # User details panel
        details_label = QLabel("User Details:")
        details_label.setStyleSheet("font-weight:bold;color:#ff6600;margin-top:10px;")
        layout.addWidget(details_label)
        
        self.user_details_text = QTextEdit()
        self.user_details_text.setReadOnly(True)
        self.user_details_text.setMaximumHeight(150)
        self.user_details_text.setStyleSheet("background:#f9f9f9;border:1px solid #ddd;border-radius:8px;padding:8px;")
        layout.addWidget(self.user_details_text)
        
        # Connect signals
        self.user_refresh_btn.clicked.connect(self.load_users)
        self.link_report_btn.clicked.connect(self.link_user_to_reports)
        self.user_search_edit.textChanged.connect(self.apply_user_filter)
        self.users_table.cellClicked.connect(self.show_user_details)
        self.users_table.cellDoubleClicked.connect(lambda r,c: self.link_user_to_reports())
        
        self.load_users()
        
        return tab

    def _metric_card(self, title: str, value: str) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:1 #f8f9fa);
                border-radius: 12px;
                border: 2px solid #ff6600;
                padding: 16px;
            }
            QLabel {
                color: #333;
                background: transparent;
            }
        """)
        v = QVBoxLayout(frame)
        v.setSpacing(8)
        v.setContentsMargins(12, 12, 12, 12)
        t = QLabel(title)
        t.setStyleSheet("font-weight:bold;color:#ff6600;font-size:12px;")
        val = QLabel(value)
        val.setStyleSheet("font-size:24px;font-weight:bold;color:#333;")
        v.addWidget(t)
        v.addWidget(val)
        v.addStretch(1)
        frame._value_label = val
        frame.setMinimumHeight(100)
        return frame

    def load_items(self):
        """Load reports from S3 - with caching"""
        # Check if already loaded and not stale
        if hasattr(self, '_all_items') and hasattr(self, '_last_load_time'):
            import time
            # Cache for 30 seconds to avoid unnecessary reloads
            if time.time() - self._last_load_time < 30:
                self.apply_filter()
                self._update_cards()
                return
        
        result = self.cloud_uploader.list_reports(prefix="ecg-reports/")
        if result.get('status') != 'success':
            QMessageBox.critical(self, "Error", f"Failed to list reports: {result.get('message')}")
            return
        self._all_items = result.get('items', [])
        
        import time
        self._last_load_time = time.time()
        
        self.apply_filter()
        self._update_cards()

    def _update_cards(self):
        items = getattr(self, '_filtered_items', [])
        total = len(items)
        total_size = sum(it.get('size', 0) for it in items)
        latest = max((it.get('last_modified') or '' for it in items), default='')
        self.count_card._value_label.setText(str(total))
        self.size_card._value_label.setText(self._format_size(total_size))
        try:
            if latest:
                latest_dt = datetime.fromisoformat(latest.replace('Z','+00:00')).strftime('%Y-%m-%d %H:%M:%S')
            else:
                latest_dt = '–'
        except Exception:
            latest_dt = latest or '–'
        self.latest_card._value_label.setText(latest_dt)

    def apply_filter(self):
        """Filter reports table - OPTIMIZED"""
        q = (self.search_edit.text() or '').strip().lower()
        items = getattr(self, '_all_items', [])
        if q:
            items = [it for it in items if q in os.path.basename(it['key']).lower()]
        self._filtered_items = items
        
        # Disable updates during bulk insert for performance
        self.table.setUpdatesEnabled(False)
        self.table.setRowCount(len(items))
        
        for i, it in enumerate(items):
            name = os.path.basename(it['key'])
            ftype = 'PDF' if name.lower().endswith('.pdf') else 'JSON'
            dt = it.get('last_modified') or ''
            try:
                if dt:
                    dt = datetime.fromisoformat(dt.replace('Z','+00:00')).strftime('%Y-%m-%d %H:%M:%S')
            except Exception:
                pass
            size_kb = int(it.get('size', 0) / 1024)
            
            # Batch create items
            items_row = [
                QTableWidgetItem(name),
                QTableWidgetItem(ftype),
                QTableWidgetItem(dt),
                QTableWidgetItem(str(size_kb)),
                QTableWidgetItem(it['key'])
            ]
            
            # Batch set all items for this row
            for col, item in enumerate(items_row):
                self.table.setItem(i, col, item)
        
        # Re-enable updates and refresh once
        self.table.setUpdatesEnabled(True)
        self.table.viewport().update()

    def _selected_key(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        item = self.table.item(row, 4)
        return item.text() if item else None

    def _format_size(self, num_bytes: int) -> str:
        try:
            units = ['B', 'KB', 'MB', 'GB', 'TB']
            size = float(num_bytes)
            idx = 0
            while size >= 1024 and idx < len(units) - 1:
                size /= 1024.0
                idx += 1
            if idx == 0:
                return f"{int(size)} {units[idx]}"
            return f"{size:.2f} {units[idx]}"
        except Exception:
            return f"{int(num_bytes/1024)} KB"

    def show_details(self):
        try:
            key = self._selected_key()
            if not key:
                self.details.setPlainText("")
                return
            
            # Prefer JSON twin
            json_key = key if key.lower().endswith('.json') else key.rsplit('.',1)[0] + '.json'
            
            # Try to get JSON from S3
            data = None
            url_res = self.cloud_uploader.generate_presigned_url(json_key)
            if url_res.get('status') == 'success':
                import requests, json
                try:
                    r = requests.get(url_res['url'], timeout=20)
                    if r.status_code == 200:
                        data = r.json()
                except Exception as e:
                    print(f"Failed to fetch JSON from S3: {e}")
            
            # If S3 fetch failed, try local file
            if not data:
                import json, os
                # Try local reports directory
                local_json = os.path.basename(json_key)
                local_paths = [
                    os.path.join("reports", local_json),
                    os.path.join("../reports", local_json),
                    local_json
                ]
                for lp in local_paths:
                    if os.path.exists(lp):
                        try:
                            with open(lp, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                            break
                        except Exception:
                            pass
            
            if not data:
                self.details.setHtml(
                    "<div style='padding:12px; color:#666;'>"
                    "<b>No JSON details available</b><br><br>"
                    f"Tried: {os.path.basename(json_key)}<br>"
                    "This report may not have associated metrics data."
                    "</div>"
                )
                return
            
            # Render key fields with better formatting
            patient = data.get('patient', {}) or {}
            user = data.get('user', {}) or {}
            metrics = data.get('metrics', {}) or {}
            machine = data.get('machine_serial', '')
            report_date = data.get('report_date', '')
            
            html_parts = []
            html_parts.append("<div style='padding:8px; font-family:Arial;'>")
            
            # Patient info
            html_parts.append("<div style='background:#fff3e0; padding:8px; border-radius:8px; margin-bottom:8px;'>")
            html_parts.append(f"<b style='color:#ff6600;'>Patient:</b> {patient.get('name','')} &nbsp; <b>Age:</b> {patient.get('age','')}")
            html_parts.append("</div>")
            
            # User info
            html_parts.append("<div style='background:#e3f2fd; padding:8px; border-radius:8px; margin-bottom:8px;'>")
            html_parts.append(f"<b style='color:#1976d2;'>User:</b> {user.get('name','')} &nbsp; <b>Phone:</b> {user.get('phone','')}")
            html_parts.append("</div>")
            
            # Machine info
            html_parts.append("<div style='background:#f1f8e9; padding:8px; border-radius:8px; margin-bottom:12px;'>")
            html_parts.append(f"<b style='color:#558b2f;'>Machine Serial:</b> {machine} &nbsp; <b>Date:</b> {report_date}")
            html_parts.append("</div>")
            
            # Metrics table
            html_parts.append("<div style='background:#fafafa; padding:8px; border-radius:8px;'>")
            html_parts.append("<b style='color:#ff6600;'>ECG Metrics:</b><br><br>")
            html_parts.append("<table style='width:100%; font-size:13px;'>")
            for k, v in metrics.items():
                html_parts.append(f"<tr><td style='padding:4px; font-weight:bold; color:#333;'>{k}:</td><td style='padding:4px;'>{v}</td></tr>")
            html_parts.append("</table>")
            html_parts.append("</div>")
            
            html_parts.append("</div>")
            
            self.details.setHtml("".join(html_parts))
        except Exception as e:
            import traceback
            self.details.setPlainText(f"Failed to load details:\n{e}\n\n{traceback.format_exc()}")

    def download_selected(self):
        key = self._selected_key()
        if not key:
            QMessageBox.information(self, "Select", "Select a report first")
            return
        # Choose local folder
        dest_dir = QFileDialog.getExistingDirectory(self, "Choose download folder")
        if not dest_dir:
            return
        # Download via presigned URL (simple)
        url_res = self.cloud_uploader.generate_presigned_url(key)
        if url_res.get('status') != 'success':
            QMessageBox.critical(self, "Error", f"Could not create link: {url_res.get('message')}")
            return
        try:
            import requests
            r = requests.get(url_res['url'], timeout=60)
            r.raise_for_status()
            local_path = os.path.join(dest_dir, os.path.basename(key))
            with open(local_path, 'wb') as f:
                f.write(r.content)
            QMessageBox.information(self, "Saved", f"Downloaded to:\n{local_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Download failed: {e}")

    def copy_link(self):
        key = self._selected_key()
        if not key:
            QMessageBox.information(self, "Select", "Select a report first")
            return
        url_res = self.cloud_uploader.generate_presigned_url(key)
        if url_res.get('status') != 'success':
            QMessageBox.critical(self, "Error", f"Could not create link: {url_res.get('message')}")
            return
        from PyQt5.QtWidgets import QApplication
        QApplication.clipboard().setText(url_res['url'])
        QMessageBox.information(self, "Copied", "Presigned URL copied to clipboard (valid ~1 hour)")
    
    # ===== Users Tab Methods =====
    
    def load_users(self):
        """Load user signup data from S3 in background thread"""
        # Show loading message
        self.user_details_text.setHtml("<div style='padding:20px;text-align:center;color:#ff6600;'><b>⏳ Loading users from S3...</b></div>")
        self.users_table.setRowCount(0)
        
        # Disable buttons during load
        self.user_refresh_btn.setEnabled(False)
        self.link_report_btn.setEnabled(False)
        
        # Load in background thread to prevent UI freeze
        from PyQt5.QtCore import QThread, pyqtSignal
        
        class LoadUsersThread(QThread):
            finished = pyqtSignal(list)
            error = pyqtSignal(str)
            
            def __init__(self, cloud_uploader):
                super().__init__()
                self.cloud_uploader = cloud_uploader
            
            def run(self):
                try:
                    result = self.cloud_uploader.list_reports(prefix="ecg-reports/")
                    if result.get('status') != 'success':
                        self.error.emit(f"Failed to list files: {result.get('message')}")
                        return
                    
                    all_items = result.get('items', [])
                    # Filter for user_signup JSON files
                    user_files = [item for item in all_items if 'user_signup' in item['key'].lower() and item['key'].lower().endswith('.json')]
                    
                    users = []
                    import requests
                    
                    # Batch download with connection pooling for speed
                    session = requests.Session()
                    for user_file in user_files:
                        try:
                            url_res = self.cloud_uploader.generate_presigned_url(user_file['key'])
                            if url_res.get('status') == 'success':
                                r = session.get(url_res['url'], timeout=5)
                                if r.status_code == 200:
                                    user_data = r.json()
                                    user_data['s3_key'] = user_file['key']
                                    users.append(user_data)
                        except Exception as e:
                            print(f"Failed to load {user_file['key']}: {e}")
                    
                    session.close()
                    self.finished.emit(users)
                    
                except Exception as e:
                    self.error.emit(str(e))
        
        def on_users_loaded(users):
            self._all_users = users
            self.apply_user_filter()
            self._update_user_cards()
            self.user_refresh_btn.setEnabled(True)
            self.link_report_btn.setEnabled(True)
            self.user_details_text.setHtml("<div style='padding:20px;text-align:center;color:#666;'><b>✅ Users loaded! Select a user to view details.</b></div>")
        
        def on_error(error_msg):
            QMessageBox.critical(self, "Error", f"Failed to load users: {error_msg}")
            self.user_refresh_btn.setEnabled(True)
            self.link_report_btn.setEnabled(True)
            self.user_details_text.setHtml(f"<div style='padding:20px;color:red;'><b>❌ Error: {error_msg}</b></div>")
        
        self.load_thread = LoadUsersThread(self.cloud_uploader)
        self.load_thread.finished.connect(on_users_loaded)
        self.load_thread.error.connect(on_error)
        self.load_thread.start()
    
    def apply_user_filter(self):
        """Filter users table based on search - OPTIMIZED"""
        q = (self.user_search_edit.text() or '').strip().lower()
        users = getattr(self, '_all_users', [])
        
        if q:
            users = [u for u in users if 
                     q in u.get('username', '').lower() or 
                     q in u.get('full_name', '').lower() or 
                     q in u.get('phone', '').lower()]
        
        self._filtered_users = users
        
        # Disable updates during bulk insert for performance
        self.users_table.setUpdatesEnabled(False)
        self.users_table.setRowCount(len(users))
        
        # Batch insert items
        for i, user in enumerate(users):
            # Create items without triggering individual updates
            items = [
                QTableWidgetItem(user.get('username', '')),
                QTableWidgetItem(user.get('full_name', '')),
                QTableWidgetItem(user.get('phone', '')),
                QTableWidgetItem(str(user.get('age', ''))),
                QTableWidgetItem(user.get('gender', '')),
                QTableWidgetItem(user.get('serial_number', ''))
            ]
            
            # Format date
            registered = user.get('registered_at', '')
            try:
                if registered:
                    registered = datetime.fromisoformat(registered).strftime('%Y-%m-%d %H:%M')
            except:
                pass
            items.append(QTableWidgetItem(registered))
            
            # Batch set all items for this row
            for col, item in enumerate(items):
                self.users_table.setItem(i, col, item)
        
        # Re-enable updates and refresh once
        self.users_table.setUpdatesEnabled(True)
        self.users_table.viewport().update()
    
    def _update_user_cards(self):
        """Update user summary cards"""
        users = getattr(self, '_filtered_users', [])
        total = len(users)
        latest = max((u.get('registered_at') or '' for u in users), default='')
        
        self.users_count_card._value_label.setText(str(total))
        
        try:
            if latest:
                latest_dt = datetime.fromisoformat(latest).strftime('%Y-%m-%d %H:%M:%S')
            else:
                latest_dt = '–'
        except:
            latest_dt = latest or '–'
        self.latest_user_card._value_label.setText(latest_dt)
    
    def show_user_details(self, row, col):
        """Show detailed information for selected user - OPTIMIZED"""
        try:
            users = getattr(self, '_filtered_users', [])
            if row < 0 or row >= len(users):
                return
            
            user = users[row]
            
            # Format user details as HTML with modern styling
            html = """
            <div style='font-family:Arial; padding:12px; background:#f9f9f9; border-radius:8px;'>
                <div style='background:linear-gradient(135deg, #ff6600 0%, #ff8533 100%); 
                            padding:12px; border-radius:8px; margin-bottom:12px;'>
                    <b style='color:white; font-size:16px;'>👤 {full_name}</b>
                </div>
                <table style='width:100%; font-size:13px;'>
                    <tr style='background:#fff5e6;'>
                        <td style='padding:8px; font-weight:bold; width:40%;'>Username:</td>
                        <td style='padding:8px;'>{username}</td>
                    </tr>
                    <tr>
                        <td style='padding:8px; font-weight:bold;'>Phone:</td>
                        <td style='padding:8px;'>{phone}</td>
                    </tr>
                    <tr style='background:#fff5e6;'>
                        <td style='padding:8px; font-weight:bold;'>Age:</td>
                        <td style='padding:8px;'>{age}</td>
                    </tr>
                    <tr>
                        <td style='padding:8px; font-weight:bold;'>Gender:</td>
                        <td style='padding:8px;'>{gender}</td>
                    </tr>
                    <tr style='background:#fff5e6;'>
                        <td style='padding:8px; font-weight:bold;'>Address:</td>
                        <td style='padding:8px;'>{address}</td>
                    </tr>
                    <tr>
                        <td style='padding:8px; font-weight:bold;'>Machine Serial:</td>
                        <td style='padding:8px;'>{serial}</td>
                    </tr>
                    <tr style='background:#fff5e6;'>
                        <td style='padding:8px; font-weight:bold;'>Registered:</td>
                        <td style='padding:8px;'>{registered}</td>
                    </tr>
                </table>
            </div>
            """.format(
                full_name=user.get('full_name', 'N/A'),
                username=user.get('username', 'N/A'),
                phone=user.get('phone', 'N/A'),
                age=user.get('age', 'N/A'),
                gender=user.get('gender', 'N/A'),
                address=user.get('address', 'N/A'),
                serial=user.get('serial_number', 'N/A'),
                registered=user.get('registered_at', 'N/A')
            )
            
            self.user_details_text.setHtml(html)
            
        except Exception as e:
            self.user_details_text.setPlainText(f"Error loading details: {e}")
    
    def link_user_to_reports(self):
        """Switch to Reports tab and filter by selected user's serial number or phone"""
        try:
            row = self.users_table.currentRow()
            if row < 0:
                QMessageBox.information(self, "Select User", "Please select a user first")
                return
            
            users = getattr(self, '_filtered_users', [])
            if row >= len(users):
                return
            
            user = users[row]
            serial = user.get('serial_number', '')
            phone = user.get('phone', '')
            name = user.get('full_name', '')
            
            # Switch to Reports tab
            self.tabs.setCurrentIndex(0)
            
            # Apply filter to show this user's reports
            # Try filtering by serial number first, then phone
            filter_text = serial if serial else phone
            if filter_text:
                self.search_edit.setText(filter_text)
                QMessageBox.information(
                    self, 
                    "Reports Filtered", 
                    f"Now showing reports for:\n{name}\n\nFiltered by: {filter_text}"
                )
            else:
                QMessageBox.warning(self, "No Filter", "This user has no serial number or phone to filter by")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to link user to reports: {str(e)}")


