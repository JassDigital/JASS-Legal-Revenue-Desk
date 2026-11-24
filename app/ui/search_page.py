from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QLabel, QHeaderView
)
from PySide6.QtCore import Qt
from app.services.search_service import SearchService

class SearchPage(QWidget):
    def __init__(self, conn):
        super().__init__()
        self.search_service = SearchService(conn)
        layout = QVBoxLayout(self)
        heading = QLabel("Global Legal Search")
        heading.setObjectName("pageTitle")
        layout.addWidget(heading)
        hint = QLabel("Search indexed legislation, sections, judgments, documents and research notes.")
        hint.setObjectName("muted")
        layout.addWidget(hint)

        row = QHBoxLayout()
        self.query = QLineEdit()
        self.query.setPlaceholderText('Enter a phrase, e.g. mutation, partition, co-sharer')
        self.query.returnPressed.connect(self.run_search)
        row.addWidget(self.query, 1)
        button = QPushButton("Search")
        button.clicked.connect(self.run_search)
        row.addWidget(button)
        layout.addLayout(row)

        self.status = QLabel("Search uses only material imported into your local library.")
        self.status.setObjectName("muted")
        layout.addWidget(self.status)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Type", "Title", "Details", "Matching passage"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.setWordWrap(True)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table, 1)

    def run_search(self):
        query = self.query.text().strip()
        results = self.search_service.search(query)
        self.table.setRowCount(len(results))
        for row_index, result in enumerate(results):
            values = [result["kind"], result["title"], result["detail"], result["excerpt"]]
            for col, value in enumerate(values):
                item = QTableWidgetItem(str(value or ""))
                item.setToolTip(str(value or ""))
                self.table.setItem(row_index, col, item)
        self.status.setText(f"{len(results)} result(s). Only locally indexed material is searched.")
