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
            'yolov8n': 'D:\\PycharmProjects\\pythonProject19(WORK)\\yolov8n.pt',
            'yolov8s': 'D:\\PycharmProjects\\pythonProject19(WORK)\\yolov8s.pt',
            'yolov8m': 'D:\\PycharmProjects\\pythonProject19(WORK)\\yolov8m.pt',
            'yolov8l': 'D:\\PycharmProjects\\pythonProject19(WORK)\\yolov8l.pt',
            'yolov9c': 'D:\\PycharmProjects\\pythonProject19(WORK)\\yolov9c.pt',
            'yolov8x': 'D:\\PycharmProjects\\pythonProject19(WORK)\\yolov8x.pt',
            'yolov10n': 'D:\\PycharmProjects\\pythonProject19(WORK)\\yolov10\\yolov10n.pt',
            'yolov10s': 'D:\\PycharmProjects\\pythonProject19(WORK)\\yolov10\\yolov10s.pt',
            'yolov10m': 'D:\\PycharmProjects\\pythonProject19(WORK)\\yolov10\\yolov10m.pt',
            'yolov10b': 'D:\\PycharmProjects\\pythonProject19(WORK)\\yolov10\\yolov10b.pt',
            'yolov10l': 'D:\\PycharmProjects\\pythonProject19(WORK)\\yolov10\\yolov10l.pt',
            'yolov10x': 'D:\\PycharmProjects\\pythonProject19(WORK)\\yolov10\\yolov10x.pt',
        }
        self.photos_dir = "D:\\PycharmProjects\\pythonProject19(WORK)\\Photos"
        self.videos_dir = "D:\\PycharmProjects\\pythonProject19(WORK)\\Videos"
        self.vision_thread = None
        self.telebot_thread = None
        self.setWindowIcon(QtGui.QIcon('C:\\Users\\quinki\\Downloads\\072934f5-5ac3-44b9-acd0-3611def46442_1.ico'))
        self.initUI()

    def show_error_message(self, message):
        QMessageBox.critical(self, "Ошибка", message)

    def initUI(self):
        self.setWindowTitle("Панель настройки системы")
        self.setGeometry(100, 100, 600, 600)
        self.setStyleSheet("font-size: 10pt;")  # Установка общего размера шрифта для всех элементов
        layout = QVBoxLayout()

        # RTSP stream input
        self.rtsp_input = QLineEdit()
        layout.addWidget(QLabel("RTSP сслыка:"))
        layout.addWidget(self.rtsp_input)
        self.rtsp_input.setText("rtsp://192.168.1.17/user=ukte&password=Kungey303336&channel=1&stream=0.sdp?")
       # self.rtsp_input.setText("rtsp://192.168.1.30/user=admin&password=303336&channel=4&stream=0.sdp?")

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
        photo_layout.addWidget(self.photos_dir_button, 1)  # Добавление аргумента stretch
        photo_layout.addWidget(self.photos_dir_display, 2)  # Добавление аргумента stretch для дополнительного места
        layout.addLayout(photo_layout)

        # Videos directory selection
        video_layout = QHBoxLayout()
        self.videos_dir_label = QLabel("Расположение видео:")
        self.videos_dir_button = QPushButton("Выбрать расположение...")
        self.videos_dir_button.clicked.connect(self.select_videos_directory)
        self.videos_dir_display = QLabel(self.videos_dir)
        video_layout.addWidget(self.videos_dir_label)
        video_layout.addWidget(self.videos_dir_button, 1)  # Добавление аргумента stretch
        video_layout.addWidget(self.videos_dir_display, 2)  # Добавление аргумента stretch для дополнительного места
        layout.addLayout(video_layout)

        layout.addSpacing(30)  # Добавление дополнительного пространства

        # Start button
        self.start_button = QPushButton("Запустить")
        self.start_button.setStyleSheet("font-size: 10pt; QPushButton { height: 50px; }")  # Увеличение кнопки и текста
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

        stream_url = self.rtsp_input.text().strip()  # Убираем лишние пробелы
        # stream_url = "rtsp://192.168.1.30/user=admin&password=303336&channel=3&stream=0.sdp?" if self.rtsp_input.text().strip() == "rtsp://192.168.1.64/user=Admin&password=f696z6$b^1v367&channel=3&stream=0.sdp" else self.rtsp_input.text().strip()
        width = self.width_input.text().strip()
        height = self.height_input.text().strip()
        selected_model_key = self.model_dropdown.currentText()
        model_path = self.models.get(selected_model_key, "")
        img_size = self.imgsz_dropdown.currentText().strip()
        photos_dir_filled = bool(self.photos_dir)  # Проверка, что директория для фото выбрана
        videos_dir_filled = bool(self.videos_dir)  # Проверка, что директория для видео выбрана

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

        # Преобразуем строки в числа
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

                # data_for_start_from_telegram.data = {
                #     "stream_url": stream_url,
                #     "width": width,
                #     "height": height,
                #     "model_path": model_path,
                #     "img_size": img_size,
                #     "photos_dir": self.photos_dir,
                #     "videos_dir": self.videos_dir,
                #     "app": self
                # }

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
