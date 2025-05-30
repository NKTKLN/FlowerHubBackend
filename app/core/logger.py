"""Модуль настройки логгирования для приложения.

Предоставляет функцию setup_logger для конфигурации вывода логов в файл или консоль,
а также возможность полного отключения логгирования. Используется для контроля
вывода диагностической информации во время исполнения.
"""

import logging


def setup_logger(
    disable_logging: bool = False, log_level: int = logging.INFO, log_file: str = ""
) -> None:
    """Настраивает систему логгирования для приложения.

    Конфигурирует базовые настройки логирования с возможностью вывода как в консоль,
    так и в файл. Поддерживает полное отключение логирования при необходимости.

    Args:
        disable_logging: Флаг отключения логирования. Если True, все логи будут
                         отключены на уровне CRITICAL. Default: False.
        log_level: Уровень детализации логирования. Допустимые значения:
                   logging.DEBUG, INFO, WARNING, ERROR, CRITICAL. Default: INFO.
        log_file: Путь к файлу для записи логов. Если None, вывод будет направлен
                  в стандартный поток вывода (консоль). Default: ''.
    """
    if disable_logging:
        logging.disable(logging.CRITICAL)
        return

    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    logging.basicConfig(level=log_level, format=log_format, filename=log_file, filemode="a")
