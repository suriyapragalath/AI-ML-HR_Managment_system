
import sys
import json
import requests
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QTextEdit, QPushButton, QLabel, 
                            QScrollArea, QFrame)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QPixmap, QImage
import base64
from io import BytesIO

WELCOME_MESSAGE = """Welcome! 👋 
I can help you with:
1. Time Series Prediction for employee leave data
2. Project Completion Estimation


Please enter your query above."""

class ResponseThread(QThread):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, url, prompt):
        super().__init__()
        self.url = url
        self.prompt = prompt

    def run(self):
        try:
            response = requests.post(
                self.url,
                json={"prompt": self.prompt},
                headers={"Content-Type": "application/json"}
            )
            if response.status_code == 200:
                self.finished.emit(response.json())
            else:
                self.error.emit(f"Error: Server returned status code {response.status_code}")
        except Exception as e:
            self.error.emit(f"Error: {str(e)}")

class MessageBubble(QFrame):
    def __init__(self, is_user=True, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        
        # ChatGPT-like styling
        self.setStyleSheet(
            "QFrame { "
            "border-radius: 15px; "
            "padding: 15px; "
            "margin: 10px; "
            f"background-color: {'#343541' if is_user else '#444654'}; "
            "color: white; "
            "}"
        )
        
        self.layout.setContentsMargins(15, 10, 15, 10)
        self.layout.setSpacing(10)

class ChatApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.backend_url = "https://030c-35-240-242-212.ngrok-free.app/process"  # Update with your ngrok URL
        self.init_ui()
        # Add welcome message
        self.add_message(WELCOME_MESSAGE, is_user=False)

    def init_ui(self):
        self.setWindowTitle('AI Assistant')
        self.setGeometry(100, 100, 1000, 800)
        self.setStyleSheet("background-color: #202123;")

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        # Chat display area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("""
            QScrollArea { 
                border: none;
                background-color: #202123;
            }
            QScrollBar:vertical {
                border: none;
                background-color: #202123;
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background-color: #565869;
                border-radius: 5px;
            }
        """)

        self.chat_widget = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_widget)
        self.chat_layout.addStretch()
        
        self.scroll_area.setWidget(self.chat_widget)
        layout.addWidget(self.scroll_area)

        # Input area
        input_layout = QHBoxLayout()
        
        self.input_field = QTextEdit()
        self.input_field.setPlaceholderText("Type your message here...")
        self.input_field.setMaximumHeight(100)
        self.input_field.setStyleSheet("""
            QTextEdit {
                border: 1px solid #565869;
                border-radius: 10px;
                padding: 10px;
                background-color: #40414f;
                color: white;
            }
        """)
        input_layout.addWidget(self.input_field)

        send_button = QPushButton("Send")
        send_button.clicked.connect(self.send_message)
        send_button.setStyleSheet("""
            QPushButton {
                background-color: #19c37d;
                color: white;
                border-radius: 10px;
                padding: 10px 20px;
                font-size: 14px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #1a8870;
            }
        """)
        input_layout.addWidget(send_button)

        layout.addLayout(input_layout)

    def add_message(self, content, is_user=True):
     bubble = MessageBubble(is_user)
    
     if isinstance(content, str):
        try:
            # Try to decode as base64 image first
            image_data = base64.b64decode(content)
            image = QImage.fromData(image_data)
            
            if not image.isNull():
                # If successful, display as image
                pixmap = QPixmap.fromImage(image)
                
                # Scale if needed while maintaining aspect ratio
                if pixmap.width() > 600:
                    pixmap = pixmap.scaledToWidth(600, Qt.TransformationMode.SmoothTransformation)
                
                image_label = QLabel()
                image_label.setPixmap(pixmap)
                image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                bubble.layout.addWidget(image_label)
            else:
                # If not a valid image, display as text
                label = QLabel(content)
                label.setWordWrap(True)
                label.setStyleSheet("color: white; font-size: 14px;")
                bubble.layout.addWidget(label)
        except:
            # If base64 decoding fails, display as text
            label = QLabel(content)
            label.setWordWrap(True)
            label.setStyleSheet("color: white; font-size: 14px;")
            bubble.layout.addWidget(label)
    
     self.chat_layout.addWidget(bubble)
    
    # Scroll to bottom
     QApplication.processEvents()
     self.scroll_area.verticalScrollBar().setValue(
        self.scroll_area.verticalScrollBar().maximum()
    )

    def send_message(self):
        prompt = self.input_field.toPlainText().strip()
        if not prompt:
            return

        # Add user message to chat
        self.add_message(prompt, is_user=True)
        self.input_field.clear()

        # Create and start response thread
        self.thread = ResponseThread(self.backend_url, prompt)
        self.thread.finished.connect(self.handle_response)
        self.thread.error.connect(self.handle_error)
        self.thread.start()
    def handle_response(self, response):
     # Extract text and base64 keys from the response
     text = response.get('result', '')
     base64_image = response.get('base64', '')

     try:
        # Display the text part
        if text:
            self.add_message(str(text), is_user=False)
        
        # If there's a base64 image, process it
        if base64_image:
            # Remove whitespace or newlines
            base64_image = base64_image.strip()
            
            # Remove data URI prefix if present
            if 'base64,' in base64_image:
                base64_image = base64_image.split('base64,')[1]
            
            # Decode and verify the base64 image
            try:
                image_data = base64.b64decode(base64_image)
                image = QImage.fromData(image_data)
                
                if not image.isNull():
                    # Add the decoded image to the chat
                    self.add_message(base64_image, is_user=False)
                else:
                    # Handle invalid image data gracefully
                    self.add_message("Error: Could not render the image.", is_user=False)
            except Exception as e:
                self.add_message(f"Error decoding image: {str(e)}", is_user=False)

     except Exception as e:
        self.add_message(f"Error processing response: {str(e)}", is_user=False)



    def handle_error(self, error_message):
        self.add_message(f"Error: {error_message}", is_user=False)

def main():
    app = QApplication(sys.argv)
    chat_app = ChatApp()
    chat_app.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()