import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QTabWidget, QLabel, QPushButton, \
    QFileDialog, QComboBox
from PyQt6.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from Bio import Entrez, SeqIO
from Bio.SeqUtils import GC
from mpl_toolkits.mplot3d import Axes3D  # This is required for 3D plotting


def read_soft_file(file_path):
    with open(file_path, 'r') as f:
        lines = f.readlines()
        start_line = 0
        for i, line in enumerate(lines):
            if line.startswith('!dataset_table_begin'):
                start_line = i + 1
                break

    data = pd.read_csv(file_path, sep='\t', skiprows=start_line)

    return data

def fetch_sequence(id, db="nucleotide"):
    Entrez.email = "your_email@example.com"
    handle = Entrez.efetch(db=db, id=id, rettype="gb", retmode="text")
    record = SeqIO.read(handle, "genbank")
    handle.close()
    return record.seq

def analyze_sequence(seq):
    length = len(seq)
    gc_content = GC(seq)
    return length, gc_content

class DataAnalysisWidget(QWidget):
    def __init__(self, data):
        super().__init__()
        self.data = data
        self.column_selector = QComboBox()
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.column_selector)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setLayout(self.layout)
        self.column_selector.currentIndexChanged.connect(self.update)
        self.create_and_add_widgets()

    def create_and_add_widgets(self):
        self.column_selector.clear()
        if not self.data.empty:
            self.column_selector.addItems(self.data.columns)

    def update(self):
        column = self.column_selector.currentText()
        if column and column in self.data:
            # Clear the current layout first
            while self.layout.count() > 1:
                child = self.layout.takeAt(1)
                if child.widget():
                    child.widget().deleteLater()

            # Numeric columns
            if self.data[column].dtype in [np.float64, np.int64]:
                num_values = len(self.data[column])
                mean_value = np.mean(self.data[column])
                median_value = np.median(self.data[column])
                max_value = np.max(self.data[column])
                min_value = np.min(self.data[column])

                num_values_label = QLabel(f"Number of values in '{column}': {num_values}")
                mean_value_label = QLabel(f"Mean value of '{column}': {mean_value:.2f}")
                median_value_label = QLabel(f"Median value of '{column}': {median_value:.2f}")
                max_value_label = QLabel(f"Max value of '{column}': {max_value}")
                min_value_label = QLabel(f"Min value of '{column}': {min_value}")

                self.layout.addWidget(num_values_label)
                self.layout.addWidget(mean_value_label)
                self.layout.addWidget(median_value_label)
                self.layout.addWidget(max_value_label)
                self.layout.addWidget(min_value_label)

            # Check if the selected column contains gene/protein identifiers
            elif column == "Your_Gene_or_Protein_Column_Name":
                # Fetch the sequence for the first ID as an example
                sequence = fetch_sequence(self.data[column].iloc[0])
                length, gc_content = analyze_sequence(sequence)
                length_label = QLabel(f"Length of sequence: {length}")
                gc_content_label = QLabel(f"GC content of sequence: {gc_content:.2f}%")
                self.layout.addWidget(length_label)
                self.layout.addWidget(gc_content_label)

            # Categorical columns
            else:
                unique_counts = self.data[column].value_counts()
                for value, count in unique_counts.items():
                    count_label = QLabel(f"Count of '{value}' in '{column}': {count}")
                    self.layout.addWidget(count_label)

class VisualizationWidget(QWidget):
    def __init__(self, data):
        super().__init__()
        self.data = data
        self.column_selector = QComboBox()
        self.plot_type_selector = QComboBox() # Added dropdown for plot types
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.column_selector)
        self.layout.addWidget(self.plot_type_selector) # Added plot type selector to layout
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.figure = plt.figure(figsize=(8, 6))
        self.canvas = FigureCanvas(self.figure)
        self.layout.addWidget(self.canvas)
        self.setLayout(self.layout)
        self.column_selector.currentIndexChanged.connect(self.update)
        self.plot_type_selector.currentIndexChanged.connect(self.update) # Connect plot type changes to update
        self.create_and_draw_plots()

    def create_and_draw_plots(self):
        self.column_selector.clear()
        self.column_selector.addItems(self.data.columns)
        self.plot_type_selector.clear()
        self.plot_type_selector.addItems(
            ["Histogram", "Line Plot", "Scatter Plot", "3D Surface Plot"])  # Added "3D Surface Plot"

    def update(self):
        column = self.column_selector.currentText()
        plot_type = self.plot_type_selector.currentText()
        if column and column in self.data:
            self.figure.clear()

            ax = self.figure.add_subplot(111)
            if self.data[column].dtype in [np.float64, np.int64]:
                if plot_type == "Histogram":
                    ax.hist(self.data[column], bins=10, edgecolor='black')
                elif plot_type == "Line Plot":
                    ax.plot(self.data[column])
                elif plot_type == "Scatter Plot":
                    ax.scatter(range(len(self.data[column])), self.data[column])
                elif plot_type == "3D Surface Plot":  # New case for 3D Surface Plot
                    ax = self.figure.add_subplot(111, projection='3d')
                    X = np.linspace(min(self.data[column]), max(self.data[column]), 30)
                    Y = np.linspace(min(self.data[column]), max(self.data[column]), 30)
                    X, Y = np.meshgrid(X, Y)
                    Z = np.sin(np.sqrt(X ** 2 + Y ** 2))
                    ax.plot_surface(X, Y, Z, cmap='viridis')
                ax.set_xlabel(column)
                ax.set_ylabel('Frequency' if plot_type == "Histogram" else 'Value')
                ax.set_title(f'{plot_type} of {column}')
            else:
                self.data[column].value_counts().plot(kind='bar', ax=ax)
                ax.set_xlabel(column)
                ax.set_ylabel('Count')
                ax.set_title(f'Counts of {column}')

            self.canvas.draw()

class ComparisonWidget(QWidget):
    def __init__(self, data):
        super().__init__()
        self.data = data
        self.column_selector1 = QComboBox()
        self.column_selector2 = QComboBox()
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.column_selector1)
        self.layout.addWidget(self.column_selector2)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.figure = plt.figure(figsize=(8, 6))
        self.canvas = FigureCanvas(self.figure)
        self.layout.addWidget(self.canvas)
        self.setLayout(self.layout)
        self.column_selector1.currentIndexChanged.connect(self.update)
        self.column_selector2.currentIndexChanged.connect(self.update)
        self.create_and_draw_plots()

    def create_and_draw_plots(self):
        self.column_selector1.clear()
        self.column_selector2.clear()
        if not self.data.empty:
            self.column_selector1.addItems(self.data.columns)
            self.column_selector2.addItems(self.data.columns)

    def update(self):
        column1 = self.column_selector1.currentText()
        column2 = self.column_selector2.currentText()
        if column1 and column2 and column1 in self.data and column2 in self.data:
            self.figure.clear()

            ax = self.figure.add_subplot(111)
            if self.data[column1].dtype in [np.float64, np.int64] and self.data[column2].dtype in [np.float64,
                                                                                                   np.int64]:
                ax.scatter(self.data[column1], self.data[column2])
                ax.set_xlabel(column1)
                ax.set_ylabel(column2)
                ax.set_title(f'{column1} vs {column2}')

            self.canvas.draw_idle()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('Medical Research Data Analysis')
        self.setGeometry(100, 100, 800, 600)

        self.tabs = QTabWidget()

        self.data_analysis_widget = DataAnalysisWidget(pd.DataFrame())
        self.visualization_widget = VisualizationWidget(pd.DataFrame())
        self.comparison_widget = ComparisonWidget(pd.DataFrame())  # Add this line

        self.tabs.addTab(self.data_analysis_widget, 'Data Analysis')
        self.tabs.addTab(self.visualization_widget, 'Visualization')
        self.tabs.addTab(self.comparison_widget, 'Comparison')  # Add this line

        self.setCentralWidget(self.tabs)

        self.open_button = QPushButton('Open File')
        self.open_button.clicked.connect(self.open_file)

        self.file_label = QLabel("No file selected.")

        self.start_button = QPushButton('Start Analysis')
        self.start_button.clicked.connect(self.start_analysis)
        self.start_button.setDisabled(True)

        self.statusBar().addWidget(self.open_button)
        self.statusBar().addWidget(self.file_label)
        self.statusBar().addWidget(self.start_button)

    def open_file(self):
        try:
            file_dialog = QFileDialog()
            file_path, _ = file_dialog.getOpenFileName(self, 'Open File', '',
                                                       'All Files (*);;CSV Files (*.csv);;Excel Files (*.xlsx);;SOFT Files (*.soft)')

            if file_path:
                self.file_label.setText(f"Selected file: {file_path}")

                self.start_button.setEnabled(True)

                if file_path.endswith('.csv'):
                    self.data = pd.read_csv(file_path)
                elif file_path.endswith('.xlsx'):
                    self.data = pd.read_excel(file_path)
                elif file_path.endswith('.soft'):
                    self.data = read_soft_file(file_path)

                # Add data validation here

        except Exception as e:
            self.file_label.setText(f"Error loading file: {str(e)}")

    # Inside the create_and_draw_plots method of VisualizationWidget class:

    def create_and_draw_plots(self):
        try:
            self.column_selector.clear()
            self.column_selector.addItems(self.data.columns)
            self.plot_type_selector.clear()
            self.plot_type_selector.addItems(["Histogram", "Line Plot", "Scatter Plot"])  # Added plot types

        except Exception as e:
            print(f"Error creating and drawing plots: {str(e)}")

    # Inside the update method of VisualizationWidget class:

    def update(self):
        try:
            column = self.column_selector.currentText()
            plot_type = self.plot_type_selector.currentText()  # Get selected plot type
            if column and column in self.data:
                self.figure.clear()

                ax = self.figure.add_subplot(111)
                if self.data[column].dtype in [np.float64, np.int64]:
                    if plot_type == "Histogram":
                        ax.hist(self.data[column], bins=10, edgecolor='black')
                    elif plot_type == "Line Plot":
                        ax.plot(self.data[column])
                    elif plot_type == "Scatter Plot":
                        ax.scatter(range(len(self.data[column])), self.data[column])
                    ax.set_xlabel(column)
                    ax.set_ylabel('Frequency' if plot_type == "Histogram" else 'Value')
                    ax.set_title(f'{plot_type} of {column}')
                else:
                    # Handle categorical data
                    self.data[column].value_counts().plot(kind='bar', ax=ax)
                    ax.set_xlabel(column)
                    ax.set_ylabel('Count')
                    ax.set_title(f'Counts of {column}')

                self.canvas.draw()

        except Exception as e:
            print(f"Error updating plots: {str(e)}")

    def start_analysis(self):
        self.data_analysis_widget.data = self.data
        self.data_analysis_widget.create_and_add_widgets()
        self.data_analysis_widget.update()
        self.visualization_widget.data = self.data
        self.visualization_widget.create_and_draw_plots()
        self.visualization_widget.update()
        self.comparison_widget.data = self.data
        self.comparison_widget.create_and_draw_plots()
        self.comparison_widget.update()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()

    sys.exit(app.exec())
