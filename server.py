import logging
import os
from file_operations import create_table

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Создание таблицы при первом запуске
create_table()

# Проверка, создалась ли база данных
if os.path.exists('file_save/cloud_storage.db'):
    logging.info("Database file created successfully.")
else:
    logging.error("Database file was not created.")
