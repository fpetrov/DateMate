from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from datemate.domain.entities import Faculty
from datemate.tgbot.functional import LanguagePhrases


def main_menu(phrases: LanguagePhrases) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text=phrases["keyboards"]["menu"]["register"], callback_data="action:register"),
        InlineKeyboardButton(text=phrases["keyboards"]["menu"]["search"], callback_data="action:search"),
    )
    builder.row(InlineKeyboardButton(text=phrases["keyboards"]["menu"]["matches"], callback_data="action:matches"))
    return builder.as_markup()


def sex_keyboard(phrases: LanguagePhrases) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text=phrases["keyboards"]["sex"]["male"], callback_data="sex:M"),
        InlineKeyboardButton(text=phrases["keyboards"]["sex"]["female"], callback_data="sex:F"),
    )
    return builder.as_markup()


def search_sex_keyboard(phrases: LanguagePhrases) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text=phrases["keyboards"]["search_sex"]["male"], callback_data="search_sex:M"),
        InlineKeyboardButton(text=phrases["keyboards"]["search_sex"]["female"], callback_data="search_sex:F"),
    )
    return builder.as_markup()


def faculty_keyboard(faculties: list[Faculty]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for faculty in faculties:
        builder.button(text=faculty.name, callback_data=f"faculty:{faculty.id}")
    builder.adjust(2)
    return builder.as_markup()


def photos_keyboard(phrases: LanguagePhrases, has_photos: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=phrases["keyboards"]["photos"]["done"], callback_data="photos:done"))
    if not has_photos:
        builder.row(InlineKeyboardButton(text=phrases["keyboards"]["back_to_menu"], callback_data="action:menu"))
    return builder.as_markup()


def candidate_actions(phrases: LanguagePhrases, candidate_id: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=phrases["keyboards"]["candidate"]["skip"],
            callback_data=f"rate:skip:{candidate_id}",
        ),
        InlineKeyboardButton(
            text=phrases["keyboards"]["candidate"]["like"],
            callback_data=f"rate:like:{candidate_id}",
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text=phrases["keyboards"]["candidate"]["next"],
            callback_data=f"search:next:{candidate_id}",
        )
    )
    return builder.as_markup()


def back_to_menu(phrases: LanguagePhrases) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=phrases["keyboards"]["back_to_menu"], callback_data="action:menu")
    return builder.as_markup()


def verify_actions(phrases: LanguagePhrases, request_id: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text=phrases["keyboards"]["verify"]["approve"], callback_data=f"approve:{request_id}"),
        InlineKeyboardButton(text=phrases["keyboards"]["verify"]["reject"], callback_data=f"reject:{request_id}"),
    )
    builder.row(
        InlineKeyboardButton(
            text=phrases["keyboards"]["verify"]["refresh"],
            callback_data="verify:refresh",
        )
    )
    return builder.as_markup()


def matches_navigation(phrases: LanguagePhrases, current_index: int, total: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if total:
        builder.row(
            InlineKeyboardButton(
                text="⬅️", callback_data=f"matches:page:{max(current_index - 1, 0)}"
            ),
            InlineKeyboardButton(text=f"{current_index + 1}/{total}", callback_data="matches:noop"),
            InlineKeyboardButton(
                text="➡️",
                callback_data=f"matches:page:{min(current_index + 1, total - 1)}",
            ),
        )

    builder.row(InlineKeyboardButton(text=phrases["keyboards"]["back_to_menu"], callback_data="action:menu"))
    return builder.as_markup()


def language_keyboard(phrases: LanguagePhrases) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    language_buttons = phrases["keyboards"]["language"]
    builder.row(
        InlineKeyboardButton(text=language_buttons["ru"], callback_data="language:ru"),
        InlineKeyboardButton(text=language_buttons["en"], callback_data="language:en"),
        InlineKeyboardButton(text=language_buttons["fr"], callback_data="language:fr"),
    )
    return builder.as_markup()
