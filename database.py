import psycopg2
from psycopg2.extras import RealDictCursor
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Настройки подключения к БД - ИСПОЛЬЗУЕМ ТОЛЬКО ASCII СИМВОЛЫ
DB_CONFIG = {
    'dbname': 'cinema_db',
    'user': 'postgres',
    'host': '127.0.0.1',  # Используем IP вместо localhost
    'port': '5432',
    'client_encoding': 'WIN1251'  # Кодировка для Windows
}


class Database:
    def __init__(self):
        self.conn = None

    def get_connection(self):
        """Установка соединения с БД"""
        try:
            if not self.conn or self.conn.closed:
                logger.info("Подключение к базе данных...")

                # Создаем DSN строку вручную (чтобы избежать проблем с кодировкой)
                dsn = f"dbname='cinema_db' user='postgres' password='postgres' host='127.0.0.1' port='5432' client_encoding='WIN1251'"
                self.conn = psycopg2.connect(dsn, cursor_factory=RealDictCursor)

                # Проверяем подключение простым запросом
                with self.conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    cur.fetchone()

                logger.info("✅ Подключение успешно установлено")
            return self.conn
        except Exception as e:
            logger.error(f"❌ Ошибка подключения к БД: {e}")
            raise

    def close(self):
        """Закрытие соединения"""
        if self.conn and not self.conn.closed:
            self.conn.close()
            logger.info("Соединение с БД закрыто")

    def _fix_encoding(self, value):
        """Исправление кодировки для строк"""
        if isinstance(value, str):
            try:
                # Пробуем разные варианты
                return value.encode('latin1').decode('utf-8')
            except:
                try:
                    return value.encode('latin1').decode('cp1251')
                except:
                    return value
        return value

    def _fix_row(self, row):
        """Исправление кодировки для всей строки"""
        if not row:
            return row
        result = {}
        for key, value in row.items():
            if isinstance(value, str):
                result[key] = self._fix_encoding(value)
            else:
                result[key] = value
        return result

    def _fix_rows(self, rows):
        """Исправление кодировки для списка строк"""
        return [self._fix_row(row) for row in rows]

    # ========== ФИЛЬМЫ ==========
    def get_movies(self):
        """Получение всех фильмов"""
        conn = self.get_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT id, title, duration, genre, age_rating FROM movies ORDER BY id")
            return self._fix_rows(cur.fetchall())

    def add_movie(self, title, duration, genre, age_rating):
        """Добавление нового фильма"""
        conn = self.get_connection()
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO movies (title, duration, genre, age_rating) 
                VALUES (%s, %s, %s, %s) 
                RETURNING id
            """, (title, duration, genre, age_rating))
            conn.commit()
            return cur.fetchone()['id']

    def delete_movie(self, movie_id):
        """Удаление фильма"""
        conn = self.get_connection()
        with conn.cursor() as cur:
            cur.execute("DELETE FROM movies WHERE id = %s", (movie_id,))
            conn.commit()
            return cur.rowcount > 0

    # ========== СЕАНСЫ ==========
    def get_sessions(self):
        """Получение всех сеансов"""
        conn = self.get_connection()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    s.id,
                    to_char(s.session_date, 'DD.MM.YYYY') as date,
                    s.session_date as date_raw,
                    to_char(s.start_time, 'HH24:MI') as start_time,
                    to_char(s.end_time, 'HH24:MI') as end_time,
                    m.title as movie,
                    h.hall_number as hall,
                    t.tariff_name,
                    t.price
                FROM sessions s
                JOIN movies m ON s.movie_id = m.id
                JOIN halls h ON s.hall_id = h.id
                JOIN tariffs t ON s.tariff_id = t.id
                ORDER BY s.session_date, s.start_time
            """)
            return self._fix_rows(cur.fetchall())

    def get_session_by_id(self, session_id):
        """Получение информации о конкретном сеансе"""
        conn = self.get_connection()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    s.id,
                    to_char(s.session_date, 'DD.MM.YYYY') as date,
                    s.session_date as date_raw,
                    to_char(s.start_time, 'HH24:MI') as start_time,
                    to_char(s.end_time, 'HH24:MI') as end_time,
                    m.id as movie_id,
                    m.title as movie,
                    m.duration,
                    m.genre,
                    m.age_rating,
                    h.id as hall_id,
                    h.hall_number as hall,
                    h.rows_count,
                    h.seats_per_row,
                    t.id as tariff_id,
                    t.tariff_name,
                    t.price
                FROM sessions s
                JOIN movies m ON s.movie_id = m.id
                JOIN halls h ON s.hall_id = h.id
                JOIN tariffs t ON s.tariff_id = t.id
                WHERE s.id = %s
            """, (session_id,))
            return self._fix_row(cur.fetchone())

    def add_session(self, movie_id, hall_id, session_date, start_time, end_time, tariff_id):
        """Добавление нового сеанса"""
        conn = self.get_connection()
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO sessions (movie_id, hall_id, session_date, start_time, end_time, tariff_id) 
                VALUES (%s, %s, %s, %s, %s, %s) 
                RETURNING id
            """, (movie_id, hall_id, session_date, start_time, end_time, tariff_id))
            conn.commit()
            return cur.fetchone()['id']

    def delete_session(self, session_id):
        """Удаление сеанса"""
        conn = self.get_connection()
        with conn.cursor() as cur:
            cur.execute("DELETE FROM sessions WHERE id = %s", (session_id,))
            conn.commit()
            return cur.rowcount > 0

    # ========== ТАРИФЫ ==========
    def get_tariffs(self):
        """Получение всех тарифов"""
        conn = self.get_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT id, tariff_name as name, price FROM tariffs ORDER BY id")
            return self._fix_rows(cur.fetchall())

    def add_tariff(self, name, price):
        """Добавление нового тарифа"""
        conn = self.get_connection()
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO tariffs (tariff_name, price) 
                VALUES (%s, %s) 
                RETURNING id
            """, (name, price))
            conn.commit()
            return cur.fetchone()['id']

    def delete_tariff(self, tariff_id):
        """Удаление тарифа"""
        conn = self.get_connection()
        with conn.cursor() as cur:
            cur.execute("DELETE FROM tariffs WHERE id = %s", (tariff_id,))
            conn.commit()
            return cur.rowcount > 0

    # ========== МЕСТА ==========
    def get_seats(self, hall_id):
        """Получение всех мест в зале"""
        conn = self.get_connection()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, row_number as row, seat_number as seat, seat_type as type 
                FROM seats 
                WHERE hall_id = %s 
                ORDER BY row_number, seat_number
            """, (hall_id,))
            return self._fix_rows(cur.fetchall())

    # ========== БИЛЕТЫ ==========
    def get_sold_tickets(self, session_id):
        """Получение проданных билетов на сеанс"""
        conn = self.get_connection()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    t.id, 
                    t.customer_name, 
                    t.price, 
                    t.payment_method,
                    s.row_number, 
                    s.seat_number, 
                    s.seat_type,
                    s.id as seat_id
                FROM tickets t
                JOIN seats s ON t.seat_id = s.id
                WHERE t.session_id = %s AND t.is_returned = false
            """, (session_id,))
            return self._fix_rows(cur.fetchall())

    def buy_ticket(self, session_id, seat_id, customer_name, price, payment_method):
        """Покупка билета"""
        conn = self.get_connection()
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO tickets (session_id, seat_id, customer_name, price, payment_method, is_returned) 
                VALUES (%s, %s, %s, %s, %s, false) 
                RETURNING id
            """, (session_id, seat_id, customer_name, price, payment_method))
            conn.commit()
            return cur.fetchone()['id']

    def return_ticket(self, ticket_id):
        """Возврат билета"""
        conn = self.get_connection()
        with conn.cursor() as cur:
            cur.execute("UPDATE tickets SET is_returned = true WHERE id = %s", (ticket_id,))
            conn.commit()
            return cur.rowcount > 0

    # ========== ПОЛЬЗОВАТЕЛИ ==========
    def get_users(self):
        """Получение всех пользователей"""
        conn = self.get_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT id, username, role, full_name FROM users ORDER BY id")
            return self._fix_rows(cur.fetchall())

    def authenticate(self, username, password):
        """Авторизация пользователя"""
        conn = self.get_connection()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, username, role, full_name 
                FROM users 
                WHERE username = %s AND password = %s
            """, (username, password))
            return self._fix_row(cur.fetchone())

    def add_user(self, username, password, role, full_name):
        """Добавление нового пользователя"""
        conn = self.get_connection()
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO users (username, password, role, full_name) 
                VALUES (%s, %s, %s, %s) 
                RETURNING id
            """, (username, password, role, full_name))
            conn.commit()
            return cur.fetchone()['id']

    def delete_user(self, user_id):
        """Удаление пользователя"""
        conn = self.get_connection()
        with conn.cursor() as cur:
            cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
            conn.commit()
            return cur.rowcount > 0


# Создаем глобальный экземпляр БД
db = Database()

# Принудительно проверяем подключение при запуске
try:
    conn = db.get_connection()
    logger.info("✅ База данных готова к работе")
except Exception as e:
    logger.error(f"❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось подключиться к БД: {e}")
    logger.error("Проверьте параметры подключения в database.py")
    raise