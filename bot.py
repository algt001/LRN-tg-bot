import asyncio
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import InlineKeyboardBuilder

# ----------------- НАСТРОЙКИ -----------------
BOT_TOKEN = "9020379171:AAFuidGp2h43xceNfsnIiJ5yzOjV4_JUPvA"
ADMIN_GROUP_ID = -1004402157688
FLOOD_CHAT_LINK = "https://t.me/+DdF7WWdWwjoxODVi"
# ---------------------------------------------

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

class Form(StatesGroup):
    photo = State()
    role = State()
    username = State()

@dp.message(Command("start"))
async def start_cmd(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Привет! Начнем заполнение анкеты.\nОтправь фото роли (персонажа):")
    await state.set_state(Form.photo)

@dp.message(Form.photo, F.photo)
async def process_photo(message: types.Message, state: FSMContext):
    await state.update_data(photo=message.photo[-1].file_id)
    await message.answer("Отлично! Теперь напиши саму роль (описание):")
    await state.set_state(Form.role)

@dp.message(Form.photo)
async def process_photo_invalid(message: types.Message):
    await message.answer("Пожалуйста, прикрепи именно фотографию.")

@dp.message(Form.role)
async def process_role(message: types.Message, state: FSMContext):
    await state.update_data(role=message.text)
    
    user_name_text = f"@{message.from_user.username}" if message.from_user.username else "Не указан"
    await message.answer(
        f"Укажи свой юзернейм в Telegram (например, @username).\n"
        f"Твой текущий юзернейм: {user_name_text}\n"
        f"Если всё верно, просто отправь его сообщением:"
    )
    await state.set_state(Form.username)

@dp.message(Form.username)
async def process_username(message: types.Message, state: FSMContext):
    await state.update_data(username=message.text)
    data = await state.get_data()
    
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Одобрить", callback_data=f"approve_{message.from_user.id}")
    builder.button(text="❌ Отклонить", callback_data=f"reject_{message.from_user.id}")
    builder.adjust(2)
    
    caption = (
        f"📥 **Новая анкета!**\n\n"
        f"**Роль:** {data['role']}\n"
        f"**Юзернейм:** {data['username']}\n"
        f"**Отправитель:** [{message.from_user.full_name}](tg://user?id={message.from_user.id})"
    )
    
    await bot.send_photo(
        chat_id=ADMIN_GROUP_ID,
        photo=data['photo'],
        caption=caption,
        parse_mode="Markdown",
        reply_markup=builder.as_markup()
    )
    
    await message.answer("Спасибо! Твоя анкета отправлена на модерацию. Ожидай решения.")
    await state.clear()

@dp.callback_query(F.data.startswith("approve_"))
async def approve_anketa(callback: types.CallbackQuery):
    user_id = int(callback.data.split("_")[1])
    
    try:
        await bot.send_message(
            chat_id=user_id,
            text=f"🎉 Поздравляем! Твоя анкета одобрена.\nВот ссылка на наш флуд-чат: {FLOOD_CHAT_LINK}"
        )
        await callback.message.edit_caption(
            caption=f"{callback.message.caption}\n\n✅ **ОДОБРЕНО** (модератор: @{callback.from_user.username or 'админ'})",
            reply_markup=None
        )
    except Exception:
        await callback.answer("Не удалось отправить сообщение пользователю.", show_alert=True)

@dp.callback_query(F.data.startswith("reject_"))
async def reject_anketa(callback: types.CallbackQuery):
    user_id = int(callback.data.split("_")[1])
    
    try:
        await bot.send_message(
            chat_id=user_id,
            text="К сожалению, твоя анкета была отклонена модератором."
        )
        await callback.message.edit_caption(
            caption=f"{callback.message.caption}\n\n❌ **ОТКЛОНЕНО** (модератор: @{callback.from_user.username or 'админ'})",
            reply_markup=None
        )
    except Exception:
        await callback.answer("Не удалось отправить сообщение пользователю.", show_alert=True)

async def main():
    print("Бот запущен и готов к работе!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
