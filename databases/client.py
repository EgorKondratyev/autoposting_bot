# Таблицы нормализованы до NF1
import sqlite3

from databases.auth_data import PATH
from log.create_logger import logger


class UsersDB:
    def __init__(self):
        try:
            self.__base = sqlite3.connect(PATH)
            self.__cur = self.__base.cursor()
            self.__cur.execute('''CREATE TABLE IF NOT EXISTS users(
                user_id BIGINT
            )''')
            self.__base.commit()
        except Exception as ex:
            logger.warning(f'An error occurred with database "users"\n'
                           f'{ex}')

    def exists_user(self, user_id: int) -> bool:
        self.__cur.execute('SELECT user_id '
                           'FROM users '
                           'WHERE user_id = ?',
                           (user_id,))
        return bool(len(self.__cur.fetchmany(1)))

    def add_user(self, user_id: int):
        self.__cur.execute('INSERT INTO users(user_id) '
                           'VALUES(?)',
                           (user_id, ))
        self.__base.commit()

    def __del__(self):
        self.__cur.close()
        self.__base.close()


class ChannelDB:
    def __init__(self):
        try:
            self.__base = sqlite3.connect(PATH)
            self.__cur = self.__base.cursor()
            self.__cur.execute('''CREATE TABLE IF NOT EXISTS channels(
                user_id BIGINT,
                channel_id BIGINT,
                channel_name TEXT
            )''')
            self.__base.commit()
        except Exception as ex:
            logger.warning(f'An error occurred with table channel_db\n'
                           f'{ex}')

    def exists_user(self, user_id: int, channel_id: int) -> bool:
        self.__cur.execute('SELECT user_id '
                           'FROM channels '
                           'WHERE user_id = ? and channel_id = ?',
                           (user_id, channel_id))
        return bool(len(self.__cur.fetchmany(1)))

    def add_user(self, user_id: int, channel_id: int, channel_name: str):
        self.__cur.execute('INSERT INTO channels(user_id, channel_id, channel_name) '
                           'VALUES(?, ?, ?)',
                           (user_id, channel_id, channel_name))
        self.__base.commit()

    def get_channels_by_user_id(self, user_id: int) -> list:
        """
        Получение всех групп текущего пользователя
        :param user_id:
        :return:
        """
        self.__cur.execute('SELECT channel_id, channel_name '
                           'FROM channels '
                           'WHERE user_id = ?',
                           (user_id, ))
        return self.__cur.fetchall()

    def get_name_channel(self, channel_id: int):
        self.__cur.execute('SELECT channel_name '
                           'FROM channels '
                           'WHERE channel_id = ?',
                           (channel_id, ))
        channels_names = self.__cur.fetchall()
        if channels_names:
            return channels_names[0][0]
        return 0

    def delete_channel(self, user_id: int, channel_id: int):
        self.__cur.execute('DELETE FROM channels '
                           'WHERE user_id = ? and channel_id = ?',
                           (user_id, channel_id))
        self.__base.commit()

    def __del__(self):
        self.__cur.close()
        self.__base.close()


class PostDB:
    """
    Таблица предназначенная для сохранения данных о конкретном посте для последующей его отмены по тегу
    """
    # context - текст поста, если таковой имеется
    def __init__(self):
        try:
            self.__base = sqlite3.connect(PATH)
            self.__cur = self.__base.cursor()
            self.__cur.execute('''CREATE TABLE IF NOT EXISTS posts(
                user_id BIGINT,
                post_tag TEXT,
                context TEXT
            )''')
        except Exception as ex:
            logger.warning(f'An error occurred with table post_db\n'
                           f'{ex}')

    def post_exists(self, user_id: int, tag: str) -> bool:
        self.__cur.execute('SELECT post_tag '
                           'FROM posts '
                           'WHERE user_id = ? and post_tag = ?',
                           (user_id, tag))
        return len(self.__cur.fetchmany(1)).__bool__()

    def post_add(self, user_id: int, tag: str, context: str):
        self.__cur.execute('INSERT INTO posts(user_id, post_tag, context) '
                           'VALUES(?, ?, ?)',
                           (user_id, tag, context))
        self.__base.commit()

    def post_del(self, user_id: int, tag: str):
        self.__cur.execute('DELETE FROM posts '
                           'WHERE user_id = ? and post_tag = ?',
                           (user_id, tag))
        self.__base.commit()

    def get_posts_tags_by_user_id(self, user_id: int) -> list:
        self.__cur.execute('SELECT post_tag '
                           'FROM posts '
                           'WHERE user_id = ?',
                           (user_id, ))
        return self.__cur.fetchall()

    def get_context_by_tag(self, user_id: int, tag: str) -> str:
        self.__cur.execute('SELECT context '
                           'FROM posts '
                           'WHERE post_tag = ? and user_id = ?',
                           (tag, user_id))
        return self.__cur.fetchall()[0][0]

    def clear_table(self):
        self.__cur.execute('DELETE FROM posts')
        self.__base.commit()

    def __del__(self):
        self.__cur.close()
        self.__base.close()


class DonorPostDB:
    # unique_id_media_file - уникальный ID файла, который мы получаем из message.file.file_unique_id
    # group_media_id - ID группировки файлов
    def __init__(self):
        try:
            self.__base = sqlite3.connect(PATH)
            self.__cur = self.__base.cursor()
            self.__cur.execute('''CREATE TABLE IF NOT EXISTS donor_posts(
                pk INTEGER PRIMARY KEY AUTOINCREMENT, 
                tag TEXT,
                photo_id TEXT,
                video_id TEXT,
                animation_id TEXT,
                content TEXT,
                video_note TEXT,
                unique_id_media_file TEXT,
                user_id BIGINT,
                group_media_id TEXT
            )''')
            self.__base.commit()
        except Exception as ex:
            logger.warning(f'An error occurred with table post_db\n'
                           f'{ex}')

    def add_post(self, tag: str, user_id: int, photo_id: str = None, video_id: str = None, animation_id: str = None,
                 content: str = None, unique_id_media_file: str = None, video_note: str = None,
                 group_media_id: str = None):
        self.__cur.execute('INSERT INTO '
                           'donor_posts(tag, photo_id, '
                           'video_id, animation_id, '
                           'content, unique_id_media_file, '
                           'video_note, user_id, group_media_id) '
                           'VALUES '
                           '(?, ?, ?, ?, ?, ?, ?, ?, ?)',
                           (tag, photo_id, video_id, animation_id, content, unique_id_media_file, video_note,
                            user_id, group_media_id))
        self.__base.commit()

    def get_posts_by_tag(self, tag: str):
        self.__cur.execute('SELECT * '
                           'FROM donor_posts '
                           'WHERE tag = ?',
                           (tag, ))
        return self.__cur.fetchall()

    def get_tags_by_user_id(self, user_id: int) -> list:
        self.__cur.execute('SELECT tag '
                           'FROM donor_posts '
                           'WHERE user_id = ?',
                           (user_id, ))
        return self.__cur.fetchall()

    def get_posts_by_grop_media_id(self, group_media_id: int) -> list:
        self.__cur.execute('SELECT * '
                           'FROM donor_posts '
                           'WHERE group_media_id = ?',
                           (group_media_id, ))
        return self.__cur.fetchall()

    def del_post_by_unique_id_file(self, unique_id_media_file: str):
        self.__cur.execute('DELETE FROM donor_posts '
                           'WHERE unique_id_media_file = ?',
                           (unique_id_media_file, ))
        self.__base.commit()

    def del_post_by_content(self, content: str):
        self.__cur.execute('DELETE FROM donor_posts '
                           'WHERE content = ?',
                           (content,))
        self.__base.commit()

    def del_post_by_tag(self, tag: str):
        self.__cur.execute('DELETE FROM donor_posts '
                           'WHERE tag = ?',
                           (tag, ))
        self.__base.commit()

    def del_post_by_pk(self, pk: int):
        self.__cur.execute('DELETE FROM donor_posts '
                           'WHERE pk = ?',
                           (pk, ))
        self.__base.commit()

    def del_post_by_group_media_id(self, group_media_id: int):
        self.__cur.execute('DELETE FROM donor_posts '
                           'WHERE group_media_id = ?',
                           (group_media_id, ))
        self.__base.commit()

    def clear_table(self):
        self.__cur.execute('DELETE FROM donor_posts')
        self.__base.commit()

    def __del__(self):
        self.__cur.close()
        self.__base.close()


class IndividualPostDB:
    def __init__(self):
        try:
            self.__base = sqlite3.connect(PATH)
            self.__cur = self.__base.cursor()
            self.__cur.execute('''CREATE TABLE IF NOT EXISTS individual_posts(
                tag TEXT,
                photo_id TEXT,
                video_id TEXT,
                content TEXT
            )''')
            self.__base.commit()
        except Exception as ex:
            logger.warning(f'An error occurred with table individual post\n'
                           f'{ex}')

    def exists_tag(self, tag: str) -> bool:
        self.__cur.execute('SELECT tag '
                           'FROM individual_posts '
                           'WHERE tag = ?',
                           (tag, ))
        return bool(len(self.__cur.fetchall()))

    def add_post(self, tag: str, photo_id: str = None, video_id: str = None, content: str = None):
        self.__cur.execute('INSERT INTO individual_posts(tag, photo_id, video_id, content) '
                           'VALUES(?, ?, ?, ?)',
                           (tag, photo_id, video_id, content))
        self.__base.commit()

    def get_post_by_tag(self, tag: str) -> list:
        self.__cur.execute('SELECT * '
                           'FROM individual_posts '
                           'WHERE tag = ?',
                           (tag, ))
        return self.__cur.fetchall()

    def del_post_by_tag(self, tag: str):
        self.__cur.execute('DELETE FROM individual_posts '
                           'WHERE tag = ?',
                           (tag, ))
        self.__base.commit()

    def __del__(self):
        self.__cur.close()
        self.__base.close()
