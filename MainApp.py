import os
import re
import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QWidget,
                             QLabel, QLineEdit, QPushButton, QComboBox, QFileDialog,
                             QHBoxLayout, QMessageBox)
from PyQt5.QtGui import QIntValidator
from PyQt5.QtCore import pyqtSignal
from PyQt5 import QtGui
from threading import Thread
import data_for_start_from_telegram
import AlertEye
import AlertEyeYouTube
import TelegramBot


# from AlertEye import vision, stop_processes
# from TelegramBot import start_telebot, stop_telebot, system_is_on_message, system_is_of_message


class MainApp(QMainWindow):
    error_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.error_signal.connect(self.show_error_message)
        self.models = {              
            'yolov8n': 'model path',  # For example D:\\PycharmProjects\\pythonProject\\yolov10\\yolov10x.pt
            'yolov8s': 'model path',
            'yolov8m': 'model path',
            'yolov8l': 'model path',
            'yolov9c': 'model path',
            'yolov8x': 'model path',
            'yolov10n': 'model path',
            'yolov10s': 'model path',
            'yolov10m': 'model path',
            'yolov10b': 'model path',
            'yolov10l': 'model path',
            'yolov10x': 'model path',
        }
        self.photos_dir = "photos dir"
        self.videos_dir = "videos dir"
        self.vision_thread = None
        self.telebot_thread = None
        #self.setWindowIcon(QtGui.QIcon('C:\\Users\\quinki\\Downloads\\072934f5-5ac3-44b9-acd0-3611def46442_1.ico'))  # Unecessary part of code adding icon
        self.initUI()

    def show_error_message(self, message):
        QMessageBox.critical(self, "Ошибка", message)

    def initUI(self):
        self.setWindowTitle("Панель настройки системы")
        self.setGeometry(100, 100, 600, 600)
        self.setStyleSheet("font-size: 10pt;") 
        layout = QVBoxLayout()

        # RTSP stream input
        self.rtsp_input = QLineEdit()
        layout.addWidget(QLabel("RTSP сслыка:"))
        layout.addWidget(self.rtsp_input)
        self.rtsp_input.setText("RTSP link")

        # Width and Height input
        self.width_input = QLineEdit()
        self.height_input = QLineEdit()
        layout.addWidget(QLabel("Ширина окна:"))
        layout.addWidget(self.width_input)
        layout.addWidget(QLabel("Высота окна:"))
        layout.addWidget(self.height_input)

        self.width_input.setText("1280")
        self.height_input.setText("720")

        only_int_validator = QIntValidator(self)
        self.width_input.setValidator(only_int_validator)
        self.height_input.setValidator(only_int_validator)

        # Model selection
        self.model_dropdown = QComboBox()
        self.model_dropdown.addItems(list(self.models.keys()))
        layout.addWidget(QLabel("Модель YOLO:"))
        layout.addWidget(self.model_dropdown)
        self.model_dropdown.setCurrentIndex(self.model_dropdown.findText('yolov8m'))

        # Image size selection
        self.imgsz_dropdown = QComboBox()
        self.imgsz_dropdown.addItems([str(i) for i in range(640, 8001, 32)])
        layout.addWidget(QLabel("Размер входного изображения:"))
        layout.addWidget(self.imgsz_dropdown)
        self.imgsz_dropdown.setCurrentIndex(self.imgsz_dropdown.findText('640'))

        # Photos directory selection
        photo_layout = QHBoxLayout()
        self.photos_dir_label = QLabel("Расположение фотографий:")
        self.photos_dir_button = QPushButton("Выбрать расположение...")
        self.photos_dir_button.clicked.connect(self.select_photos_directory)
        self.photos_dir_display = QLabel(self.photos_dir)
        photo_layout.addWidget(self.photos_dir_label)
        photo_layout.addWidget(self.photos_dir_button, 1)  
        photo_layout.addWidget(self.photos_dir_display, 2)  
        layout.addLayout(photo_layout)

        # Videos directory selection
        video_layout = QHBoxLayout()
        self.videos_dir_label = QLabel("Расположение видео:")
        self.videos_dir_button = QPushButton("Выбрать расположение...")
        self.videos_dir_button.clicked.connect(self.select_videos_directory)
        self.videos_dir_display = QLabel(self.videos_dir)
        video_layout.addWidget(self.videos_dir_label)
        video_layout.addWidget(self.videos_dir_button, 1)  
        video_layout.addWidget(self.videos_dir_display, 2) 
        layout.addLayout(video_layout)

        layout.addSpacing(30) 

        # Start button
        self.start_button = QPushButton("Запустить")
        self.start_button.setStyleSheet("font-size: 10pt; QPushButton { height: 50px; }")  
        global is_running
        self.start_button.clicked.connect(self.start_processes)
        layout.addWidget(self.start_button)

        layout.addSpacing(30)

        # Close button
        self.close_button = QPushButton("Закрыть потоки")
        self.close_button.setStyleSheet("font-size: 10pt; QPushButton { height: 50px; }")
        self.close_button.clicked.connect(self.close_threads)
        # self.close_button.clicked.connect(stop_telebot)
        # self.close_button.clicked.connect(self.close_application)
        layout.addWidget(self.close_button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def select_photos_directory(self):
        self.photos_dir = QFileDialog.getExistingDirectory(self, "Выбранное расположение: ")
        self.photos_dir_display.setText(self.photos_dir)
        print(f"Selected photos directory: {self.photos_dir}")

    def select_videos_directory(self):
        self.videos_dir = QFileDialog.getExistingDirectory(self, "Выбранное расположение: ")
        self.videos_dir_display.setText(self.videos_dir)
        print(f"Selected videos directory: {self.videos_dir}")

    def start_processes(self):
        global is_running
        global youtube
        youtube = False
        is_running = True
        error = False

        stream_url = self.rtsp_input.text().strip()  
        width = self.width_input.text().strip()
        height = self.height_input.text().strip()
        selected_model_key = self.model_dropdown.currentText()
        model_path = self.models.get(selected_model_key, "")
        img_size = self.imgsz_dropdown.currentText().strip()
        photos_dir_filled = bool(self.photos_dir) 
        videos_dir_filled = bool(self.videos_dir) 

        # Проверяем, что все необходимые поля заполнены
        # Проверка заполнения обязательных полей
        if not stream_url:
            QMessageBox.warning(self, "Ошибка запуска", "URL потока должен быть указан!")
            return

        if not (width.isdigit() and height.isdigit()):
            QMessageBox.warning(self, "Ошибка запуска",
                                "Ширина и высота должны быть указаны и быть числовыми значениями!")
            return

        # Проверка наличия предустановленных директорий
        if not hasattr(self, 'photos_dir') or not hasattr(self, 'videos_dir'):
            QMessageBox.warning(self, "Ошибка конфигурации", "Директории для фото и видео не настроены!")
            return

        # Проверка, что хотя бы одна из предустановленных директорий существует
        if not (os.path.exists(self.photos_dir) or os.path.exists(self.videos_dir)):
            QMessageBox.warning(self, "Ошибка конфигурации", "Ни одна из предустановленных директорий не существует!")
            return

        width = int(width)
        height = int(height)

        print(f"Preparing to start vision with model: {model_path}")
        if not re.search(r'\byoutube\b', stream_url, re.IGNORECASE):
            try:
                print(f'\nProgram started with parameters:\n'
                      f'Stream URL: {stream_url}\n'
                      f'Width/Height: {width}/{height}\n'
                      f'Model: {selected_model_key}\n'
                      f'Input image size: {img_size}\n'
                      f'Photos directory: {self.photos_dir}\n'
                      f'Videos directory: {self.videos_dir}\n')
                self.vision_thread = Thread(target=AlertEye.vision, args=(
                    stream_url, width, height, model_path, img_size, self.photos_dir, self.videos_dir, self),
                                            daemon=True)
                self.vision_thread.start()

            except Exception as e:
                QMessageBox.critical(self, "Ошибка RTSP. Проверьте ссылку")
                print(f"Ошибка при запуске потоков: {str(e)}")
                error = True
            if not error:
                self.telebot_thread = Thread(target=TelegramBot.start_telebot, daemon=True)
                self.telebot_thread.start()
            self.rtsp_input.setEnabled(False)
            self.width_input.setEnabled(False)
            self.height_input.setEnabled(False)
            self.model_dropdown.setEnabled(False)
            self.imgsz_dropdown.setEnabled(False)
            self.photos_dir_button.setEnabled(False)
            self.videos_dir_button.setEnabled(False)
            self.start_button.setEnabled(False)
        else:
            try:
                youtube = True
                print(f'\nProgram started with parameters:\n'
                      f'Stream URL: {stream_url}\n'
                      f'Width/Height: {width}/{height}\n'
                      f'Model: {selected_model_key}\n'
                      f'Input image size: {img_size}\n'
                      f'Photos directory: {self.photos_dir}\n'
                      f'Videos directory: {self.videos_dir}\n')
                self.vision_thread = Thread(target=AlertEyeYouTube.vision, args=(
                    stream_url, width, height, model_path, img_size, self.photos_dir, self.videos_dir, self),
                                            daemon=True)
                self.vision_thread.start()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка RTSP. Проверьте ссылку")
                print(f"Ошибка при запуске потоков: {str(e)}")
                error = True
            if not error:
                self.telebot_thread = Thread(target=TelegramBot.start_telebot, daemon=True)
                self.telebot_thread.start()
            self.rtsp_input.setEnabled(False)
            self.width_input.setEnabled(False)
            self.height_input.setEnabled(False)
            self.model_dropdown.setEnabled(False)
            self.imgsz_dropdown.setEnabled(False)
            self.photos_dir_button.setEnabled(False)
            self.videos_dir_button.setEnabled(False)
            self.start_button.setEnabled(False)

    def close_threads(self):
        if not youtube:
            AlertEye.stop_processes()
        else:
            AlertEyeYouTube.stop_processes()

        if self.vision_thread:
            self.vision_thread.join()
        TelegramBot.stop_telebot()
        if self.telebot_thread:
            self.telebot_thread.join()

        self.rtsp_input.setEnabled(True)
        self.width_input.setEnabled(True)
        self.height_input.setEnabled(True)
        self.model_dropdown.setEnabled(True)
        self.imgsz_dropdown.setEnabled(True)
        self.photos_dir_button.setEnabled(True)
        self.videos_dir_button.setEnabled(True)
        self.start_button.setEnabled(True)


def main():
    app = QApplication(sys.argv)
    ex = MainApp()
    ex.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
