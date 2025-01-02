#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import sqlite3
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QPushButton, QLabel, 
                           QVBoxLayout, QHBoxLayout, QWidget, QComboBox,
                           QLineEdit, QSpinBox, QTableWidget, QTableWidgetItem,
                           QMessageBox, QGridLayout)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QDoubleValidator

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Investment Tracker")
        self.setMinimumSize(600, 600)
        self.setup_database()
        self.init_ui()

    def setup_database(self):
        self.conn = sqlite3.connect('investments.db')
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS investments (
                id INTEGER PRIMARY KEY,
                date TEXT,
                type TEXT,
                amount REAL
            )
        ''')
        self.conn.commit()
        
    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_widget.setContentsMargins(5, 5, 5, 5)
        
        # Überschrift
        title = QLabel("Investment Tracker", main_widget)
        title.setFont(QFont('Arial', 24))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setGeometry(10, 10, 580, 40)
        
        # Eingabebereich - Absolute Positionierung
        type_label = QLabel("Typ:", main_widget)
        type_label.setFont(QFont('Arial', 10))
        type_label.setGeometry(10, 60, 25, 25)
        
        self.type_combo = QComboBox(main_widget)
        self.type_combo.addItems(["ETF", "Aktien", "Bitcoin", "Sonstige"])
        self.type_combo.setGeometry(37, 60, 100, 25)
        self.type_combo.setFont(QFont('Arial', 10))
        
        amount_label = QLabel("Betrag:", main_widget)
        amount_label.setFont(QFont('Arial', 10))
        amount_label.setGeometry(145, 60, 45, 25)
        
        self.amount_input = QLineEdit(main_widget)
        self.amount_input.setValidator(QDoubleValidator(0.00, 999999999.99, 2))
        self.amount_input.setPlaceholderText("Betrag in €")
        self.amount_input.setGeometry(192, 60, 100, 25)
        self.amount_input.setFont(QFont('Arial', 10))
        
        add_button = QPushButton("Investition hinzufügen", main_widget)
        add_button.clicked.connect(self.add_investment)
        add_button.setGeometry(300, 60, 140, 25)
        add_button.setFont(QFont('Arial', 10))
        add_button.setStyleSheet("""
            QPushButton {
                background-color: #198754;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: #157347;
            }
        """)
        
        # Filter Bereich
        year_label = QLabel("Jahr:", main_widget)
        year_label.setFont(QFont('Arial', 10))
        year_label.setGeometry(10, 95, 30, 25)
        
        self.year_filter = QSpinBox(main_widget)
        current_year = datetime.now().year
        self.year_filter.setRange(2000, current_year)
        self.year_filter.setValue(current_year)
        self.year_filter.setGeometry(42, 95, 70, 25)
        self.year_filter.setFont(QFont('Arial', 10))
        
        month_label = QLabel("Monat:", main_widget)
        month_label.setFont(QFont('Arial', 10))
        month_label.setGeometry(120, 95, 40, 25)
        
        self.month_filter = QSpinBox(main_widget)
        self.month_filter.setRange(1, 12)
        self.month_filter.setValue(datetime.now().month)
        self.month_filter.setGeometry(162, 95, 70, 25)
        self.month_filter.setFont(QFont('Arial', 10))
        
        filter_button = QPushButton("Filtern", main_widget)
        filter_button.clicked.connect(self.update_table)
        filter_button.setGeometry(240, 95, 70, 25)
        filter_button.setFont(QFont('Arial', 10))
        filter_button.setStyleSheet("""
            QPushButton {
                background-color: #0d6efd;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: #0b5ed7;
            }
        """)
        
        # Tabelle
        self.table = QTableWidget(main_widget)
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Datum", "Typ", "Betrag (€)", ""])
        self.table.setGeometry(10, 130, 580, 400)
        self.table.setFont(QFont('Arial', 10))
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        
        # Verbinde Zeilen-Auswahl und Zellenänderung
        self.table.itemSelectionChanged.connect(self.on_selection_change)
        self.table.itemChanged.connect(self.on_item_changed)
        
        # Summen-Labels
        self.monthly_sum_label = QLabel(main_widget)
        self.monthly_sum_label.setFont(QFont('Arial', 12))
        self.monthly_sum_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.monthly_sum_label.setGeometry(10, 540, 580, 20)
        
        self.sum_label = QLabel(main_widget)
        self.sum_label.setFont(QFont('Arial', 14))
        self.sum_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.sum_label.setGeometry(10, 565, 580, 25)
        
        # Initial Update
        self.update_table()
        
    def add_investment(self):
        amount_text = self.amount_input.text().replace(',', '.')
        try:
            amount = float(amount_text)
            investment_type = self.type_combo.currentText()
            date = datetime.now().strftime('%Y-%m-%d')
            
            self.cursor.execute('''
                INSERT INTO investments (date, type, amount)
                VALUES (?, ?, ?)
            ''', (date, investment_type, amount))
            self.conn.commit()
            
            self.amount_input.clear()
            self.update_table()
            QMessageBox.information(self, "Erfolg", "Investition wurde hinzugefügt!")
        except ValueError:
            QMessageBox.warning(self, "Fehler", "Bitte geben Sie einen gültigen Betrag ein!")
    
    def update_table(self):
        # Temporär itemChanged-Signal deaktivieren
        self.table.itemChanged.disconnect(self.on_item_changed)
        
        year = self.year_filter.value()
        month = self.month_filter.value()
        
        # Monatliche Summe berechnen
        self.cursor.execute('''
            SELECT SUM(amount) FROM investments
            WHERE strftime('%Y', date) = ? AND strftime('%m', date) = ?
        ''', (str(year), f"{month:02d}"))
        monthly_total = self.cursor.fetchone()[0] or 0
        self.monthly_sum_label.setText(f"Monatssumme: {monthly_total:.2f} €")
        
        # Einzelne Investitionen anzeigen
        self.cursor.execute('''
            SELECT id, date, type, amount FROM investments
            WHERE strftime('%Y', date) = ? AND strftime('%m', date) = ?
            ORDER BY date DESC
        ''', (str(year), f"{month:02d}"))
        
        investments = self.cursor.fetchall()
        self.table.setRowCount(len(investments))
        
        total = 0
        for row, (id_, date, type_, amount) in enumerate(investments):
            # Speichere ID in allen Spalten
            for col in range(4):
                item = QTableWidgetItem()
                item.setData(Qt.ItemDataRole.UserRole, id_)
                if col == 0:
                    item.setText(date)
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)  # Datum nicht editierbar
                elif col == 1:
                    item.setText(type_)
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)  # Typ nicht editierbar
                elif col == 2:
                    item.setText(f"{amount:.2f}")  # Ohne € Symbol für einfachere Bearbeitung
                elif col == 3:
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)  # Letzte Spalte nicht editierbar
                self.table.setItem(row, col, item)
            
            total += amount
        
        self.sum_label.setText(f"Gesamtsumme: {total:.2f} €")
        self.table.resizeColumnsToContents()
        self.table.setColumnWidth(3, 70)
        
        # itemChanged-Signal wieder aktivieren
        self.table.itemChanged.connect(self.on_item_changed)

    def delete_investment(self, investment_id):
        reply = QMessageBox.question(
            self,
            'Investition löschen',
            'Möchten Sie diese Investition wirklich löschen?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.cursor.execute('DELETE FROM investments WHERE id = ?', (investment_id,))
            self.conn.commit()
            self.update_table()
            QMessageBox.information(self, "Erfolg", "Investition wurde gelöscht!")

    def on_selection_change(self):
        # Entferne zuerst alle alten Löschen-Buttons
        for row in range(self.table.rowCount()):
            if self.table.cellWidget(row, 3) is not None:
                self.table.removeCellWidget(row, 3)
                self.table.setItem(row, 3, QTableWidgetItem(""))

        # Füge den Löschen-Button nur in der ausgewählten Zeile hinzu
        current_row = self.table.currentRow()
        if current_row >= 0:
            delete_button = QPushButton("Löschen")
            delete_button.setStyleSheet("""
                QPushButton {
                    background-color: #dc3545;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    padding: 3px;
                    font-size: 10px;
                }
                QPushButton:hover {
                    background-color: #bb2d3b;
                }
            """)
            # Hole ID aus einer beliebigen Spalte (hier erste Spalte)
            investment_id = self.table.item(current_row, 0).data(Qt.ItemDataRole.UserRole)
            delete_button.clicked.connect(lambda checked, id_=investment_id: self.delete_investment(id_))
            self.table.setCellWidget(current_row, 3, delete_button)

    def on_item_changed(self, item):
        if item.column() == 2:  # Betrag-Spalte
            try:
                # Versuche den neuen Betrag zu parsen
                new_amount = float(item.text().replace(',', '.').replace('€', '').strip())
                
                # Aktualisiere Datenbank
                investment_id = item.data(Qt.ItemDataRole.UserRole)
                self.cursor.execute('UPDATE investments SET amount = ? WHERE id = ?', 
                                  (new_amount, investment_id))
                self.conn.commit()
                
                # Aktualisiere die Anzeige
                self.update_table()
            except ValueError:
                QMessageBox.warning(self, "Fehler", "Bitte geben Sie einen gültigen Betrag ein!")
                self.update_table()  # Stelle den alten Wert wieder her

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 