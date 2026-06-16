import sys
from PyQt6.QtWidgets import QApplication
import qdarktheme

from src.ui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    
    # Apply dark theme
    app.setStyleSheet(qdarktheme.load_stylesheet())
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
