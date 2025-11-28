from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from datemate.domain.entities import Faculty


def main_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🚀 Заполнить анкету", callback_data="action:register"),
        InlineKeyboardButton(text="❤️ Смотреть анкеты", callback_data="action:search"),
    )
    return builder.as_markup()


def sex_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Парень", callback_data="sex:M"),
        InlineKeyboardButton(text="Девушка", callback_data="sex:F"),
    )
    return builder.as_markup()


def faculty_keyboard(faculties: list[Faculty]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for faculty in faculties:
        builder.button(text=faculty.name, callback_data=f"faculty:{faculty.id}")
    builder.adjust(2)
    return builder.as_markup()


def photos_keyboard(has_photos: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="✅ Готово", callback_data="photos:done"))
    if not has_photos:
        builder.row(InlineKeyboardButton(text="⬅️ В меню", callback_data="action:menu"))
    return builder.as_markup()


def candidate_actions(candidate_id: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="👎 Пропустить", callback_data=f"rate:skip:{candidate_id}"),
        InlineKeyboardButton(text="❤️ Лайк", callback_data=f"rate:like:{candidate_id}"),
    )
    builder.row(InlineKeyboardButton(text="➡️ Дальше", callback_data="search:next"))
    return builder.as_markup()


def back_to_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ В меню", callback_data="action:menu")
    return builder.as_markup()


def verify_actions(request_id: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"approve:{request_id}"),
        InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject:{request_id}"),
    )
    builder.row(InlineKeyboardButton(text="🔄 Обновить список", callback_data="verify:refresh"))
    return builder.as_markup()
