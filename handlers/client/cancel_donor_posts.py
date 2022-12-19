import traceback

from aiogram.types import Message, CallbackQuery
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher import FSMContext

from create_bot.bot import dp
from databases.client import DonorPostDB
from handlers.stop_fsm import create_keyboard_stop_fsm
from keyboards.inline.cancel_donor_posts import create_cancel_donor_posts_keyboard
from states.cancel_donor_posts import CancelDonorFSM
from utils.create_cron import msh


# @dp.callback_query_handler(Text(equals='start_cancel_donor_posts'))
async def get_posts(callback: CallbackQuery):
    await callback.answer()
    post_db = DonorPostDB()
    posts_all = post_db.get_tags_by_user_id(user_id=callback.from_user.id)
    if posts_all:
        try:
            amount_posts = len(posts_all)
            posts = list(set(posts_all))
            posts_menu = await create_cancel_donor_posts_keyboard(posts)
            await callback.message.answer(f'<b>Количество постов в очереди:</b> {amount_posts}\n\n'
                                          f'<i>Все посты, которые ожидают публикации</i> (указаны теги в качестве имён): ',
                                          reply_markup=posts_menu,
                                          parse_mode='html')
            await CancelDonorFSM.get_post.set()
        except Exception:
            traceback.print_exc()
    else:
        await callback.message.answer('На данный момент не установлено ни одного поста')


# @dp.callback_query_handler(Text(startswith='cancel_donor_'))
async def confirm_cancel_job(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    job_tag = callback.data[len('cancel_donor_'):]
    async with state.proxy() as data:
        data['tag'] = job_tag
    post_db = DonorPostDB()
    posts = post_db.get_posts_by_tag(tag=job_tag)
    amount_posts = len(posts)
    await callback.message.answer(f'Количество постов в данном теге: <b>{amount_posts}</b>\n\n'
                                  f'Для удаления данных постов напиши <code>DELETE JOB</code>: ',
                                  reply_markup=create_keyboard_stop_fsm(), parse_mode='html')
    await CancelDonorFSM.confirm.set()


# @dp.message_handler(state=CancelDonorFSM.confirm)
async def cancel_donor(message: Message, state: FSMContext):
    if message.text == 'DELETE JOB':
        async with state.proxy() as data:
            job_tag = data['tag']
        post_donor_db = DonorPostDB()
        post_donor_db.del_post_by_tag(tag=job_tag)
        await state.finish()
        await message.answer('Задача успешно снята с очереди')
        msh.del_job(job_name=job_tag)
    else:
        await state.finish()
        await message.answer('Операция остановлена')


def register_handlers_cancel_posts_donor():
    dp.register_callback_query_handler(get_posts, Text(equals='start_cancel_donor_posts'))
    dp.register_callback_query_handler(confirm_cancel_job, Text(startswith='cancel_donor_'),
                                       state=CancelDonorFSM.get_post)
    dp.register_message_handler(cancel_donor, state=CancelDonorFSM.confirm)
