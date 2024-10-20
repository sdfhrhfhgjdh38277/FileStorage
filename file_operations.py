import os
import sqlite3
from loguru import logger
import shutil

DATABASE_PATH = 'file_save/cloud_storage.db'


def get_db_connection():
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def create_table():
    with get_db_connection() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                data BLOB NOT NULL
            )
        ''')
        conn.commit()


create_table()

FILES_DIR = 'file_storage'


def upload_file(file_path):
    try:
        os.makedirs(FILES_DIR, exist_ok=True)
        filename = os.path.basename(file_path)
        dest_path = os.path.join(FILES_DIR, filename)

        shutil.copy(file_path, dest_path)  # Копируем файл в хранилище

        with get_db_connection() as conn:
            conn.execute('''
                INSERT INTO files (filename, data) VALUES (?, ?)
            ''', (filename, None))  # Сохраняем только метаданные
            conn.commit()

        logger.info(f"Файл '{filename}' успешно загружен.")
    except Exception as e:
        logger.error(f"Ошибка при загрузке файла: {str(e)}")


def upload_file(file_path):
    try:
        filename = os.path.basename(file_path)
        with open(file_path, 'rb') as f:
            data = f.read()  # Читаем файл целиком
            with get_db_connection() as conn:
                conn.execute('''
                    INSERT INTO files (filename, data) VALUES (?, ?)
                ''', (filename, data))
                conn.commit()
        logger.info(f"Файл '{filename}' успешно загружен в БД.")
    except Exception as e:
        logger.error(f"Ошибка при загрузке файла: {str(e)}")


def list_files():
    try:
        with get_db_connection() as conn:
            files = conn.execute('SELECT id, filename FROM files').fetchall()
            return [{"id": file["id"], "filename": file["filename"]} for file in files]
    except Exception as e:
        logger.error(f"Ошибка при получении списка файлов: {str(e)}")
        return []


def download_file(file_id, save_path):
    try:
        with get_db_connection() as conn:
            # Получаем только нужные данные
            result = conn.execute('SELECT filename, data FROM files WHERE id = ?', (file_id,)).fetchone()

            if not result:
                logger.warning(f"Файл с ID {file_id} не найден.")
                return

            filename = result["filename"]
            file_data = result["data"]

            output_path = os.path.join(save_path, filename)
            logger.info(f"Выгрузка файла '{filename}' в '{output_path}'.")

            # Используем потоковую запись
            with open(output_path, 'wb') as f:
                f.write(file_data)

            logger.info(f"Файл '{filename}' успешно выгружен.")
    except Exception as e:
        logger.error(f"Ошибка при выгрузке файла: {str(e)}")


def get_file_preview(file_id):
    try:
        with get_db_connection() as conn:
            file = conn.execute('SELECT filename, data, size, created_at FROM files WHERE id = ?',
                                (file_id,)).fetchone()
            if file is None:
                logger.warning(f"Файл с ID {file_id} не найден.")
                return None

            # Для текстовых файлов возвращаем содержимое и метаданные
            filename, data, size, created_at = file
            preview_data = data.decode('utf-8') if data else "Нет данных для отображения."

            return {
                'filename': filename,
                'preview': preview_data,
                'size': size,
                'created_at': created_at
            }
    except Exception as e:
        logger.error(f"Ошибка при получении предпросмотра файла: {str(e)}")
        return None
