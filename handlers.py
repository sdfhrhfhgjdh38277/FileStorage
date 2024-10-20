import flet as ft
import os
import shutil
from loguru import logger
from file_operations import list_files, upload_file, download_file


def update_file_list(page, file_list):
    try:
        files = list_files()
        file_names = [filename for file_id, filename in files]
        file_list.options = [ft.dropdown.Option(file) for file in file_names]
        file_list.value = None
        file_list.update()
        logger.info("File list updated successfully.")
    except Exception as e:
        error_msg = f'Failed to update file list: {str(e)}'
        page.add(ft.Text(error_msg, color=ft.colors.RED))
        logger.error(error_msg)


def upload_file_action(e: ft.FilePickerResultEvent):
    try:
        if e.files:
            print("Files selected for upload.")
            for file in e.files:
                with open(file.path, "rb") as f:
                    data = f.read()
                    print(f"File read: {file.name}, size: {len(data)}")
                    upload_file(file.name, data)
            # Обновление списка файлов
            update_file_list(e.page, e.page.controls[0])  # Передача страницы и списка файлов
            print(f"Uploaded files: {[file.name for file in e.files]}")
    except Exception as ex:
        print(f"Failed to upload files: {str(ex)}")


def download_file_action(e):
    try:
        page = e.page
        file_list = page.controls[0]
        save_path_input = page.controls[1]

        selected_file = file_list.value  # Получаем выбранный файл из выпадающего списка
        if not selected_file:
            error_msg = 'No file selected for download.'
            page.add(ft.Text(error_msg, color=ft.colors.RED))
            logger.warning(error_msg)
            return

        file_id = None
        files = list_files()
        for fid, fname in files:
            if fname == selected_file:
                file_id = fid
                break

        if file_id is None:
            error_msg = 'Selected file not found in the database.'
            page.add(ft.Text(error_msg, color=ft.colors.RED))
            logger.error(error_msg)
            return
            save_path = save_path_input.value
            if save_path:
                try:
                    logger.info(f"Attempting to save file to: {save_path}")
                    save_dir = os.path.dirname(save_path)
                    if not os.path.exists(save_dir):
                        logger.info(f"Directory does not exist. Creating: {save_dir}")
                        os.makedirs(save_dir, exist_ok=True)

                    total, used, free = shutil.disk_usage(save_dir)
                    if free < len(file_data):
                        error_msg = f"Not enough disk space. Available: {free} bytes."
                        page.add(ft.Text(error_msg, color=ft.colors.RED))
                        logger.error(error_msg)
                        return

                    with open(save_path, "wb") as f:
                        f.write(file_data)
                    success_msg = f'File saved to {save_path}'
                    page.add(ft.Text(success_msg, color=ft.colors.GREEN))
                    logger.info(success_msg)
                except PermissionError:
                    error_msg = f'Permission denied. Cannot save the file to {save_path}.'
                    page.add(ft.Text(error_msg, color=ft.colors.RED))
                    logger.error(error_msg)
                except FileNotFoundError:
                    error_msg = f'Directory does not exist for path: {save_path}.'
                    page.add(ft.Text(error_msg, color=ft.colors.RED))
                    logger.error(error_msg)
                except Exception as ex:
                    error_msg = f'Failed to save file: {str(ex)}'
                    page.add(ft.Text(error_msg, color=ft.colors.RED))
                    logger.error(f'{error_msg} - {ex}')
            else:
                error_msg = 'No save path provided.'
                page.add(ft.Text(error_msg, color=ft.colors.RED))
                logger.warning(error_msg)
        else:
            error_msg = 'File ID not found.'
            page.add(ft.Text(error_msg, color=ft.colors.RED))
            logger.error(error_msg)
    except Exception as ex:
        error_msg = f'Failed to download file: {str(ex)}'
        if e.page:
            e.page.add(ft.Text(error_msg, color=ft.colors.RED))
        logger.error(error_msg)
