import sys
import threading  # Import threading to run AI in the background

# Import necessary PyQt6 modules
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QGridLayout, QLineEdit, QPushButton, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, pyqtSignal, QObject
from PyQt6.QtGui import QFont, QIcon, QFontDatabase, QColor

# We will import our calculator 'brain' and 'ai'
import calculator_core
import ai_services  # <-- IMPORTED OUR NEW AI FILE

# --- Global App Styling (QSS for our calculator) ---
# This QSS is now VALID and contains the critical selector fix.
APP_STYLES = """
/* Global styling for the main window */
QWidget#MainWindow {
    background-color: #0A0A0A; /* background-dark */
    border-radius: 40px; /* rounded-2.5rem */
}

/* Styling for the two calculator displays */
QLineEdit {
    background-color: transparent; /* Transparent background */
    border: none; /* No border */
    color: #F5F5F7; /* text-light -- TYPO FIX (T7 -> F7) */
    font-family: 'Sora', sans-serif; /* Ensure Sora is used if available */
    qproperty-alignment: 'AlignRight'; /* Align text to the right */
    padding-right: 10px; /* Small padding for display text */
}

QLineEdit#ExpressionDisplay {
    color: rgba(245, 245, 247, 0.6); /* text-text-light/60 */
    font-size: 24px;
    font-weight: 400;
}

QLineEdit#ResultDisplay {
    font-size: 64px; /* text-6xl */
    font-weight: 700; /* font-bold */
}

/* Styling for all buttons (QPushButton) */
QPushButton {
    border: none;
    border-radius: 16px; /* rounded-2xl */
    font-family: 'Sora', sans-serif; /* Default font for buttons */
    font-size: 20px; /* text-xl */
    font-weight: 600; /* font-semibold */
    color: #FFFFFF;
    min-height: 64px; /* h-16 */
}

/* --- :pressed and :hover states for each button type --- */

/* Number Buttons (0-9, .) */
QPushButton[class="number"] {
    background-color: #2A2D37; /* button-dark */
}
QPushButton[class="number"]:hover {
    background-color: #3a3e4c; /* Darker hover */
}
QPushButton[class="number"]:pressed {
    background-color: #20232b; /* Darker pressed */
}

/* Function Buttons (sin, cos, AC, etc.) */
QPushButton[class="function"] {
    background-color: #4C505F; /* button-medium */
}
/* --- TYPO FIX HERE: Removed extra colon --- */
QPushButton[class="function"]:hover {
    background-color: #5c6070; /* Darker hover */
}
QPushButton[class="function"]:pressed {
    background-color: #3c404d; /* Darker pressed */
}

/* Operator Buttons (+, -, *, /) */
QPushButton[class="operator"] {
    background-color: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: 1,
        stop: 0 #D946EF, stop: 1 #8B5CF6
    );
    font-size: 24px;
    font-weight: 700;
}
QPushButton[class="operator"]:hover {
    background-color: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: 1,
        stop: 0 #E879F9, stop: 1 #A78BFA
    );
}
QPushButton[class="operator"]:pressed {
    background-color: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: 1,
        stop: 0 #C026D3, stop: 1 #7C3AED
    ); /* Darker pressed gradient */
}

/* Equals Button (=) */
QPushButton[class="equals"] {
    background-color: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: 1,
        stop: 0 #34D399, stop: 1 #06B6D4
    );
    font-size: 24px;
    font-weight: 700;
}
QPushButton[class="equals"]:hover {
    background-color: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: 1,
        stop: 0 #6EE7B7, stop: 1 #22D3EE
    );
}
QPushButton[class="equals"]:pressed {
    background-color: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: 1,
        stop: 0 #10B981, stop: 1 #0891B2
    ); /* Darker pressed gradient */
}


/* Mic Button (AI) */
QPushButton#MicButton {
    background-color: #4C505F; /* button-medium */
    font-family: 'Material Symbols Outlined', sans-serif; /* Explicitly use the icon font */
    font-size: 28px; /* Make icon larger */
    font-weight: 400; /* Material symbols generally use regular weight */
    color: #FFFFFF; /* Ensure color is white for icon visibility */
}
QPushButton#MicButton:hover {
    background-color: #5c6070;
}
QPushButton#MicButton:pressed {
    background-color: #3c404d; /* Darker pressed */
}
"""


# --- AI Worker Thread ---
class AiWorker(QObject):
    command_ready = pyqtSignal(str)

    def run(self):
        command = ai_services.listen_for_command()
        parsed_expression = ai_services.parse_command(command)
        self.command_ready.emit(parsed_expression)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("KaCalc")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(390, 800)

        central_widget = QWidget()
        central_widget.setObjectName("MainWindow")
        self.setCentralWidget(central_widget)

        self._load_fonts()
        self.setStyleSheet(APP_STYLES)

        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        display_layout = self._create_display()
        main_layout.addLayout(display_layout)

        separator = QWidget()
        separator.setFixedHeight(1)
        separator.setStyleSheet("background-color: rgba(255, 255, 255, 0.1);")
        main_layout.addWidget(separator)

        buttons_grid_layout = self._create_buttons()
        main_layout.addLayout(buttons_grid_layout)

        main_layout.setContentsMargins(24, 24, 24, 32)
        main_layout.setSpacing(12)

        self.current_expression = ""
        self.last_result_showing = False

        self.ai_thread = None
        self.ai_worker = None

        self.show()

    def _load_fonts(self):
        # --- THE FIX IS HERE: `r"""` ---
        r"""
        To fix font errors, you MUST download the .ttf files and
        place them in your project folder (C:\Users\Lenovo\PycharmProjects\KaCalc\),
        right next to main.py.
        """
        print("Loading fonts...")

        font_id = QFontDatabase.addApplicationFont("Sora-Regular.ttf")
        if font_id == -1:
            print("Error: Sora-Regular.ttf not found or could not be loaded.")
        else:
            print("Sora Regular loaded.")

        font_id = QFontDatabase.addApplicationFont("Sora-Bold.ttf")
        if font_id == -1:
            print("Error: Sora-Bold.ttf not found or could not be loaded.")
        else:
            print("Sora Bold loaded.")

        font_id = QFontDatabase.addApplicationFont("MaterialSymbolsOutlined.ttf")
        if font_id == -1:
            print("Error: MaterialSymbolsOutlined.ttf not found or could not be loaded.")
        else:
            print("Material Symbols font loaded successfully.")

    def _create_display(self) -> QVBoxLayout:
        display_layout = QVBoxLayout()
        display_layout.setSpacing(0)

        self.expression_display = QLineEdit()
        self.expression_display.setObjectName("ExpressionDisplay")
        self.expression_display.setReadOnly(True)

        self.result_display = QLineEdit()
        self.result_display.setObjectName("ResultDisplay")
        self.result_display.setReadOnly(True)

        self._on_all_clear()

        display_layout.addWidget(self.expression_display)
        display_layout.addWidget(self.result_display)

        display_layout.addStretch()

        return display_layout

    def _create_buttons(self) -> QGridLayout:
        buttons_layout = QGridLayout()
        buttons_layout.setSpacing(12)

        buttons_map = [
            ("AC", (0, 0), (1, 1), "function"), ("()", (0, 1), (1, 1), "function"),
            ("^", (0, 2), (1, 1), "function"), ("√", (0, 3), (1, 1), "function"),
            ("/", (0, 4), (1, 1), "operator"),
            ("sin", (1, 0), (1, 1), "function"), ("7", (1, 1), (1, 1), "number"),
            ("8", (1, 2), (1, 1), "number"), ("9", (1, 3), (1, 1), "number"),
            ("*", (1, 4), (1, 1), "operator"),
            ("cos", (2, 0), (1, 1), "function"), ("4", (2, 1), (1, 1), "number"),
            ("5", (2, 2), (1, 1), "number"), ("6", (2, 3), (1, 1), "number"),
            ("-", (2, 4), (1, 1), "operator"),
            ("tan", (3, 0), (1, 1), "function"), ("1", (3, 1), (1, 1), "number"),
            ("2", (3, 2), (1, 1), "number"), ("3", (3, 3), (1, 1), "number"),
            ("+", (3, 4), (1, 1), "operator"),
            ("🎙️", (4, 0), (1, 1), "mic"),
            ("0", (4, 1), (1, 1), "number"),
            (".", (4, 2), (1, 1), "number"),
            ("=", (4, 3), (1, 2), "equals"),
        ]

        for (text, pos, span, prop) in buttons_map:
            button = QPushButton(text)

            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(15)
            shadow.setXOffset(0)

            if prop == "mic":
                button.setObjectName("MicButton")
                button.setText("mic")
                shadow.setYOffset(2)
                shadow.setColor(QColor(0, 0, 0, 51))

            elif prop == "operator":
                button.setProperty("class", prop)
                shadow.setYOffset(4)
                shadow.setColor(QColor(217, 70, 239, 76))

            elif prop == "equals":
                button.setProperty("class", prop)
                shadow.setYOffset(4)
                shadow.setColor(QColor(50, 215, 75, 76))

            else:  # "number" and "function"
                button.setProperty("class", prop)
                shadow.setYOffset(2)
                shadow.setColor(QColor(0, 0, 0, 51))

            button.setGraphicsEffect(shadow)
            button.clicked.connect(lambda _, t=text: self._on_button_click(t))
            buttons_layout.addWidget(button, pos[0], pos[1], span[0], span[1])

        return buttons_layout

    # --- Mouse Drag Support (to move frameless window) ---
    def mousePressEvent(self, event):
        self.oldPos = event.globalPosition()

    def mouseMoveEvent(self, event):
        delta = event.globalPosition() - self.oldPos
        self.move(int(self.x() + delta.x()), int(self.y() + delta.y()))
        self.oldPos = event.globalPosition()

    # --- Button Click Handlers ---

    def _on_button_click(self, text: str):
        """Handles all button presses."""

        # --- Set alignment for numerical/equation input ---
        # We do this here so any button press resets the alignment
        # after a status message was shown.
        self.result_display.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.expression_display.setAlignment(Qt.AlignmentFlag.AlignRight)

        if text == "🎙️":
            self._on_mic_click()
            return

        if text == "=":
            self._on_equals()
            return

        if text == "AC":
            self._on_all_clear()
            return

        if text == "()":
            self._on_parentheses()
            return

        if self.last_result_showing:
            # --- BUG FIX: Check against the list defined in calculator_core ---
            is_operator = text in calculator_core.BASIC_OPERATORS or \
                          text in ["^", "√", "sin", "cos", "tan"]

            if not is_operator:
                self.current_expression = ""

            self.last_result_showing = False

        if text in ["sin", "cos", "tan"]:
            self.current_expression += f"{text}("
        elif text == "√":
            self.current_expression += "sqrt("
        elif text == "^":
            self.current_expression += "**"  # Use **
        else:
            self.current_expression += text

        self.result_display.setText(self.current_expression)

    def _on_equals(self):
        if not self.current_expression:
            return

        # --- Set alignment for result ---
        self.result_display.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.expression_display.setAlignment(Qt.AlignmentFlag.AlignRight)

        result = calculator_core.evaluate_expression(self.current_expression)

        self.expression_display.setText(self.current_expression)
        self.result_display.setText(result)

        if "Error:" not in result:
            self.current_expression = result
            self.last_result_showing = True
        else:
            # --- Set alignment for error message ---
            self.result_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.current_expression = ""
            self.last_result_showing = False

    def _on_all_clear(self):
        # --- Set alignment for default state ---
        self.result_display.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.expression_display.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.current_expression = ""
        self.expression_display.setText("")
        self.result_display.setText("0")
        self.last_result_showing = False

    def _on_parentheses(self):
        if self.last_result_showing:
            self.current_expression = ""
            self.last_result_showing = False

        open_count = self.current_expression.count("(")
        close_count = self.current_expression.count(")")

        # --- BUG FIX: Check against the list defined in calculator_core ---
        check_tuple = tuple(calculator_core.BASIC_OPERATORS + ["**", "sqrt(", "sin(", "cos(", "tan(", "("])

        if open_count > close_count and not self.current_expression.endswith(check_tuple):
            self.current_expression += ")"
        else:
            self.current_expression += "("

        self.result_display.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.result_display.setText(self.current_expression)

    # --- AI/Mic Handler Functions ---

    def _on_mic_click(self):
        print("Mic clicked!")

        # --- Set alignment for status message ---
        self.result_display.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.expression_display.setText("")
        self.result_display.setText("Listening...")

        self.ai_worker = AiWorker()
        self.ai_thread = threading.Thread(target=self.ai_worker.run)
        self.ai_worker.command_ready.connect(self._on_ai_command_ready)
        self.ai_thread.start()

    def _on_ai_command_ready(self, expression: str):
        print(f"GUI received expression: {expression}")

        if not expression:
            # --- Set alignment for status message ---
            self.expression_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.result_display.setAlignment(Qt.AlignmentFlag.AlignRight)  # For the "0"

            self.result_display.setText("0")
            self.expression_display.setText("Could not understand")
            self.current_expression = ""
            self.last_result_showing = False
            return

        # Set alignment back to right for the expression
        self.result_display.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.expression_display.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.current_expression = expression
        self.result_display.setText(expression)
        self._on_equals()


# --- Application Entry Point ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec())

