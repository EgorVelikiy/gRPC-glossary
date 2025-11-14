"""
Модуль для работы с PostgreSQL базой данных.
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import errors
import os
import logging

logger = logging.getLogger(__name__)


class Database:
    """Класс для работы с PostgreSQL базой данных."""
    
    def __init__(self):
        """Инициализация подключения к базе данных."""
        self.host = os.getenv('DB_HOST', 'localhost')
        self.port = os.getenv('DB_PORT', '5432')
        self.database = os.getenv('DB_NAME', 'glossary')
        self.user = os.getenv('DB_USER', 'postgres')
        self.password = os.getenv('DB_PASSWORD', 'postgres')
        
        # Проверяем существование БД и создаем, если нужно
        self._ensure_database_exists()
        
        # Подключаемся к БД
        self.conn = psycopg2.connect(
            host=self.host,
            port=self.port,
            database=self.database,
            user=self.user,
            password=self.password
        )
        self._init_table()
    
    def _ensure_database_exists(self):
        """Проверка существования базы данных и создание, если её нет."""
        try:
            # Пытаемся подключиться к целевой БД
            test_conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password
            )
            test_conn.close()
            logger.info(f"База данных '{self.database}' уже существует")
        except psycopg2.errors.InvalidCatalogName:
            # БД не существует, создаем её
            logger.info(f"База данных '{self.database}' не найдена. Создание...")
            try:
                # Подключаемся к системной БД postgres для создания новой БД
                admin_conn = psycopg2.connect(
                    host=self.host,
                    port=self.port,
                    database='postgres',  # Подключаемся к системной БД
                    user=self.user,
                    password=self.password
                )
                admin_conn.autocommit = True  # Необходимо для создания БД
                
                with admin_conn.cursor() as cur:
                    cur.execute(f'CREATE DATABASE "{self.database}"')
                    logger.info(f"База данных '{self.database}' успешно создана")
                
                admin_conn.close()
            except psycopg2.OperationalError:
                logger.info(f"База данных '{self.database}' не найдена. Создание...")
                try:
                    admin_conn = psycopg2.connect(
                        host=self.host,
                        port=self.port,
                        database='postgres',
                        user=self.user,
                        password=self.password
                    )
                    admin_conn.autocommit = True
                    with admin_conn.cursor() as cur:
                        cur.execute(f'CREATE DATABASE "{self.database}"')
                        logger.info(f"База данных '{self.database}' успешно создана")
                    admin_conn.close()
                except Exception as e:
                    logger.error(f"Ошибка при создании базы данных: {repr(e)}")
                    raise
            except Exception as e:
                logger.error(f"Ошибка при подключении к базе данных: {e}")
                raise
    
    def _init_table(self):
        """Инициализация таблицы терминов."""
        with self.conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS terms (
                    keyword VARCHAR(255) PRIMARY KEY,
                    description TEXT NOT NULL
                );
            """)
            self.conn.commit()
    
    def get_all_terms(self):
        """Получение всех терминов."""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT keyword, description FROM terms ORDER BY keyword")
            return [dict(row) for row in cur.fetchall()]
    
    def get_term(self, keyword):
        """Получение термина по ключевому слову."""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT keyword, description FROM terms WHERE keyword = %s", (keyword,))
            result = cur.fetchone()
            return dict(result) if result else None
    
    def add_term(self, keyword, description):
        """Добавление нового термина."""
        with self.conn.cursor() as cur:
            cur.execute(
                "INSERT INTO terms (keyword, description) VALUES (%s, %s)",
                (keyword, description)
            )
            self.conn.commit()
            return True
    
    def update_term(self, keyword, description):
        """Обновление термина."""
        with self.conn.cursor() as cur:
            cur.execute(
                "UPDATE terms SET description = %s WHERE keyword = %s",
                (description, keyword)
            )
            self.conn.commit()
            return cur.rowcount > 0
    
    def delete_term(self, keyword):
        """Удаление термина."""
        with self.conn.cursor() as cur:
            cur.execute("DELETE FROM terms WHERE keyword = %s", (keyword,))
            self.conn.commit()
            return cur.rowcount > 0
    
    def close(self):
        """Закрытие соединения с базой данных."""
        if self.conn:
            self.conn.close()
