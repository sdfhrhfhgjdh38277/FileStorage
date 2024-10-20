import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget, QLabel,
    QFileDialog, QMessageBox, QTextEdit, QStackedWidget, QSlider, QStyle, QScrollArea
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget
from file_operations import upload_file, list_files, download_file, get_db_connection

TEMP_DIR = "temp"

# Создаём директорию temp, если её нет
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)


def get_file_preview(file_id):
    try:
        with get_db_connection() as conn:
            result = conn.execute('SELECT filename, data FROM files WHERE id = ?', (file_id,)).fetchone()
            if not result:
                return None, 'Файл не найден.'

            filename = result[0]
            data = result[1]
            file_path = os.path.join(TEMP_DIR, filename)

            with open(file_path, "wb") as f:
                f.write(data)

            if filename.endswith(('.txt', '.py')):
                return create_text_preview(file_path), None

            elif filename.endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                return create_image_preview(file_path), None

            elif filename.endswith('.mp3'):
                return create_audio_player(file_path), None

            elif filename.endswith('.mp4'):
                return create_video_player(file_path), None

            else:
                return QLabel("Предпросмотр недоступен для этого типа файла."), None

    except Exception as e:
        return None, f'Ошибка: {str(e)}'


def create_text_preview(file_path):
    """Создаёт текстовый виджет с прокруткой для отображения содержимого."""
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    text_widget = QTextEdit(content)
    text_widget.setReadOnly(True)
    return text_widget


def create_image_preview(file_path):
    """Создаёт виджет для отображения изображения с прокруткой."""
    pixmap = QPixmap(file_path)

    # Создаём QLabel для изображения
    label = QLabel()
    label.setPixmap(pixmap)
    label.setAlignment(Qt.AlignCenter)

    # Создаём QScrollArea для прокрутки
    scroll_area = QScrollArea()
    scroll_area.setWidget(label)
    scroll_area.setWidgetResizable(True)

    # Устанавливаем размеры QScrollArea, чтобы оно занимало доступное пространство
    scroll_area.setMinimumSize(400, 300)
    scroll_area.setMaximumSize(1920, 1080)  # Установите максимум, как вам нужно

    return scroll_area


def create_audio_player(audio_path):
    """Создаёт аудиоплеер для воспроизведения mp3-файлов."""
    player = QMediaPlayer()
    player.setMedia(QMediaContent(QUrl.fromLocalFile(audio_path)))

    play_button = QPushButton()
    play_button.setIcon(play_button.style().standardIcon(QStyle.SP_MediaPlay))
    play_button.clicked.connect(
        lambda: player.play() if player.state() != QMediaPlayer.PlayingState else player.pause())

    layout = QVBoxLayout()
    layout.addWidget(play_button)

    audio_widget = QWidget()
    audio_widget.setLayout(layout)

    return audio_widget


def create_video_player(video_path):
    """Создаёт видеоплеер для воспроизведения mp4-файлов."""
    player = QMediaPlayer()
    video_widget = QVideoWidget()

    player.setVideoOutput(video_widget)
    player.setMedia(QMediaContent(QUrl.fromLocalFile(video_path)))

    play_button = QPushButton()
    play_button.setIcon(play_button.style().standardIcon(QStyle.SP_MediaPlay))
    play_button.clicked.connect(
        lambda: player.play() if player.state() != QMediaPlayer.PlayingState else player.pause())

    slider = QSlider(Qt.Horizontal)
    slider.setRange(0, player.duration() // 1000)
    player.positionChanged.connect(lambda pos: slider.setValue(pos // 1000))
    slider.sliderMoved.connect(lambda pos: player.setPosition(pos * 1000))

    layout = QVBoxLayout()
    layout.addWidget(video_widget)
    layout.addWidget(play_button)
    layout.addWidget(slider)

    video_widget_container = QWidget()
    video_widget_container.setLayout(layout)

    return video_widget_container


class FilePreviewApp(QWidget):
    def __init__(self):
        super().__init__()
        self.file_list = None
        self.preview_area = None
        self.init_ui()
        self.update_file_list()

    def init_ui(self):
        main_layout = QHBoxLayout()

        # Список файлов
        self.file_list = QListWidget()
        self.file_list.setMaximumWidth(150)
        self.file_list.itemClicked.connect(self.preview_file)

        left_layout = QVBoxLayout()
        left_layout.addWidget(self.file_list)

        # Кнопки
        upload_button = QPushButton('Загрузить файл в БД с ПК')
        upload_button.clicked.connect(self.upload_file)

        download_button = QPushButton('Выгрузить файл из БД в ПК')
        download_button.clicked.connect(self.download_file)

        button_layout = QVBoxLayout()
        button_layout.addWidget(upload_button)
        button_layout.addWidget(download_button)

        left_layout.addLayout(button_layout)
        main_layout.addLayout(left_layout)

        # Область предпросмотра
        self.preview_area = QStackedWidget()
        placeholder = QLabel('Предпросмотр файла будет здесь')
        placeholder.setStyleSheet("background-color: lightgray;")
        placeholder.setAlignment(Qt.AlignCenter)
        self.preview_area.addWidget(placeholder)

        main_layout.addWidget(self.preview_area)
        self.setLayout(main_layout)

        self.setWindowTitle('File Preview Application')
        self.setGeometry(300, 300, 800, 600)

    def update_file_list(self):
        """Обновляет список файлов из базы данных."""
        self.file_list.clear()
        files = list_files()
        for file in files:
            self.file_list.addItem(f"{file['id']}: {file['filename']}")

    def upload_file(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self, "Выберите файл для загрузки", "", "All Files (*)",
                                                   options=options)
        if file_name:
            upload_file(file_name)
            self.update_file_list()
            QMessageBox.information(self, "Успех", "Файл успешно загружен в базу данных.")

    def download_file(self):
        if self.file_list.currentItem() is None:
            QMessageBox.warning(self, "Ошибка", "Выберите файл для выгрузки.")
            return

        file_info = self.file_list.currentItem().text().split(": ")
        file_id = int(file_info[0])

        folder_path = QFileDialog.getExistingDirectory(self, "Выберите папку для сохранения")
        if folder_path:
            download_file(file_id, folder_path)
            QMessageBox.information(self, "Успех", "Файл успешно выгружен.")

    def preview_file(self, item):
        file_info = item.text().split(": ")
        file_id = int(file_info[0])

        preview_widget, error = get_file_preview(file_id)
        if error:
            QMessageBox.warning(self, "Ошибка", error)
            return

        self.preview_area.addWidget(preview_widget)
        self.preview_area.setCurrentWidget(preview_widget)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = FilePreviewApp()
    ex.show()
    sys.exit(app.exec_())
