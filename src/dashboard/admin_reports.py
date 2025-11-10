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
        self.resize(1400, 850)  # Increased size for better viewing
        
        # Apply modern window styling
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f8f9fa, stop:1 #e9ecef);
            }
        """)

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

        # Summary cards - Modern design with icons and colors
        cards = QHBoxLayout()
        cards.setSpacing(16)
        self.count_card = self._metric_card("Total Files", "0", "■", "#9C27B0")
        self.size_card = self._metric_card("Total Size", "0 KB", "▲", "#FF9800")
        self.latest_card = self._metric_card("Latest Upload", "–", "◆", "#00BCD4")
        cards.addWidget(self.count_card, 1)
        cards.addWidget(self.size_card, 1)
        cards.addWidget(self.latest_card, 1)
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
        
        # Summary cards for users - Modern design with icons and colors
        cards = QHBoxLayout()
        cards.setSpacing(16)
        self.users_count_card = self._metric_card("Total Users", "0", "●", "#4CAF50")
        self.latest_user_card = self._metric_card("Latest Registration", "–", "◆", "#2196F3")
        cards.addWidget(self.users_count_card, 1)
        cards.addWidget(self.latest_user_card, 1)
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
        
        # Main horizontal split: Table (left) + Sidebar (right)
        main_horizontal = QHBoxLayout()
        main_horizontal.setSpacing(16)
        
        # Left side: Full-page user table
        table_container = QFrame()
        table_container.setStyleSheet("""
            QFrame {
                background: white;
                border-radius: 12px;
                border: 1px solid #e0e0e0;
                padding: 0px;
            }
        """)
        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(0, 0, 0, 0)
        table_layout.addWidget(self.users_table)
        main_horizontal.addWidget(table_container, 2)  # Table takes 2/3 of width
        
        # Right side: Collapsible sidebar for patient details
        self.sidebar_frame = QFrame()
        self.sidebar_frame.setStyleSheet("""
            QFrame {
                background: white;
                border-radius: 12px;
                border: 2px solid #ff6600;
                padding: 16px;
            }
        """)
        self.sidebar_frame.setMinimumWidth(400)
        self.sidebar_frame.setMaximumWidth(500)
        self.sidebar_frame.setVisible(False)  # Hidden by default until user clicks
        
        sidebar_layout = QVBoxLayout(self.sidebar_frame)
        sidebar_layout.setSpacing(12)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        
        # Sidebar header with close button
        sidebar_header = QHBoxLayout()
        sidebar_title = QLabel("📊 Patient Details")
        sidebar_title.setStyleSheet("font-weight:bold;color:#ff6600;font-size:16px;")
        sidebar_header.addWidget(sidebar_title)
        
        self.close_sidebar_btn = QPushButton("✕")
        self.close_sidebar_btn.setFixedSize(32, 32)
        self.close_sidebar_btn.setStyleSheet("""
            QPushButton {
                background: #f44336;
                color: white;
                border-radius: 16px;
                font-size: 18px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover {
                background: #d32f2f;
            }
        """)
        self.close_sidebar_btn.clicked.connect(self.close_sidebar)
        sidebar_header.addWidget(self.close_sidebar_btn)
        sidebar_layout.addLayout(sidebar_header)
        
        # Scrollable patient details
        self.user_details_text = QTextEdit()
        self.user_details_text.setReadOnly(True)
        self.user_details_text.setStyleSheet("""
            QTextEdit {
                background: #fafafa;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 12px;
                font-size: 13px;
            }
        """)
        sidebar_layout.addWidget(self.user_details_text)
        
        main_horizontal.addWidget(self.sidebar_frame, 1)  # Sidebar takes 1/3 of width
        
        layout.addLayout(main_horizontal)
        
        # Connect signals
        self.user_refresh_btn.clicked.connect(self.load_users)
        self.link_report_btn.clicked.connect(self.link_user_to_reports)
        self.user_search_edit.textChanged.connect(self.apply_user_filter)
        self.users_table.cellClicked.connect(self.show_user_details)
        self.users_table.cellDoubleClicked.connect(lambda r,c: self.link_user_to_reports())
        
        self.load_users()
        
        return tab

    def _metric_card(self, title: str, value: str, icon: str = "📊", color: str = "#ff6600") -> QFrame:
        """Create a modern, professional metric card with icon and gradient"""
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #ffffff, stop:0.5 {color}08, stop:1 {color}15);
                border-radius: 16px;
                border: none;
                padding: 0px;
            }}
            QFrame:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #ffffff, stop:0.5 {color}12, stop:1 {color}20);
            }}
        """)
        
        # Add subtle shadow effect
        from PyQt5.QtWidgets import QGraphicsDropShadowEffect
        from PyQt5.QtGui import QColor
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 30))
        frame.setGraphicsEffect(shadow)
        
        v = QVBoxLayout(frame)
        v.setSpacing(12)
        v.setContentsMargins(20, 20, 20, 20)
        
        # Top row: Icon + Title
        top_row = QHBoxLayout()
        top_row.setSpacing(8)
        
        icon_label = QLabel(icon)
        icon_label.setStyleSheet(f"""
            font-size: 32px;
            background: {color};
            border-radius: 12px;
            padding: 8px;
            min-width: 48px;
            max-width: 48px;
            min-height: 48px;
            max-height: 48px;
        """)
        icon_label.setAlignment(Qt.AlignCenter)
        top_row.addWidget(icon_label)
        
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            font-weight: bold;
            color: #666;
            font-size: 13px;
            letter-spacing: 0.5px;
            text-transform: uppercase;
            background: transparent;
        """)
        title_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        top_row.addWidget(title_label, 1)
        
        v.addLayout(top_row)
        
        # Value with accent bar
        value_container = QFrame()
        value_container.setStyleSheet(f"""
            QFrame {{
                background: transparent;
                border-left: 4px solid {color};
                padding-left: 12px;
            }}
        """)
        value_layout = QVBoxLayout(value_container)
        value_layout.setContentsMargins(0, 0, 0, 0)
        
        val = QLabel(value)
        val.setStyleSheet(f"""
            font-size: 36px;
            font-weight: bold;
            color: {color};
            background: transparent;
        """)
        val.setAlignment(Qt.AlignLeft)
        value_layout.addWidget(val)
        
        v.addWidget(value_container)
        
        frame._value_label = val
        frame.setMinimumHeight(140)
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
        
        # Cache reports globally for patient lookup
        self._cached_reports = self._all_items
        
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
        """Show detailed information for selected user with ECG metrics and reports - CRASH-PROOF"""
        try:
            print(f"🖱️ User clicked row {row}, col {col}")
            
            users = getattr(self, '_filtered_users', [])
            if row < 0 or row >= len(users):
                print(f"⚠️ Invalid row selection: {row}")
                return
            
            user = users[row]
            print(f"👤 Selected user: {user.get('full_name', 'Unknown')}")
            
            # Show loading state
            try:
                self.user_details_text.setHtml("""
                    <div style='text-align:center; padding:40px; color:#ff6600;'>
                        <b style='font-size:16px;'>⏳ Loading patient data...</b><br>
                        <span style='font-size:12px; color:#666; margin-top:8px;'>
                            Fetching ECG metrics and reports from cloud...
                        </span>
                    </div>
                """)
            except Exception as html_err:
                print(f"⚠️ Error showing loading state: {html_err}")
            
            # Show sidebar with animation
            try:
                if hasattr(self, 'sidebar_frame'):
                    self.sidebar_frame.setVisible(True)
                    print(f"✅ Sidebar opened")
                else:
                    print(f"⚠️ Sidebar frame not found - using inline display")
            except Exception as sidebar_err:
                print(f"⚠️ Error showing sidebar: {sidebar_err}")
            
            # Process user selection with delay to allow UI update
            try:
                from PyQt5.QtCore import QTimer
                QTimer.singleShot(50, lambda: self._load_user_details_async(user))
            except Exception as timer_err:
                print(f"❌ Error scheduling async load: {timer_err}")
                # Fallback: load synchronously
                self._load_user_details_async(user)
            
        except Exception as e:
            print(f"❌ Critical error in show_user_details: {e}")
            import traceback
            traceback.print_exc()
            
            # Don't crash - show error message
            try:
                self.user_details_text.setHtml("""
                    <div style='padding:20px; text-align:center; color:#f44336;'>
                        <b>⚠️ Error</b><br><br>
                        Could not load patient details. Please try again.
                    </div>
                """)
            except:
                pass  # Silent fail - don't crash the entire app
    
    def close_sidebar(self):
        """Close the patient details sidebar"""
        self.sidebar_frame.setVisible(False)
        self.users_table.clearSelection()
    
    def _load_user_details_async(self, user):
        """Load user details asynchronously to prevent UI freeze - CRASH-PROOF"""
        try:
            print(f"📊 Loading details for user: {user.get('full_name', 'Unknown')}")
            
            # Fetch patient reports and metrics from S3
            serial = user.get('serial_number', '')
            phone = user.get('phone', '')
            
            # Wrap in try-catch to prevent crashes
            patient_reports = []
            latest_metrics = None
            
            try:
                # Get all reports for this patient
                patient_reports = self.get_patient_reports(serial, phone)
                print(f"✅ Found {len(patient_reports)} reports for patient")
            except Exception as e:
                print(f"⚠️ Error fetching patient reports: {e}")
                patient_reports = []
            
            try:
                # Get latest ECG metrics from most recent report
                latest_metrics = self.get_latest_patient_metrics(serial, phone)
                if latest_metrics:
                    print(f"✅ Loaded ECG metrics successfully")
                else:
                    print(f"⚠️ No metrics found for patient")
            except Exception as e:
                print(f"⚠️ Error fetching patient metrics: {e}")
                latest_metrics = None
            
            # Build enhanced HTML with patient info, metrics, and reports
            html_parts = []
            html_parts.append("<div style='font-family:Arial; padding:12px; background:#f9f9f9; border-radius:8px;'>")
            
            # Patient Header
            html_parts.append("""
                <div style='background:linear-gradient(135deg, #ff6600 0%, #ff8533 100%); 
                            padding:16px; border-radius:8px; margin-bottom:16px;'>
                    <b style='color:white; font-size:18px;'>👤 {full_name}</b>
                    <div style='color:#ffe0cc; font-size:12px; margin-top:4px;'>Patient ID: {serial}</div>
                </div>
            """.format(full_name=user.get('full_name', 'N/A'), serial=user.get('serial_number', 'N/A')))
            
            # Basic Info Card
            html_parts.append("<div style='background:white; padding:12px; border-radius:8px; margin-bottom:12px; border:1px solid #e0e0e0;'>")
            html_parts.append("<b style='color:#ff6600; font-size:14px;'>📋 Basic Information</b>")
            html_parts.append("<table style='width:100%; font-size:13px; margin-top:8px;'>")
            info_items = [
                ("Username", user.get('username', 'N/A')),
                ("Phone", user.get('phone', 'N/A')),
                ("Age", user.get('age', 'N/A')),
                ("Gender", user.get('gender', 'N/A')),
                ("Address", user.get('address', 'N/A')),
                ("Registered", user.get('registered_at', 'N/A'))
            ]
            for i, (label, value) in enumerate(info_items):
                bg = '#fff5e6' if i % 2 == 0 else 'white'
                html_parts.append(f"<tr style='background:{bg};'><td style='padding:6px; font-weight:bold; width:40%;'>{label}:</td><td style='padding:6px;'>{value}</td></tr>")
            html_parts.append("</table></div>")
            
            # ECG Metrics Card (if available)
            if latest_metrics:
                html_parts.append("<div style='background:white; padding:12px; border-radius:8px; margin-bottom:12px; border:1px solid #e0e0e0;'>")
                html_parts.append("<b style='color:#ff6600; font-size:14px;'>💓 Latest ECG Metrics</b>")
                html_parts.append("<div style='color:#666; font-size:11px; margin-top:2px;'>From most recent report</div>")
                
                # Display key metrics in a grid
                html_parts.append("<div style='display:grid; grid-template-columns:1fr 1fr; gap:8px; margin-top:12px;'>")
                
                metric_items = [
                    ("Heart Rate", latest_metrics.get('Heart_Rate', '--'), "bpm", "#e74c3c"),
                    ("PR Interval", latest_metrics.get('PR_Interval', '--'), "ms", "#3498db"),
                    ("QRS Duration", latest_metrics.get('QRS_Duration', '--'), "ms", "#2ecc71"),
                    ("QRS Axis", latest_metrics.get('QRS_Axis', '--'), "°", "#9b59b6"),
                    ("ST Segment", latest_metrics.get('ST_Segment', '--'), "mV", "#f39c12"),
                    ("QTc Interval", latest_metrics.get('QTc_Interval', '--'), "ms", "#1abc9c"),
                    ("Rhythm", latest_metrics.get('Rhythm_Interpretation', '--'), "", "#e67e22"),
                    ("Report Date", latest_metrics.get('report_date', '--'), "", "#95a5a6")
                ]
                
                for label, value, unit, color in metric_items:
                    html_parts.append(f"""
                        <div style='background:linear-gradient(135deg, {color}15 0%, {color}05 100%); 
                                    padding:10px; border-radius:6px; border-left:3px solid {color};'>
                            <div style='font-size:11px; color:#666; font-weight:bold;'>{label}</div>
                            <div style='font-size:16px; font-weight:bold; color:{color}; margin-top:4px;'>{value} {unit}</div>
                        </div>
                    """)
                
                html_parts.append("</div></div>")
            else:
                html_parts.append("<div style='background:#fff3cd; padding:12px; border-radius:8px; margin-bottom:12px; border:1px solid #ffc107;'>")
                html_parts.append("<b style='color:#ff6600;'>⚠️ No ECG metrics found</b><br>")
                html_parts.append("<span style='font-size:12px; color:#666;'>This patient hasn't generated any reports yet.</span>")
                html_parts.append("</div>")
            
            # Patient Reports List
            html_parts.append("<div style='background:white; padding:12px; border-radius:8px; border:1px solid #e0e0e0;'>")
            html_parts.append(f"<b style='color:#ff6600; font-size:14px;'>📊 Patient Reports ({len(patient_reports)})</b>")
            
            if patient_reports:
                html_parts.append("<div style='margin-top:12px; max-height:250px; overflow-y:auto;'>")
                for i, report in enumerate(patient_reports[:10]):  # Show latest 10
                    bg = '#f8f9fa' if i % 2 == 0 else 'white'
                    report_name = os.path.basename(report.get('key', 'Unknown'))
                    report_date = report.get('last_modified', 'Unknown')
                    report_size = self._format_size(report.get('size', 0))
                    
                    html_parts.append(f"""
                        <div style='background:{bg}; padding:10px; border-radius:6px; margin-bottom:6px; border:1px solid #e0e0e0;'>
                            <div style='font-weight:bold; color:#333; font-size:13px;'>📄 {report_name}</div>
                            <div style='font-size:11px; color:#666; margin-top:4px;'>
                                📅 {report_date} &nbsp;&nbsp; 💾 {report_size}
                            </div>
                        </div>
                    """)
                
                if len(patient_reports) > 10:
                    html_parts.append(f"<div style='text-align:center; color:#666; font-size:12px; margin-top:8px;'>... and {len(patient_reports) - 10} more reports</div>")
                
                html_parts.append("</div>")
            else:
                html_parts.append("<div style='text-align:center; padding:20px; color:#999;'>No reports found for this patient</div>")
            
            html_parts.append("</div>")
            html_parts.append("</div>")
            
            # Safely set HTML - catch any rendering errors
            try:
                self.user_details_text.setHtml("".join(html_parts))
                print(f"✅ Successfully displayed patient details for {user.get('full_name', 'Unknown')}")
            except Exception as render_err:
                print(f"❌ Error rendering HTML: {render_err}")
                self.user_details_text.setPlainText(f"Patient: {user.get('full_name', 'Unknown')}\n\nError displaying details. Please try again.")
            
        except Exception as e:
            print(f"❌ Critical error in _load_user_details_async: {e}")
            import traceback
            traceback.print_exc()
            
            # Show user-friendly error message instead of crashing
            try:
                error_msg = str(e)[:100] if e else "Unknown error"
                patient_name = user.get('full_name', 'Unknown') if isinstance(user, dict) else 'Unknown'
                self.user_details_text.setHtml(f"""
                    <div style='padding:20px; text-align:center;'>
                        <b style='color:#f44336; font-size:16px;'>⚠️ Error Loading Patient Data</b><br><br>
                        <span style='color:#666; font-size:13px;'>
                            Unable to load details for this patient.<br>
                            This might be due to network issues or missing data.<br><br>
                            <b>Patient:</b> {patient_name}<br>
                            <b>Error:</b> {error_msg}
                        </span>
                    </div>
                """)
            except:
                # Last resort fallback
                self.user_details_text.setPlainText("Error loading patient data. Please try again.")
    
    def get_patient_reports(self, serial, phone):
        """Get all reports for a specific patient by checking JSON metadata - CRASH-PROOF"""
        try:
            all_reports = getattr(self, '_cached_reports', [])
            if not all_reports:
                print(f"⚠️ No cached reports available")
                return []
            
            patient_reports = []
            
            print(f"🔍 Searching {len(all_reports)} reports for patient: serial={serial}, phone={phone}")
            
            # First, try filename matching (fast)
            for report in all_reports:
                key = report.get('key', '')
                if not key.endswith('.pdf'):
                    continue
                    
                # Check if serial or phone appears in the key/filename
                if (serial and serial in key) or (phone and phone in key):
                    patient_reports.append(report)
                    print(f"✅ Found report by filename: {os.path.basename(key)}")
            
            # If no reports found by filename, check JSON metadata (slower but thorough)
            if len(patient_reports) == 0 and (serial or phone):
                print("📥 No filename matches, checking JSON metadata...")
                
                try:
                    import requests
                except ImportError:
                    print("❌ requests module not available, skipping JSON metadata check")
                    return []
                
                # Limit to first 20 reports to prevent timeout
                reports_to_check = all_reports[:20]
                print(f"📥 Checking {len(reports_to_check)} reports for metadata match...")
                
                for report in reports_to_check:
                    try:
                        key = report.get('key', '')
                        if not key.endswith('.pdf'):
                            continue
                        
                        # Check corresponding JSON file
                        json_key = key.replace('.pdf', '.json')
                        
                        url_res = self.cloud_uploader.generate_presigned_url(json_key)
                        if url_res.get('status') != 'success':
                            continue
                        
                        r = requests.get(url_res['url'], timeout=3)
                        if r.status_code == 200:
                            json_data = r.json()
                            
                            # Check if this report belongs to the patient
                            json_serial = json_data.get('machine_serial', '')
                            json_phone = json_data.get('user', {}).get('phone', '')
                            
                            match = False
                            if serial and json_serial and serial == json_serial:
                                match = True
                            elif phone and json_phone and phone == json_phone:
                                match = True
                            
                            if match:
                                patient_reports.append(report)
                                print(f"✅ Found report by JSON metadata: {os.path.basename(key)}")
                    except Exception as e:
                        # Skip reports we can't fetch - don't crash
                        print(f"⚠️ Skipping report {key}: {str(e)[:50]}")
                        continue
            
            # Sort by date (newest first)
            patient_reports.sort(key=lambda x: x.get('last_modified', ''), reverse=True)
            print(f"📊 Total reports found for patient: {len(patient_reports)}")
            return patient_reports
            
        except Exception as e:
            print(f"❌ Error getting patient reports: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def get_latest_patient_metrics(self, serial, phone):
        """Get latest ECG metrics for a patient from their most recent report JSON"""
        try:
            # Get patient's reports
            reports = self.get_patient_reports(serial, phone)
            
            if not reports:
                return None
            
            # Get the most recent report
            latest_report = reports[0]
            report_key = latest_report.get('key', '')
            
            # Look for corresponding JSON file
            if report_key.endswith('.pdf'):
                json_key = report_key.replace('.pdf', '.json')
            else:
                json_key = report_key + '.json'
            
            # Download and parse JSON metrics
            try:
                import requests
                url_res = self.cloud_uploader.generate_presigned_url(json_key)
                if url_res.get('status') == 'success':
                    r = requests.get(url_res['url'], timeout=5)
                    if r.status_code == 200:
                        metrics = r.json()
                        metrics['report_date'] = latest_report.get('last_modified', 'Unknown')
                        return metrics
            except Exception as json_err:
                print(f"Could not load JSON metrics: {json_err}")
                return None
            
            return None
            
        except Exception as e:
            print(f"Error getting patient metrics: {e}")
            return None
    
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


