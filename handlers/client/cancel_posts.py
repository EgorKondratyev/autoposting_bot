from aiogram.types import Message, CallbackQuery
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher import FSMContext

from create_bot.bot import dp
from databases.client import PostDB
from handlers.stop_fsm import create_keyboard_stop_fsm
from keyboards.inline.cancel_posts import create_cancel_posts_keyboard
from states.cancel_posts import CancelPostFSM
from utils.create_cron import msh


# @dp.callback_query_handler(Text(equals='start_cancel_posts'))
async def get_posts(callback: CallbackQuery):
    await callback.answer()
    post_db = PostDB()
    posts = post_db.get_posts_tags_by_user_id(user_id=callback.from_user.id)
    if posts:
        posts_menu = await create_cancel_posts_keyboard(posts)
        await callback.message.answer(f'<b>Количество постов в очереди:</b> {len(posts)}\n\n'
                                      f'<i>Все посты, которые ожидают публикации</i> (указаны теги в качестве имён): ',
                                      reply_markup=posts_menu, parse_mode='html')
        await CancelPostFSM.get_post.set()

    else:
        await callback.message.answer('На данный момент не установлено ни одного поста')


# @dp.callback_query_handler(Text(startswith='cancel_job_'))
async def confirm_cancel_job(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    job_tag = callback.data[len('cancel_job_'):]
    async with state.proxy() as data:
        data['tag'] = job_tag
    post_db = PostDB()
    context_post = post_db.get_context_by_tag(user_id=callback.from_user.id, tag=job_tag)
    if context_post:
        await callback.message.answer(f'<b>Текст поста:</b> \n\n'
                                      f'{context_post}', parse_mode='html')
    await callback.message.answer('Для удаления данной публикации напиши <code>DELETE JOB</code>: ',
                                  reply_markup=create_keyboard_stop_fsm(), parse_mode='html')
    await CancelPostFSM.confirm.set()


# @dp.message_handler(state=CancelPostFSM.confirm)
async def cancel_post(message: Message, state: FSMContext):
    if message.text.upper() == 'DELETE JOB':
        async with state.proxy() as data:
            job_tag = data['tag']
        msh.del_job(job_tag)
        post_db = PostDB()
        if post_db.post_exists(user_id=message.from_user.id, tag=job_tag):
            post_db.post_del(user_id=message.from_user.id, tag=job_tag)
        await state.finish()
        await message.answer('Задача успешно снята с очереди')
    else:
        await state.finish()
        await message.answer('Операция остановлена')


def register_handlers_cancel_posts():
    dp.register_callback_query_handler(get_posts, Text(equals='start_cancel_posts'))
    dp.register_callback_query_handler(confirm_cancel_job, Text(startswith='cancel_job_'), state=CancelPostFSM.get_post)
    dp.register_message_handler(cancel_post, state=CancelPostFSM.confirm)
