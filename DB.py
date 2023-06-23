import datetime
import sqlite3


class DataBase:
    def __init__(self, db_file):
        self.conn = sqlite3.connect(db_file)
        self.cursor = self.conn.cursor()
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS face_encodings
                            (id INTEGER PRIMARY KEY AUTOINCREMENT,
                             encoding TEXT,
                             source_url TEXT,
                             image_url TEXT)''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                            id            INTEGER PRIMARY KEY NOT NULL UNIQUE,
                            telegram_id   INTEGER NOT NULL UNIQUE,
                            name          TEXT,
                            nickname      TEXT,
                            date_of_birth TEXT,
                            status        INTEGER DEFAULT (0) 
                        )''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS users_requests (
                            id      INTEGER PRIMARY KEY UNIQUE NOT NULL,
                            user_id INTEGER REFERENCES users (id) NOT NULL,
                            date    TEXT    NOT NULL,
                            count   NUMERIC NOT NULL DEFAULT (1) 
                        )''')
        self.conn.commit()

    def add_face(self, encoding_str: str, source_url=None, save_path=None) -> (bool, str):
        ''' add the encoded face to the database as a string.
                encoding_str - encoded string
                source_url - source address str | None
                save_path - path where the image is saved '''
        try:
            with self.conn:
                self.cursor.execute(
                    'INSERT INTO face_encodings (encoding, source_url, image_url) VALUES (?, ?, ?)',
                    (encoding_str, source_url, save_path))
            return True, ""
        except Exception as ex:
            return False, f"Ошибка добавления в базу ({ex})"

    def get_faces(self, limit=-1) -> (bool, list | str):
        ''' get a list consisting of id and encoding from the database.
            limit - limit output '''
        try:
            with self.conn:
                cur = self.cursor.execute('SELECT id, encoding FROM face_encodings LIMIT ?', (limit,))
                res = cur.fetchall()
            return True, res
        except Exception as ex:
            return False, f"Ошибка обращения к базе ({ex})"

    def add_user(self, tg_id: int, name: str, nickname: str, date_of_birth: str, status=0) -> (bool, str):
        ''' add a user to the database
            tg_id - telegram identifier
            name - first_name
            nickname - username telegram
            date_of_birth - date of birth (str)
            status - 0-regular user, 1-vip, 2-admin, -1-ban'''
        try:
            with self.conn:
                cur = self.cursor.execute(
                    'INSERT INTO users (telegram_id, name, nickname, date_of_birth, status) VALUES (?, ?, ?, ?, ?)',
                    (tg_id, name, nickname, date_of_birth, status))
            return True, ""
        except Exception as ex:
            return False, f"Ошибка обращения к базе ({ex})"

    def get_user(self, user_id: int) -> (bool, list | str):
        ''' get a user from the database by telegram ID '''
        try:
            with self.conn:
                cur = self.cursor.execute('SELECT * FROM users WHERE telegram_id = ?', (user_id,))
                res = cur.fetchone()
            return True, res
        except Exception as ex:
            return False, f"Ошибка обращения к базе ({ex})"

    def del_user(self, user_id: int) -> (bool, str):
        ''' delete a user from the database by telegram ID '''
        try:
            with self.conn:
                self.cursor.execute('DELETE FROM users WHERE telegram_id = ?', (user_id,))
            return True, ""
        except Exception as ex:
            return False, f"Ошибка обращения к базе ({ex})"

    def add_request(self, user_id: int) -> (bool, str):
        ''' increase the user request counter (if there is no record, then create one)
                user_id - telegram ID '''
        try:
            count = self.get_count_requests(user_id)
            if count[1] == 0:
                with self.conn:
                    cur = self.cursor.execute(
                        'INSERT INTO users_requests (user_id, date) VALUES (?, ?)',
                        (user_id, datetime.date.today()), )
            else:
                with self.conn:
                    cur = self.cursor.execute(
                        'UPDATE users_requests SET count = count+1 WHERE user_id = ? AND date = ?',
                        (user_id, datetime.date.today()), )
            return True, ""
        except Exception as ex:
            print(ex)
            return False, f"Ошибка обращения к базе ({ex})"

    def get_count_requests(self, user_id: int) -> (bool, list | str):
        ''' get the number of user requests for that day
                user_id - telegram ID '''
        try:
            with self.conn:
                cur = self.cursor.execute('SELECT count FROM users_requests WHERE user_id = ? AND date = ?',
                                          (user_id, datetime.date.today(),))
                res = cur.fetchone()
                if res is None:
                    res = 0
                else:
                    res = res[0]
                return True, res
        except Exception as ex:
            return False, f"Ошибка обращения к базе ({ex})"

    def get_face_encodings_data_by_id(self, id_list: list) -> (bool, list | str):
        ''' get the data of encoded persons from the database by the list of their ids
                id_list - a list of ids '''
        if len(id_list) == 0:
            return False, "Список пуст"
        try:
            with self.conn:
                query = 'SELECT source_url, image_url FROM face_encodings WHERE id in (' + ','.join(
                    (str(n) for n in id_list)) + ')'
                cur = self.cursor.execute(query)
                res = cur.fetchall()
            return True, res
        except Exception as ex:
            return False, f"Ошибка обращения к базе ({ex})"
