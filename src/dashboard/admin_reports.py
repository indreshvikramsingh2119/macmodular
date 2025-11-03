import os
from datetime import datetime
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QFileDialog, QFrame
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
        self.setWindowTitle("Admin Reports (S3)")
        self.resize(1100, 680)

        layout = QVBoxLayout(self)
        # App-style header actions
        header = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search filename…")
        self.search_edit.setClearButtonEnabled(True)
        self.refresh_btn = QPushButton("Refresh")
        self.download_btn = QPushButton("Download")
        self.copy_url_btn = QPushButton("Copy Link")
        for b in (self.refresh_btn, self.download_btn, self.copy_url_btn):
            b.setStyleSheet("background:#ff6600;color:#fff;border-radius:10px;padding:6px 14px;")
        header.addWidget(QLabel("Filter:"))
        header.addWidget(self.search_edit, 2)
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

        self.table = QTableWidget(0, 5, self)
        self.table.setHorizontalHeaderLabels(["File", "Type", "Date", "Size (KB)", "S3 Key"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setAlternatingRowColors(True)
        self.table.setWordWrap(False)
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

    def _metric_card(self, title: str, value: str) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet("QFrame{background:#f7f7f7;border-radius:12px;border:2px solid #eee;} QLabel{color:#333}")
        v = QVBoxLayout(frame)
        t = QLabel(title); t.setStyleSheet("font-weight:bold;color:#ff6600")
        val = QLabel(value); val.setStyleSheet("font-size:18px;font-weight:600")
        v.addWidget(t); v.addWidget(val); v.addStretch(1)
        frame._value_label = val
        return frame

    def load_items(self):
        result = self.cloud_uploader.list_reports(prefix="ecg-reports/")
        if result.get('status') != 'success':
            QMessageBox.critical(self, "Error", f"Failed to list reports: {result.get('message')}")
            return
        self._all_items = result.get('items', [])
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
        q = (self.search_edit.text() or '').strip().lower()
        items = getattr(self, '_all_items', [])
        if q:
            items = [it for it in items if q in os.path.basename(it['key']).lower()]
        self._filtered_items = items
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
            self.table.setItem(i, 0, QTableWidgetItem(name))
            self.table.setItem(i, 1, QTableWidgetItem(ftype))
            self.table.setItem(i, 2, QTableWidgetItem(dt))
            self.table.setItem(i, 3, QTableWidgetItem(str(size_kb)))
            self.table.setItem(i, 4, QTableWidgetItem(it['key']))

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


