# Таблицы нормализованы до NF1
import sqlite3
import traceback

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
    """
    Сущность, содержащая каналы конкретного человека
    """
    def __init__(self):
        try:
            self.__base = sqlite3.connect(PATH)
            self.__cur = self.__base.cursor()
            self.__cur.execute('''CREATE TABLE IF NOT EXISTS channels(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
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

    def get_id_by_channel_id(self, user_id: int, channel_id: int):
        self.__cur.execute('SELECT id '
                           'FROM channels '
                           'WHERE user_id = ? and channel_id = ?',
                           (user_id, channel_id))
        result = self.__cur.fetchall()
        if result:
            return result[0][0]
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

    def posts_del_by_channel_id(self, user_id: int, channel_id: int):
        self.__cur.execute('DELETE FROM posts '
                           'WHERE user_id = ? and channel_id = ?',
                           (user_id, channel_id))
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


class CheckDonorPostDB:
    """
    Сущность, которая будет содержать в себе те посты (если быть точнее pk donor_posts), которые не надо опубликовывать
    в каналы, которые определит сам user (наполнение данной сущности происходит в модуле cancel_posts_in_channel)
    """
    def __init__(self):
        try:
            self.__base = sqlite3.connect(PATH)
            self.__cur = self.__base.cursor()
            self.__cur.execute('''CREATE TABLE IF NOT EXISTS check_donor_posts(
                pk_donor_post INTEGER,
                channel_id BIGINT,
                user_id BIGINT
            )''')
            self.__base.commit()
        except Exception as ex:
            logger.warning(f'An error occurred with table post_db\n'
                           f'{ex}')

    def add(self, user_id: int, channel_id: int, pk_donor_posts: int):
        """
        Добавление ограничения на публикацию поста в определенный канал
        :param user_id:
        :param channel_id:
        :param pk_donor_posts:
        :return:
        """
        self.__cur.execute('INSERT INTO check_donor_posts(user_id, channel_id, pk_donor_post) '
                           'VALUES(?, ?, ?)',
                           (user_id, channel_id, pk_donor_posts))
        self.__base.commit()

    def exists_pk(self, user_id: int, channel_id: int, pk: int):
        self.__cur.execute('SELECT pk_donor_post '
                           'FROM check_donor_posts '
                           'WHERE user_id = ? and channel_id = ? and pk_donor_post = ?',
                           (user_id, channel_id, pk))
        return bool(len(self.__cur.fetchall()))

    def get_all_pk_donor_post(self, user_id: int, channel_id: int):
        self.__cur.execute('SELECT pk_donor_post '
                           'FROM check_donor_posts '
                           'WHERE user_id = ? and channel_id = ?',
                           (user_id, channel_id))
        return self.__cur.fetchall()

    def del_pk(self, user_id: int, channel_id: int, pk: int):
        self.__cur.execute('DELETE FROM check_donor_posts '
                           'WHERE user_id = ? and channel_id = ? and pk_donor_post = ?',
                           (user_id, channel_id, pk))
        self.__base.commit()

    def clear_table(self):
        self.__cur.execute('DELETE FROM check_donor_posts')
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

    def add_post(self, tag: str, user_id: int, photo_id: str = None, video_id: str = None,
                 animation_id: str = None, content: str = None, unique_id_media_file: str = None,
                 video_note: str = None, group_media_id: str = None):
        """
        Добавление новой записи в текущую сущность.
        :param tag:
        :param user_id:
        :param photo_id:
        :param video_id:
        :param animation_id:
        :param content:
        :param unique_id_media_file:
        :param video_note:
        :param group_media_id:
        :return:
        """
        # Добавляем все данные о посте в сущность donor_posts
        self.__cur.execute('INSERT INTO '
                           'donor_posts(tag, photo_id, '
                           'video_id, animation_id, '
                           'content, unique_id_media_file, '
                           'video_note, user_id, group_media_id) '
                           'VALUES '
                           '(?, ?, ?, ?, ?, ?, ?, ?, ?)',
                           (tag, photo_id, video_id, animation_id, content, unique_id_media_file, video_note,
                            user_id, group_media_id))
        # Связываем данный пост с каналами, в которые этот пост будет опубликовываться
        self.__base.commit()

    def get_all_pk_by_user_id(self, user_id: int):
        self.__cur.execute('SELECT pk '
                           'FROM donor_posts '
                           'WHERE user_id = ?',
                           (user_id, ))
        return self.__cur.fetchall()

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

    def del_post_by_channel_id(self, channel_id: int):
        self.__cur.execute('DELETE FROM donor_posts '
                           'WHERE channel_id = ?',
                           (channel_id, ))
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



# class PostsTags:
#     """
#     Сущность, связывающая таблицу donor_posts (по id) и channels (по id) отношением ManyToMany
#     Данная промежуточная таблица создана с целью удаления постов из определенного канала
#     """
#     # donor_post_id - уникальный идентификатор сущности donor_posts (из составного ключа самый удобный
#     # был donor_post_id ;) )
#     # table_channel_id - уникальный идентификатор сущности channels (но надо учитывать, что это не ID канала,
#     # а именно ID сущности channels), telegram_channel_id - ID канала из телеграмма
#     def __init__(self):
#         try:
#             self.__base = sqlite3.connect(PATH)
#             self.__cur = self.__base.cursor()
#             self.__cur.execute('''CREATE TABLE IF NOT EXISTS posts_tags(
#                 donor_post_id INTEGER,
#                 table_channel_id INTEGER
#             )''')
#             self.__base.commit()
#         except Exception as ex:
#             logger.warning(f'An error occurred with table post_db\n'
#                            f'{ex}')
#
#     def get_tags_from_channel(self, telegram_channel_id: int, user_id: int):
#         """
#         Получение всех тегов для постов конкретного пользователя, которые привязаны к конкретному каналу.
#         Иначе говоря получение только тех тегов, которые будут поститься в канал telegram_channel_id.
#         :param user_id:
#         :param telegram_channel_id: Канал, по которому будут браться теги.
#         :return:
#         """
#         try:
#             self.__cur.execute('SELECT DISTINCT dp.pk FROM channels ch '
#                                'INNER JOIN posts_tags pt ON pt.table_channel_id=ch.id '
#                                'INNER JOIN donor_posts dp ON dp.pk=pt.donor_post_id '
#                                'WHERE ch.channel_id = ? and ch.user_id = ?',
#                                (telegram_channel_id, user_id))
#         except Exception:
#             traceback.print_exc()
#         posts_pk = self.__cur.fetchall()
#         return posts_pk
#
#     def add(self, table_channel_id: int, donor_post_id: int):
#         """
#         Добавить в текущую сущность связь
#         :param table_channel_id: ID записи из сущности channels
#         :param donor_post_id: id из сущности donor_post
#         :return:
#         """
#         try:
#             self.__cur.execute('INSERT INTO posts_tags(table_channel_id, donor_post_id) '
#                                'VALUES(?, ?)',
#                                (table_channel_id, donor_post_id))
#         except Exception:
#             traceback.print_exc()
#
#     def clear_table(self):
#         self.__cur.execute('DELETE FROM posts_tags')
#         self.__base.commit()
#
#     def __del__(self):
#         self.__cur.close()
#         self.__base.close()
