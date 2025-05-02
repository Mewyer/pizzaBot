import asyncio
import logging
import sys
from os import getenv

from aiogram import Bot, Dispatcher, html, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import FSInputFile
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import CommandObject
from aiogram.utils.keyboard import InlineKeyboardBuilder

class AdminStates(StatesGroup):
    WAITING_ACTION = State()
    WAITING_NEW_PIZZA_NAME = State()
    WAITING_NEW_PIZZA_DESC = State()
    WAITING_NEW_PIZZA_PHOTO = State()
    WAITING_PIZZA_TO_REMOVE = State()


class OrderStates(StatesGroup):
    WAITING_ADDRESS = State()  
    WAITING_PHONE = State()   
    WAITING_COMMENT = State() 
    WAITING_SIZE = State()    

user_carts = {}  

ADMIN_IDS = []
orders_db={}

pizza_info = {
    "m1": {
        "name": "Индейка с овощами гриль",
        "description": """Состав начинки:
Пастрами из индейки, овощи гриль, кубики брынзы, моцарелла, фирменный томатный соус.
Тесто как обычно: мука в/с, вода, масло подсолнечное, сахар, соль, дрожжи."""
    },
    "m2": {
        "name": "Додо Микс",
        "description": """Додо Микс — наша фирменная пицца, которая собрала в себе сразу 4 любимых вкуса: 
Песто, Ветчина и сыр, Карбонара и Четыре сыра."""
    },
    "m3": {
        "name": "Овощи и грибы",
        "description": """Название: Овощи и грибы
Состав: Шампиньоны , томаты , сладкий перец , красный лук , кубики брынзы , моцарелла, фирменный томатный соус, итальянские травы"""
    },
    "m4": {
        "name": "колбаски барбекю",
         "description": """Состав: 30 см, традиционное тесто 30, 570 г
Острые колбаски чоризо 
, соус барбекю, томаты , красный лук , моцарелла, фирменный томатный соус"""
    },
    "m5": {
        "name": "Супермясная",
        "description": "Цыпленок, митболы из говядины, пикантная пепперони, томатный соус, острая чоризо, моцарелла, бекон"
    },
    "m6": {
        "name": "Двойная пеперони",
        "desctiption": """30 см, традиционное тесто 30, 620 г
Двойная порция пикантной пепперони 
, увеличенная порция моцареллы, фирменный томатный соус"""
    }
}

dp = Dispatcher()

admin_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Просмотр заказов", callback_data="view_orders")],
        [InlineKeyboardButton(text="Добавить пиццу", callback_data="add_pizza")],
        [InlineKeyboardButton(text="Удалить пиццу", callback_data="remove_pizza")],
        [InlineKeyboardButton(text="Статистика", callback_data="stats")],
        [InlineKeyboardButton(text="Выход", callback_data="admin_exit")]
    ]
)


pay_menu=InlineKeyboardMarkup(
        inline_keyboard=
        [
            [InlineKeyboardButton(text="Наличными", callback_data="paid")],
            [InlineKeyboardButton(text="Другое", callback_data="buying")]
        ]
    )

buy_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Добавить в корзину", callback_data="add_to_cart"),
         InlineKeyboardButton(text="Купить на сайте", url="https://dodopizza.ru/moscow")],
        [InlineKeyboardButton(text="Назад", callback_data="menu")]

    ]
)

pizzas_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Назад", callback_data="menu"),
         InlineKeyboardButton(text="Зазакать", callback_data="buy")]
    ]
)

cart_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Очистить корзину", callback_data="clear_cart")],
        [InlineKeyboardButton(text="Заказать", callback_data="order")],
        [InlineKeyboardButton(text="Назад", callback_data="menu")]
    ]
)

in_kb1= InlineKeyboardMarkup(
    inline_keyboard=[
        [
        InlineKeyboardButton(text="Индейка с овощами гриль", callback_data="m1"),
         InlineKeyboardButton(text="Додо микс", callback_data="m2")],
        [
        InlineKeyboardButton(text="Овощи и грибы", callback_data="m3"),
        InlineKeyboardButton(text="колбаски барбекю", callback_data="m4")
        ],
        [
        InlineKeyboardButton(text="Супермясная", callback_data="m5"),
        InlineKeyboardButton(text="Двойная пеперони", callback_data="m6")
        ]
    ]
)

rep_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Заказать пиццу🍕"), 
         KeyboardButton(text="Корзина🗑️")]
    ],
    resize_keyboard=True
)

buying_menu_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="СБП", callback_data="paid")],
        [InlineKeyboardButton(text="Криптовалюта", callback_data="paid")],
        [InlineKeyboardButton(text="Банковская карта", callback_data="paid")]
    ]
)


@dp.message(CommandStart())
async def start(message: Message) -> None:
    user_id = message.from_user.id
    user_carts[user_id] = []  
    await message.answer("""
Этот бот позволяет пользователям удобно заказывать пиццу прямо в Telegram. Включает в себя:
✅ Меню с выбором пицц (разные размеры, начинки)
✅ Корзину товаров (добавление, удаление, изменение количества)
✅ Оформление заказа (доставка или самовывоз, выбор адреса)
✅ Оплату (онлайн или наличными)
✅ Админ-панель (управление меню, заказами, статистикой)
""",
            reply_markup=rep_kb)

@dp.message(lambda message: message.text == "Заказать пиццу🍕")
async def menu(message: Message) -> None:
    await message.answer_photo(
        photo=FSInputFile("assets/menu.jpg"),
        caption=
("""
Меню (Было взято часть меню ДоДопиццы)
Выберете ваш заказ:
1. Индейка с овощами гриль
2. Додо микс
3. Овощи и грибы
4. колбаски барбекю
5. Супермясная
6. Двойная пеперони
"""), 
        reply_markup=in_kb1
    )

@dp.message(lambda message: message.text == "Корзина🗑️")
async def show_cart(message: Message):
    user_id = message.from_user.id
    cart = user_carts.get(user_id, [])
    
    await message.delete()

    if not cart:
        await message.answer("Ваша корзина пуста")
        return
    
    cart_text = "Ваша корзина:\n\n"
    for item in cart:
        cart_text += f"🍕 {item['name']}\n"
    
    cart_text += f"\nВсего товаров: {len(cart)}"
    
    await message.answer(cart_text, reply_markup=cart_kb)

@dp.callback_query(lambda c: c.data == "clear_cart")
async def clear_cart(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user_carts[user_id] = []
    await callback.answer("Корзина очищена", show_alert=True)
    await callback.message.edit_text("Ваша корзина пуста")

@dp.callback_query(lambda c: c.data == "menu")
async def menu(callback: types.CallbackQuery):
    await callback.message.delete()

@dp.callback_query(lambda c: c.data == "buy")
async def buy_pizza_menu(callback: types.CallbackQuery):
    await callback.message.delete()
    await callback.message.answer(
        "Выберите способ покупки",
        reply_markup=buy_menu
    )

@dp.callback_query(lambda c: c.data == "add_to_cart")
async def add_to_cart(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    state_data = await state.get_data()
    
    if 'current_pizza' not in state_data:
        await callback.answer("Не удалось определить пиццу", show_alert=True)
        return
    
    pizza_id = state_data['current_pizza']
    if pizza_id not in pizza_info:
        await callback.answer("Информация о пицце не найдена", show_alert=True)
        return
    
    pizza = pizza_info[pizza_id]
    
    if user_id not in user_carts:
        user_carts[user_id] = []
    
    user_carts[user_id].append({
        "name": pizza['name'],
        "description": pizza['description']
    })
    
    await callback.answer(f"{pizza['name']} добавлена в корзину", show_alert=True)

@dp.callback_query(lambda с: с.data == "order")
async def start_order(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите адрес доставки:")
    await state.set_state(OrderStates.WAITING_ADDRESS)

@dp.message(OrderStates.WAITING_ADDRESS)
async def process_address(message: Message, state: FSMContext):
    await state.update_data(address=message.text)
    await message.answer("Теперь введите ваш телефон для связи:")
    await state.set_state(OrderStates.WAITING_PHONE)

@dp.message(OrderStates.WAITING_PHONE)
async def process_phone(message: Message, state: FSMContext):
    if not message.text.isdigit() or len(message.text) < 5:
        return await message.answer("Пожалуйста, введите корректный номер телефона")
    
    await state.update_data(phone=message.text)
    sizes = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Маленькая (25см)", callback_data="size_small")],
        [InlineKeyboardButton(text="Средняя (30см)", callback_data="size_medium")],
        [InlineKeyboardButton(text="Большая (35см)", callback_data="size_large")]
    ])
    await message.answer("Выберите размер пиццы:", reply_markup=sizes)
    await state.set_state(OrderStates.WAITING_SIZE)

@dp.callback_query(OrderStates.WAITING_SIZE, lambda c: c.data.startswith("size_"))
async def process_size(callback: types.CallbackQuery, state: FSMContext):
    size_map = {
        "size_small": "Маленькая (25см)",
        "size_medium": "Средняя (30см)",
        "size_large": "Большая (35см)"
    }
    size = size_map[callback.data]
    await state.update_data(size=size)
    
    await callback.message.edit_text(f"Выбран размер: {size}")
    await callback.message.answer("Добавьте комментарий к заказу (или нажмите /skip чтобы пропустить):")
    await state.set_state(OrderStates.WAITING_COMMENT)

@dp.message(OrderStates.WAITING_COMMENT)
async def process_comment(message: Message, state: FSMContext):
    await state.update_data(comment=message.text)
    await finish_order(message, state)

@dp.message(Command("skip"), OrderStates.WAITING_COMMENT)
async def skip_comment(message: Message, state: FSMContext):
    await state.update_data(comment="Без комментария")
    await finish_order(message, state)

async def finish_order(message: Message, state: FSMContext):
    data = await state.get_data()
    user_id = message.from_user.id
    await state.clear()
    
    # Формируем текст заказа
    order_id = len(orders_db) + 1
    orders_db[order_id] = {
        "user_id": user_id,
        "address": data['address'],
        "phone": data['phone'],
        "size": data['size'],
        "comment": data['comment'],
        "items": user_carts.get(user_id, [])
    }
    
    order_text = (
        "Ваш заказ:\n"
        f"Номер заказа: #{order_id}\n"
        f"Адрес: {data['address']}\n"
        f"Телефон: {data['phone']}\n"
        f"Размер: {data['size']}\n"
        f"Комментарий: {data['comment']}\n\n"
        "Спасибо за заказ!"
    )
    await message.answer(order_text, reply_markup=pay_menu)
    user_carts[user_id] = []

@dp.callback_query(lambda c: c.data == "buying")
async def buy_pizza(callback: types.CallbackQuery):
    await callback.message.delete()
    await callback.message.answer("""
Выберите способ оплаты:
""",
            reply_markup=buying_menu_kb
        )

@dp.callback_query(lambda c:  c.data == "paid")
async def thx_for_paid(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user_carts[user_id] = []
    await callback.message.delete()
    await callback.message.answer(
        """
Заказ оформлен успешно
Благодарим за покупку!
"""
    )

@dp.callback_query(lambda c: c.data == "m1")
async def m1(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(current_pizza="m1")
    await callback.answer()
    pizza = pizza_info["m1"]
    await callback.message.answer_photo(
        photo=FSInputFile("assets/m1.webp"),
        caption=f"Название: {pizza['name']}\n\n{pizza['description']}",
        reply_markup=pizzas_menu
    )

@dp.callback_query(lambda c: c.data == "m2")
async def m1(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(current_pizza="m2")
    await callback.answer()
    pizza = pizza_info["m2"]
    await callback.message.answer_photo(
        photo=FSInputFile("assets/m2.jpeg"),
        caption=f"Название: {pizza['name']}\n\n{pizza['description']}",
        reply_markup=pizzas_menu
    )

@dp.callback_query(lambda c: c.data == "m3")
async def m1(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(current_pizza="m3")
    await callback.answer()
    pizza = pizza_info["m3"]
    await callback.message.answer_photo(
        photo=FSInputFile("assets/m3.jpg"),
        caption=f"Название: {pizza['name']}\n\n{pizza['description']}",
        reply_markup=pizzas_menu
    )

@dp.callback_query(lambda c: c.data == "m4")
async def m1(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(current_pizza="m4")
    await callback.answer()
    pizza = pizza_info["m4"]
    await callback.message.answer_photo(
        photo=FSInputFile("assets/m4.jpg"),
        caption=f"Название: {pizza['name']}\n\n{pizza['description']}",
        reply_markup=pizzas_menu
    )

@dp.callback_query(lambda c: c.data == "m5")
async def m1(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(current_pizza="m5")
    await callback.answer()
    pizza = pizza_info["m5"]
    await callback.message.answer_photo(
        photo=FSInputFile("assets/m5.jpeg"),
        caption=f"Название: {pizza['name']}\n\n{pizza['description']}",
        reply_markup=pizzas_menu
    )
@dp.callback_query(lambda c: c.data == "m6")
async def m1(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(current_pizza="m6")
    await callback.answer()
    pizza = pizza_info["m6"]
    await callback.message.answer_photo(
        photo=FSInputFile("assets/m6.jpg"),
        caption=f"Название: {pizza['name']}\n\n{pizza['description']}",
        reply_markup=pizzas_menu
    )

# Админ панель

@dp.callback_query(lambda c: c.data in ["admin_cancel", "admin_exit", "admin_back"])
async def admin_cancel(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "Админ-панель:",
        reply_markup=admin_kb
    )
    await callback.answer()

@dp.message(Command("admin"))
async def admin_panel(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("Доступ запрещен")
        return
    
    await message.answer("Админ-панель:", reply_markup=admin_kb)

@dp.callback_query(lambda c: c.data == "view_orders")
async def view_orders(callback: types.CallbackQuery):
    if not orders_db:
        await callback.answer("Нет активных заказов", show_alert=True)
        return
    
    builder = InlineKeyboardBuilder()
    for order_id, order_data in orders_db.items():
        builder.add(InlineKeyboardButton(
            text=f"Заказ #{order_id}",
            callback_data=f"order_detail_{order_id}"
        )
        )
    builder.adjust(1)
    
    await callback.message.edit_text(
        "Список заказов:",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


@dp.callback_query(lambda c: c.data.startswith("order_detail_"))
async def order_detail(callback: types.CallbackQuery):
    order_id = int(callback.data.split("_")[-1])
    order = orders_db.get(order_id)
    
    if not order:
        await callback.answer("Заказ не найден", show_alert=True)
        return
    
    order_text = (
        f"Заказ #{order_id}\n"
        f"Пользователь: {order['user_id']}\n"
        f"Адрес: {order['address']}\n"
        f"Телефон: {order['phone']}\n"
        f"Размер: {order['size']}\n"
        f"Комментарий: {order['comment']}\n"
        f"Товары:\n"
    )
    
    for item in order['items']:
        order_text += f"- {item['name']}\n"
    
    await callback.message.edit_text(
        order_text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Назад", callback_data="view_orders")]]
        )
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data == "add_pizza")
async def add_pizza_start(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Введите название новой пиццы:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Отмена", callback_data="admin_cancel")]]
        )
    )
    await state.set_state(AdminStates.WAITING_NEW_PIZZA_NAME)
    await callback.answer()

@dp.message(AdminStates.WAITING_NEW_PIZZA_NAME)
async def process_pizza_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer(
        "Введите описание пиццы:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Отмена", callback_data="admin_cancel")]]
        )
    )
    await state.set_state(AdminStates.WAITING_NEW_PIZZA_DESC)

@dp.message(AdminStates.WAITING_NEW_PIZZA_DESC)
async def process_pizza_desc(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer(
        "Отправьте фото пиццы:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Отмена", callback_data="admin_cancel")]]
        )
    )
    await state.set_state(AdminStates.WAITING_NEW_PIZZA_PHOTO)

@dp.message(AdminStates.WAITING_NEW_PIZZA_PHOTO)
async def process_pizza_photo(message: Message, state: FSMContext):
    if not message.photo:
        await message.answer("Пожалуйста, отправьте фото")
        return
    
    data = await state.get_data()
    pizza_id = f"m{len(pizza_info) + 1}"
    
    # Сохраняем фото (в реальном проекте нужно сохранять файл)
    pizza_info[pizza_id] = {
        "name": data['name'],
        "description": data['description'],
        "photo_id": message.photo[-1].file_id
    }
    
    await message.answer(
        f"Пицца {data['name']} успешно добавлена! ID: {pizza_id}",
        reply_markup=admin_kb
    )
    await state.clear()

# Удаление пиццы
@dp.callback_query(lambda c: c.data == "remove_pizza")
async def remove_pizza_start(callback: types.CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    for pizza_id, pizza_data in pizza_info.items():
        builder.add(InlineKeyboardButton(
            text=pizza_data['name'],
            callback_data=f"remove_{pizza_id}"
        ))
    builder.adjust(1)
    
    await callback.message.edit_text(
        "Выберите пиццу для удаления:",
        reply_markup=builder.as_markup()
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith("remove_"))
async def process_remove_pizza(callback: types.CallbackQuery):
    pizza_id = callback.data.split("_")[-1]
    if pizza_id in pizza_info:
        del pizza_info[pizza_id]
        await callback.answer(f"Пицца удалена", show_alert=True)
    else:
        await callback.answer("Пицца не найдена", show_alert=True)
    
    await callback.message.edit_text(
        "Админ-панель:",
        reply_markup=admin_kb
    )

@dp.callback_query(lambda c: c.data == "stats")
async def show_stats(callback: types.CallbackQuery):
    stats_text = (
        f"Всего пицц в меню: {len(pizza_info)}\n"
        f"Всего заказов: {len(orders_db)}\n"
        f"Пользователей с корзинами: {len(user_carts)}"
    )
    
    await callback.message.edit_text(
        stats_text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Назад", callback_data="admin_back")]]
        )
    )
    await callback.answer()

async def main() -> None:
    bot = Bot(token="")

    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())