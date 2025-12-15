from __future__ import annotations

from datetime import datetime

from aiogram.enums import ParseMode
from aiogram.types import CallbackQuery, Message

from datemate.tgbot.functional import CoreContext, Phrases, keyboards


async def update_dialog_message(event: Message | CallbackQuery, context: CoreContext, text: str, reply_markup=None) -> None:
    await context.respond_text(event, text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)


async def show_main_menu(event: Message | CallbackQuery, context: CoreContext, phrases: Phrases, is_registered: bool) -> None:
    text = phrases["menu"]["registered" if is_registered else "unregistered"]
    await update_dialog_message(event, context, text, reply_markup=keyboards.main_menu())


def _sex_label(sex: str | None) -> str:
    if sex == "M":
        return "Парень"
    if sex == "F":
        return "Девушка"
    return "—"


def _search_sex_label(search_sex: str | None) -> str:
    if search_sex == "M":
        return "Парня"
    if search_sex == "F":
        return "Девушку"
    return "Кого угодно"


def format_profile_caption(user, match_time: datetime | None = None) -> str:
    faculty_name = user.faculty.name if getattr(user, "faculty", None) else "—"

    caption_lines = [
        f"{user.name}, {user.age}",
        f"Пол: {_sex_label(user.sex)}",
        f"Ищу: {_search_sex_label(getattr(user, 'search_sex', None))}",
        f"Факультет: {faculty_name}",
        "",
        user.description or "",
    ]

    if match_time:
        caption_lines.extend(["", match_time.strftime("Совпадение: %d.%m.%Y %H:%M")])

    return "\n".join(line for line in caption_lines if line is not None)


async def show_profile(
    event: Message | CallbackQuery,
    context: CoreContext,
    user,
    phrases: Phrases,
    reply_markup=None,
    match_time: datetime | None = None,
):
    caption = format_profile_caption(user, match_time=match_time)
    if user.photos:
        await context.respond_photo(
            event,
            user.photos[0],
            caption=caption,
            reply_markup=reply_markup,
            fallback_text=caption,
        )
        return

    await update_dialog_message(event, context, caption, reply_markup=reply_markup)


async def ensure_registered_user(
    event: Message | CallbackQuery,
    context: CoreContext,
    phrases: Phrases,
    user_repo,
    telegram_id: int,
    not_registered_text: str | None = None,
):
    user = await user_repo.get_by_telegram_id(telegram_id)
    if user is None:
        await update_dialog_message(
            event,
            context,
            not_registered_text or phrases["search"]["not_registered"],
            reply_markup=keyboards.main_menu(),
        )
        return None

    return user

