from __future__ import annotations

import logging
import re

from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from datemate.domain.entities import Faculty
from datemate.domain.repositories import FacultyRepository, UserRepository
from datemate.tgbot.functional import CoreContext, Phrases, keyboards

router = Router()


class RegistrationState(StatesGroup):
    name = State()
    sex = State()
    age = State()
    faculty = State()
    description = State()
    photos = State()


async def _update_dialog_message(event: Message | CallbackQuery, context: CoreContext, text: str, reply_markup=None) -> None:
    await context.respond_text(event, text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)


async def _show_main_menu(event: Message | CallbackQuery, context: CoreContext, phrases: Phrases, is_registered: bool) -> None:
    text = phrases["menu"]["registered" if is_registered else "unregistered"]
    await _update_dialog_message(event, context, text, reply_markup=keyboards.main_menu())


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, context: CoreContext, phrases: Phrases, session) -> None:
    await context.delete_core_message()
    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(message.from_user.id)
    await _show_main_menu(message, context, phrases, is_registered=user is not None)


@router.callback_query(F.data == "action:menu")
async def back_to_menu(callback: CallbackQuery, state: FSMContext, context: CoreContext, phrases: Phrases, session) -> None:
    await callback.answer()
    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(callback.from_user.id)
    await _show_main_menu(callback, context, phrases, is_registered=user is not None)


@router.callback_query(F.data == "action:register")
async def start_registration(callback: CallbackQuery, state: FSMContext, context: CoreContext, phrases: Phrases, session) -> None:
    await callback.answer()
    await state.set_state(RegistrationState.name)
    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(callback.from_user.id)
    prompt = phrases["registration"]["name"]["repeat" if user else "ask"]
    await _update_dialog_message(callback, context, prompt)


@router.message(RegistrationState.name)
async def set_name(message: Message, state: FSMContext, context: CoreContext, phrases: Phrases) -> None:
    if not message.text:
        await _update_dialog_message(message, context, phrases["registration"]["name"]["invalid"])
        return

    cleaned_name = message.text.strip()
    if not re.fullmatch(r"[A-Za-zА-Яа-яЁё\- ]{2,50}", cleaned_name):
        await _update_dialog_message(message, context, phrases["registration"]["name"]["invalid"])
        return

    await state.update_data(name=cleaned_name)
    await state.set_state(RegistrationState.sex)
    await _update_dialog_message(message, context, phrases["registration"]["sex"], reply_markup=keyboards.sex_keyboard())


@router.callback_query(RegistrationState.sex, F.data.startswith("sex:"))
async def set_sex(callback: CallbackQuery, state: FSMContext, context: CoreContext, phrases: Phrases) -> None:
    await callback.answer()
    sex_value = callback.data.split(":", maxsplit=1)[1]
    if sex_value not in {"M", "F"}:
        await _update_dialog_message(callback, context, phrases["registration"]["sex_invalid"], reply_markup=keyboards.sex_keyboard())
        return

    await state.update_data(sex=sex_value)
    await state.set_state(RegistrationState.age)
    await _update_dialog_message(callback, context, phrases["registration"]["age"])


@router.message(RegistrationState.age)
async def set_age(message: Message, state: FSMContext, context: CoreContext, phrases: Phrases, session) -> None:
    if not message.text or not message.text.strip().isdigit():
        await _update_dialog_message(message, context, phrases["registration"]["age_invalid"])
        return

    age_value = int(message.text.strip())
    if age_value < 16 or age_value > 100:
        await _update_dialog_message(message, context, phrases["registration"]["age_invalid"])
        return

    await state.update_data(age=age_value)
    await state.set_state(RegistrationState.faculty)
    faculties = [Faculty.from_model(f) for f in await FacultyRepository(session).list_faculties()]
    await _update_dialog_message(message, context, phrases["registration"]["faculty"], reply_markup=keyboards.faculty_keyboard(faculties))


@router.callback_query(RegistrationState.faculty, F.data.startswith("faculty:"))
async def set_faculty(callback: CallbackQuery, state: FSMContext, context: CoreContext, phrases: Phrases, session) -> None:
    await callback.answer()
    faculty_id = callback.data.split(":", maxsplit=1)[1]
    faculty_repo = FacultyRepository(session)
    faculty = await faculty_repo.get_by_id(faculty_id)
    if faculty is None:
        faculties = [Faculty.from_model(f) for f in await faculty_repo.list_faculties()]
        await _update_dialog_message(callback, context, phrases["registration"]["faculty_invalid"], reply_markup=keyboards.faculty_keyboard(faculties))
        return

    await state.update_data(faculty_id=faculty.id)
    await state.set_state(RegistrationState.description)
    await _update_dialog_message(callback, context, phrases["registration"]["description"])


@router.message(RegistrationState.description)
async def set_description(message: Message, state: FSMContext, context: CoreContext, phrases: Phrases) -> None:
    if not message.text or not message.text.strip():
        await _update_dialog_message(message, context, phrases["registration"]["description_invalid"])
        return

    await state.update_data(description=message.text.strip(), photo_ids=[])
    await state.set_state(RegistrationState.photos)
    await _update_dialog_message(
        message,
        context,
        phrases["registration"]["photos"],
        reply_markup=keyboards.photos_keyboard(has_photos=False),
    )


@router.message(RegistrationState.photos)
async def set_photos(message: Message, state: FSMContext, context: CoreContext, phrases: Phrases, session) -> None:
    data = await state.get_data()
    photo_ids: list[str] = list(data.get("photo_ids", []))

    if not message.photo:
        await _update_dialog_message(
            message,
            context,
            phrases["registration"]["photos_invalid"],
            reply_markup=keyboards.photos_keyboard(has_photos=bool(photo_ids)),
        )
        return

    photo_id = message.photo[-1].file_id
    photo_ids.append(photo_id)
    await state.update_data(photo_ids=photo_ids)
    await _update_dialog_message(
        message,
        context,
        phrases["registration"]["photos_saved"],
        reply_markup=keyboards.photos_keyboard(has_photos=True),
    )


@router.callback_query(RegistrationState.photos, F.data == "photos:done")
async def finish_photos(callback: CallbackQuery, state: FSMContext, context: CoreContext, phrases: Phrases, session) -> None:
    await callback.answer()
    data = await state.get_data()
    photo_ids: list[str] = list(data.get("photo_ids", []))

    if not photo_ids:
        await _update_dialog_message(
            callback,
            context,
            phrases["registration"]["photos_missing_on_finish"],
            reply_markup=keyboards.photos_keyboard(has_photos=False),
        )
        return

    user_repo = UserRepository(session)
    await user_repo.upsert_user(
        telegram_id=callback.from_user.id,
        name=data["name"],
        sex=data["sex"],
        age=data["age"],
        faculty_id=data["faculty_id"],
        description=data["description"],
        photo_ids=photo_ids,
    )

    await _update_dialog_message(
        callback,
        context,
        phrases["registration"]["completed"],
        reply_markup=keyboards.main_menu(),
    )


@router.callback_query(F.data == "action:search")
async def search_profiles(callback: CallbackQuery, context: CoreContext, phrases: Phrases, session) -> None:
    await callback.answer()
    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(callback.from_user.id)
    if user is None:
        await _update_dialog_message(callback, context, phrases["search"]["not_registered"], reply_markup=keyboards.main_menu())
        return

    logging.log(logging.WARN, f"Searching profiles for {user.telegram_id}")
    await _update_dialog_message(callback, context, phrases["search"]["placeholder"], reply_markup=keyboards.main_menu())


@router.message()
async def undefined(message: Message, context: CoreContext, phrases: Phrases):
    await _update_dialog_message(message, context, phrases["undefined_command"], reply_markup=keyboards.main_menu())
