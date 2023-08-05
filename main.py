import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QTabWidget, QLabel, QPushButton, \
    QFileDialog, QComboBox
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas


def read_soft_file(file_path):
    # Identify the start of the data table
    with open(file_path, 'r') as f:
        lines = f.readlines()
        start_line = 0
        for i, line in enumerate(lines):
            if line.startswith('!dataset_table_begin'):
                start_line = i + 1
                break

    # Read the data table into a pandas DataFrame
    data = pd.read_csv(file_path, sep='\t', skiprows=start_line)

    return data


class DataAnalysisWidget(QWidget):
    def __init__(self, data):
        super().__init__()
        self.data = data
        self.layout = QVBoxLayout()
        self.layout.setAlignment(Qt.AlignTop)
        self.setLayout(self.layout)
        self.create_and_add_widgets()
        # Adding the dropdown for column selection
        self.column_dropdown = QComboBox()
        self.column_dropdown.addItems(list(self.data.columns))
        self.column_dropdown.currentIndexChanged.connect(self.update_visualization)
        self.layout.addWidget(self.column_dropdown)
        self.column_dropdown = QComboBox()
        self.layout.addWidget(self.column_dropdown)


    def populate_dropdown(self):
        # Clear existing items
        self.column_dropdown.clear()
        # Add new items
        self.column_dropdown.addItems(list(self.data.columns))

    def create_and_add_widgets(self):
        for column in self.data.columns:
            if self.data[column].dtype in [np.float64, np.int64]:
                # Compute basic statistics for numerical columns
                num_values = len(self.data[column])
                mean_value = np.mean(self.data[column])
                median_value = np.median(self.data[column])
                max_value = np.max(self.data[column])
                min_value = np.min(self.data[column])

                # Create labels to display the analysis results
                num_values_label = QLabel(f"Number of values in '{column}': {num_values}")
                mean_value_label = QLabel(f"Mean value of '{column}': {mean_value:.2f}")
                median_value_label = QLabel(f"Median value of '{column}': {median_value:.2f}")
                max_value_label = QLabel(f"Max value of '{column}': {max_value}")
                min_value_label = QLabel(f"Min value of '{column}': {min_value}")

                # Add labels to the layout
                self.layout.addWidget(num_values_label)
                self.layout.addWidget(mean_value_label)
                self.layout.addWidget(median_value_label)
                self.layout.addWidget(max_value_label)
                self.layout.addWidget(min_value_label)
            else:
                # Count unique values for categorical columns
                unique_counts = self.data[column].value_counts()
                for value, count in unique_counts.items():  # Use items() instead of iteritems()
                    count_label = QLabel(f"Count of '{value}' in '{column}': {count}")
                    self.layout.addWidget(count_label)

    def update(self):
        # Clear the current layout first
        while self.layout.count():
            child = self.layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Then call the code that creates and adds new widgets to the layout
        self.create_and_add_widgets()

    def update_visualization(self, index):
        selected_column = self.column_dropdown.itemText(index)
        # Code to update the visualization based on the selected column
        # For example, if you are using a matplotlib plot:
        plt.plot(self.data[selected_column])
        plt.show()


class VisualizationWidget(QWidget):
    def __init__(self, data):
        super().__init__()
        self.data = data
        self.layout = QVBoxLayout()
        self.layout.setAlignment(Qt.AlignTop)
        self.figure = plt.figure(figsize=(8, 6))
        self.canvas = FigureCanvas(self.figure)
        self.layout.addWidget(self.canvas)
        self.setLayout(self.layout)
        self.create_and_draw_plots()

    def create_and_draw_plots(self):
        for i, column in enumerate(self.data.columns):
            ax = self.figure.add_subplot(len(self.data.columns), 1, i + 1)
            if self.data[column].dtype in [np.float64, np.int64]:  # Update the dtype check
                # Generate histogram for numerical columns
                ax.hist(self.data[column], bins=10, edgecolor='black')
                ax.set_xlabel(column)
                ax.set_ylabel('Frequency')
                ax.set_title(f'Distribution of {column}')
            else:
                # Generate bar plot for categorical columns
                self.data[column].value_counts().plot(kind='bar', ax=ax)
                ax.set_xlabel(column)
                ax.set_ylabel('Count')
                ax.set_title(f'Counts of {column}')

    def visualize_selected_column(self, column_name):
        self.figure.clear()
        ax = self.figure.add_subplot(1, 1, 1)
        ax.plot(self.data[column_name])  # Or any other plot you want for the selected column
        self.canvas.draw()

    def update(self):
        # Clear the current figure first
        self.figure.clear()

        # Then call the code that creates new plots and draws them on the canvas
        self.create_and_draw_plots()

        # Finally, redraw the canvas
        self.canvas.draw()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('Medical Research Data Analysis')
        self.setGeometry(100, 100, 800, 600)

        self.tabs = QTabWidget()

        # Create the data analysis and visualization widgets
        self.data_analysis_widget = DataAnalysisWidget(pd.DataFrame())
        self.visualization_widget = VisualizationWidget(pd.DataFrame())

        # Add the widgets to the tabs
        self.tabs.addTab(self.data_analysis_widget, 'Data Analysis')
        self.tabs.addTab(self.visualization_widget, 'Visualization')

        self.setCentralWidget(self.tabs)

        self.open_button = QPushButton('Open File')
        self.open_button.clicked.connect(self.open_file)

        # Add a label to show the selected file
        self.file_label = QLabel("No file selected.")

        # Add a start button
        self.start_button = QPushButton('Start Analysis')
        self.start_button.clicked.connect(self.start_analysis)
        self.start_button.setDisabled(True)  # Disable the button until a file is selected

        self.statusBar().addWidget(self.open_button)
        self.statusBar().addWidget(self.file_label)
        self.statusBar().addWidget(self.start_button)

        # Create the data analysis and visualization widgets
        self.data_analysis_widget = DataAnalysisWidget(pd.DataFrame())
        self.visualization_widget = VisualizationWidget(pd.DataFrame())

        # Connect the dropdown selection to update the visualization
        self.data_analysis_widget.column_dropdown.currentIndexChanged.connect(
            lambda index: self.visualization_widget.visualize_selected_column(
                self.data_analysis_widget.column_dropdown.itemText(index)
            )
        )

    def open_file(self):
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(self, 'Open File', '',
                                                   'All Files (*);;CSV Files (*.csv);;Excel Files (*.xlsx);;SOFT Files (*.soft)')

        if file_path:
            # Read the file into a Pandas DataFrame
            if file_path.endswith('.csv'):
                data = pd.read_csv(file_path)
            elif file_path.endswith('.xlsx'):
                data = pd.read_excel(file_path)
            elif file_path.endswith('.soft'):
                data = read_soft_file(file_path)

            # Update the file label
            self.file_label.setText(f"Selected file: {file_path}")

            # Enable the start button
            self.start_button.setEnabled(True)

            # Update the data in both widgets
            self.data_analysis_widget.data = data
            self.visualization_widget.data = data

            # Populate the dropdown with the new columns
            self.data_analysis_widget.populate_dropdown()

    def start_analysis(self):
        self.data_analysis_widget.data = self.data
        self.data_analysis_widget.update()

        self.visualization_widget.data = self.data
        self.visualization_widget.update()


if __name__ == '__main__':
    # Create the application and main window
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()

    # Start the application event loop
    sys.exit(app.exec_())
