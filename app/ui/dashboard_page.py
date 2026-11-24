from PySide6.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QLabel, QFrame

class DashboardPage(QWidget):
    def __init__(self, conn):
        super().__init__()
        layout = QVBoxLayout(self)
        title = QLabel("Research Dashboard")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        intro = QLabel("Your offline-first legal and revenue research workspace.")
        intro.setObjectName("muted")
        layout.addWidget(intro)

        grid = QGridLayout()
        counts = [
            ("Acts & instruments", "SELECT COUNT(*) FROM legislation"),
            ("Sections", "SELECT COUNT(*) FROM sections"),
            ("Judgments", "SELECT COUNT(*) FROM judgments"),
            ("Documents", "SELECT COUNT(*) FROM documents"),
            ("My legal cases", "SELECT COUNT(*) FROM legal_cases"),
            ("Research notes", "SELECT COUNT(*) FROM research_notes"),
        ]
        for index, (label, sql) in enumerate(counts):
            count = conn.execute(sql).fetchone()[0]
            card = QFrame()
            card.setObjectName("metricCard")
            card_layout = QVBoxLayout(card)
            value = QLabel(str(count))
            value.setObjectName("metricValue")
            name = QLabel(label)
            name.setObjectName("muted")
            card_layout.addWidget(value)
            card_layout.addWidget(name)
            grid.addWidget(card, index // 3, index % 3)
        layout.addLayout(grid)

        note = QLabel(
            "Data integrity reminder: demonstration records are synthetic. "
            "Import and verify official source documents before relying on legal material."
        )
        note.setWordWrap(True)
        note.setObjectName("notice")
        layout.addWidget(note)
        layout.addStretch(1)
