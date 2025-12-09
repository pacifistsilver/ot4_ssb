import sys
import json
from dataclasses import dataclass, asdict
from typing import List, Optional
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QFormLayout, 
                               QLineEdit, QDoubleSpinBox, QPushButton, QTableWidget, 
                               QTableWidgetItem, QHeaderView, QGroupBox, QTextEdit, 
                               QMessageBox, QFileDialog, QTabWidget, QCheckBox)
from PySide6.QtCore import Qt
import os

## CONSTANTS
COL_CONC = 0
COL_STOCK = 1
COL_DILUENT = 2

## WellData objects
@dataclass
class WellData:
    final_conc_uM: float
    stock_vol_uL: float
    diluent_vol_uL: float

## dilutions calculator function
def calculate_dilutions(stock_conc_uM: float, total_vol_uL: float, targets_uM: List[float]) -> List[WellData]:
    """
    returns a list of WellData objects
    """
    results = []
    for target in targets_uM:
        # C1V1 = C2V2  =>  V1 = (C2 * V2) / C1
        if stock_conc_uM == 0:
            stock_vol = 0.0
        else:
            stock_vol = (target * total_vol_uL) / stock_conc_uM
            
        diluent_vol = total_vol_uL - stock_vol
        
        # create WellData object
        well = WellData(
            final_conc_uM=target,
            stock_vol_uL=stock_vol,
            diluent_vol_uL=diluent_vol
        )
        results.append(well)
    return results

## UI LAYER
class DilutionApp(QWidget):
    def __init__(self):
        super().__init__()
        # window title
        self.setWindowTitle("Generate Dose-Response Opentrons Config")
        
        # store calculated data here. The Table and JSON view just reflect this.
        self.experiment_data: List[WellData] = []
        
        # main layout
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)
        
        # tab layout
        self.tabs = QTabWidget()
        self.main_layout.addWidget(self.tabs)
        
        self.tab_setup = QWidget()
        self.tab_table = QWidget()
        self.tab_json = QWidget()        
        
        self.tabs.addTab(self.tab_setup, "Input Parameters")
        self.tabs.addTab(self.tab_table, "Table Preview")
        self.tabs.addTab(self.tab_json, "JSON Output")        
        
        self.create_setup_tab()
        self.create_table_tab()
        self.create_json_tab()
        
        # populate with default data
        self.set_defaults()

    ## input setup
    def create_setup_tab(self):
        # setup tab layout
        layout = QVBoxLayout()
        # parameter input layout
        group_box = QGroupBox("Define Experiment Variables")
        form_layout = QFormLayout()

        # helper to reduce repetition
        def add_input(label: str, widget: QWidget, suffix: Optional[str] = None) -> QWidget:
            if suffix and isinstance(widget, QDoubleSpinBox):
                widget.setSuffix(suffix)
            form_layout.addRow(label, widget)
            return widget

        ## inputs
        # input stock name
        self.input_stock_name = add_input("Stock Name:", QLineEdit())
        self.input_stock_name.setPlaceholderText("e.g., Stock Solution") # type: ignore

        # input stock concentration
        self.input_stock_conc = add_input("Stock Concentration (μM):", QDoubleSpinBox(), " μM")
        self.input_stock_conc.setRange(0, 10000) # type: ignore
        self.input_stock_conc.setDecimals(2) # type: ignore
        
        # pipette rate settings
        self.input_asp_rate = add_input("Aspirate Rate (μL/s):", QDoubleSpinBox(), " μL")
        self.input_asp_rate.setRange(0, 10000) # type: ignore
        self.input_asp_rate.setDecimals(2) # type: ignore
        self.input_disp_rate = add_input("Dispense Rate (μL/s):", QDoubleSpinBox(), " μL")
        self.input_disp_rate.setRange(0, 10000) # type: ignore
        self.input_disp_rate.setDecimals(2) # type: ignore
        self.input_blowout_rate = add_input("Blowout Rate (μL/s):", QDoubleSpinBox(), " μL")
        self.input_blowout_rate.setRange(0, 10000) # type: ignore
        self.input_blowout_rate.setDecimals(2) # type: ignore
                
        # viscous liquid check
        self.input_viscous_liquid = add_input("Is Viscous Liquid?", QCheckBox(), " μL")
        self.input_viscous_liquid.stateChanged.connect(self.onStateChanged)
        self.viscous_bool: bool = False

        # input diluent name
        self.input_diluent_name = add_input("Diluent Name:", QLineEdit())
        self.input_diluent_name.setPlaceholderText("e.g., Buffer") # type: ignore

        # input total well volume
        self.input_total_vol = add_input("Total Destination Plate Well Volume (μL):", QDoubleSpinBox(), " μL")
        self.input_total_vol.setRange(0, 10000) # type: ignore

        # input target concentrations (must be a comma-separated list in uM)
        self.input_targets = add_input("Target Concentrations (μM):", QLineEdit())
        self.input_targets.setPlaceholderText("e.g., 0, 5, 10, 50, 100") # type: ignore
        self.input_targets.setToolTip("Enter comma-separated values in μM") # type: ignore
        
        # input the number of replicates
        self.replicates = add_input("Number of Replicates:", QDoubleSpinBox())
        self.replicates.setRange(0, 3) # type: ignore
        self.replicates.setDecimals(0) # type: ignore
        
        # layout of above experimental parameters in group
        group_box.setLayout(form_layout)
        layout.addWidget(group_box)
        
        # calculate dilutions
        self.btn_calculate = QPushButton("Calculate")
        self.btn_calculate.clicked.connect(self.run_calculation)
        layout.addWidget(self.btn_calculate)
        
        layout.addStretch()
        self.tab_setup.setLayout(layout)
        

    ## file dialog handler
    def onStateChanged(self):
        if self.input_viscous_liquid.isChecked():
            self.input_viscous_liquid.setText("Viscous")
            self.viscous_bool = True
        else:
            self.input_viscous_liquid.setText("Not Viscous")
            self.viscous_bool = False

    
    ## table setup
    def create_table_tab(self):
        layout = QVBoxLayout()
        
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Final Conc (μM)", "Stock Vol (μL)", "Diluent Vol (μL)"])
        self.table.setAlternatingRowColors(True)
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        
        layout.addWidget(self.table)        
        self.tab_table.setLayout(layout)

    ## json setup
    def create_json_tab(self):
        layout = QVBoxLayout()
        
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setStyleSheet("background-color: #f8f8f8; font-family: monospace;")
        
        self.btn_generate_json = QPushButton("Generate JSON")
        self.btn_generate_json.setFixedHeight(40)
        self.btn_generate_json.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        self.btn_generate_json.clicked.connect(self.generate_json)

        layout.addWidget(self.btn_generate_json)
        layout.addWidget(self.output_text)
        self.tab_json.setLayout(layout)

    ## handle defaults
    def set_defaults(self):
        self.input_stock_name.setText("Stock Solution") # type: ignore
        self.input_diluent_name.setText("Buffer") # type: ignore
        self.input_stock_conc.setValue(15) # type: ignore
        self.input_total_vol.setValue(100.0) # type: ignore
        self.input_asp_rate.setValue(50)
        self.input_blowout_rate.setValue(150)
        self.input_disp_rate.setValue(150)
        self.input_targets.setText("0, 2, 4, 6, 8, 10, 12, 14") # type: ignore
        self.replicates.setValue(1) # type: ignore

    ## calls function calculate dilutions to populate ui
    def run_calculation(self):
        """
        Orchestrator: 
        1. Gets inputs from UI
        2. Calls logic function
        3. Updates Data Model
        4. Updates UI
        """
        try:
            # first we get inputs from the user
            stock_conc = self.input_stock_conc.value() # type: ignore
            total_vol = self.input_total_vol.value() # type: ignore
            raw_targets = self.input_targets.text().split(',') # type: ignore
            targets = [float(x.strip()) for x in raw_targets if x.strip()] 

            # input validation
            if stock_conc <= 0:
                QMessageBox.warning(self, "Error", "Stock concentration must be greater than 0.")
                return

            # call calculate dilutions and obtain a welldata object
            new_data = calculate_dilutions(stock_conc, total_vol, targets)
            
            # update data model
            self.experiment_data = new_data

            # update ui
            self.refresh_table()
            
            # switch tabs
            self.tabs.setCurrentIndex(1)

        except ValueError:
            QMessageBox.critical(self, "Error", "Invalid input in Target Concentrations. Please use numbers separated by commas.")

    ## referesh table with input data
    def refresh_table(self):
        """Updates the table based entirely on self.experiment_data."""
        self.table.setRowCount(len(self.experiment_data))
        
        for row_idx, well in enumerate(self.experiment_data):
            # check for warnings (logic inside UI update is okay for visual alerts)
            if well.stock_vol_uL > self.input_total_vol.value(): # type: ignore
                QMessageBox.warning(self, "Warning", f"Target {well.final_conc_uM} requires more stock than total volume!")

            # table item helper
            def make_item(val: float) -> QTableWidgetItem:
                item = QTableWidgetItem()
                item.setData(Qt.EditRole, round(val, 3))
                return item

            self.table.setItem(row_idx, COL_CONC, make_item(well.final_conc_uM))
            self.table.setItem(row_idx, COL_STOCK, make_item(well.stock_vol_uL))
            self.table.setItem(row_idx, COL_DILUENT, make_item(well.diluent_vol_uL))

    ## generate json with class data
    def generate_json(self):
        """Builds JSON from the Data Model, NOT the Table."""
        #
        if not self.experiment_data:
            QMessageBox.warning(self, "Warning", "No data to export. Please calculate first.")
            return

        # build structure
        data = {
            "stock_name": self.input_stock_name.text(), # type: ignore

            "stock_conc_uM": self.input_stock_conc.value(), # type: ignore
            "diluent_name": self.input_diluent_name.text(), # type: ignore
            "total_vol_uL": self.input_total_vol.value(), # type: ignore
            "replicates": int(self.replicates.value()), # type: ignore
            "viscous_check": self.viscous_bool,
            "asp_rate": self.input_asp_rate.value(),
            "disp_rate": self.input_disp_rate.value(),
            "blowout_rate": self.input_blowout_rate.value(),

            # converts dataclasses to list of dicts or separate arrays
            "wells": [asdict(well) for well in self.experiment_data],
            "final_conc_uM": [w.final_conc_uM for w in self.experiment_data],
            "stock_vol_uL": [w.stock_vol_uL for w in self.experiment_data],
            "diluent_vol_uL": [w.diluent_vol_uL for w in self.experiment_data]
            
        }

        # dump data json to ui and file  
        try:
            json_output = json.dumps(data, indent=4)
            self.output_text.setText(json_output)
            
            with open('dilution_config.json', 'w') as f:
                f.write(json_output)
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save JSON: {str(e)}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    window = DilutionApp()
    window.show()
    
    # app.exec is now preferred over sys.ext
    app.exec()