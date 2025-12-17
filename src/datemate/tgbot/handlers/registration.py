from __future__ import annotations

import re

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from datemate.domain.entities import Faculty
from datemate.domain.repositories import FacultyRepository, UserRepository
from datemate.tgbot.functional import CoreContext, Phrases, keyboards
from datemate.tgbot.handlers.common import update_dialog_message

router = Router()


class RegistrationState(StatesGroup):
    language = State()
    name = State()
    sex = State()
    search_sex = State()
    age = State()
    faculty = State()
    description = State()
    photos = State()


@router.callback_query(F.data == "action:register")
async def start_registration(callback: CallbackQuery, state: FSMContext, context: CoreContext, phrases: Phrases, session) -> None:
    await callback.answer()
    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(callback.from_user.id)
    data = await state.get_data()
    await state.update_data(existing_user=bool(user))
    language = data.get("language")

    if user:
        language = user.language
        await state.update_data(language=language)
        await context.update_language(language)

    if language:
        await state.set_state(RegistrationState.name)
        prompt_key = "repeat" if user else "ask"
        await update_dialog_message(
            callback,
            context,
            phrases["registration"]["name"][prompt_key],
        )
        return

    await state.set_state(RegistrationState.language)
    prompt = phrases["registration"]["language"]["ask"]
    await update_dialog_message(callback, context, prompt, reply_markup=keyboards.language_keyboard(phrases))


@router.callback_query(RegistrationState.language)
async def set_language(callback: CallbackQuery, state: FSMContext, context: CoreContext, phrases: Phrases, phrases_provider: Phrases) -> None:
    await callback.answer()
    if not callback.data or not callback.data.startswith("language:"):
        await update_dialog_message(
            callback,
            context,
            phrases["registration"]["language"]["invalid"],
            reply_markup=keyboards.language_keyboard(phrases),
        )
        return

    language_code = callback.data.split(":", maxsplit=1)[1]
    if language_code not in {"ru", "en", "fr"}:
        await update_dialog_message(
            callback,
            context,
            phrases["registration"]["language"]["invalid"],
            reply_markup=keyboards.language_keyboard(phrases),
        )
        return

    await state.update_data(language=language_code)
    data = await state.get_data()
    await state.set_state(RegistrationState.name)
    localized_phrases = phrases_provider.for_language(language_code)
    prompt_key = "repeat" if data.get("existing_user") else "ask"
    await update_dialog_message(
        callback,
        context,
        localized_phrases["registration"]["name"][prompt_key],
    )


@router.message(RegistrationState.name)
async def set_name(message: Message, state: FSMContext, context: CoreContext, phrases: Phrases) -> None:
    if not message.text:
        await update_dialog_message(message, context, phrases["registration"]["name"]["invalid"])
        return

    cleaned_name = message.text.strip()
    if not re.fullmatch(r"[A-Za-zА-Яа-яЁё\- ]{2,50}", cleaned_name):
        await update_dialog_message(message, context, phrases["registration"]["name"]["invalid"])
        return

    await state.update_data(name=cleaned_name)
    await state.set_state(RegistrationState.sex)
    await update_dialog_message(message, context, phrases["registration"]["sex"], reply_markup=keyboards.sex_keyboard(phrases))


@router.callback_query(RegistrationState.sex, F.data.startswith("sex:"))
async def set_sex(callback: CallbackQuery, state: FSMContext, context: CoreContext, phrases: Phrases) -> None:
    await callback.answer()
    sex_value = callback.data.split(":", maxsplit=1)[1]
    if sex_value not in {"M", "F"}:
        await update_dialog_message(
            callback, context, phrases["registration"]["sex_invalid"], reply_markup=keyboards.sex_keyboard(phrases)
        )
        return

    await state.update_data(sex=sex_value)
    await state.set_state(RegistrationState.search_sex)
    await update_dialog_message(
        callback,
        context,
        phrases["registration"]["search_sex"],
        reply_markup=keyboards.search_sex_keyboard(phrases),
    )


@router.callback_query(RegistrationState.search_sex, F.data.startswith("search_sex:"))
async def set_search_sex(callback: CallbackQuery, state: FSMContext, context: CoreContext, phrases: Phrases) -> None:
    await callback.answer()
    search_value = callback.data.split(":", maxsplit=1)[1]
    if search_value not in {"M", "F"}:
        await update_dialog_message(
            callback,
            context,
            phrases["registration"]["search_sex_invalid"],
            reply_markup=keyboards.search_sex_keyboard(phrases),
        )
        return

    await state.update_data(search_sex=search_value)
    await state.set_state(RegistrationState.age)
    await update_dialog_message(callback, context, phrases["registration"]["age"])


@router.message(RegistrationState.age)
async def set_age(message: Message, state: FSMContext, context: CoreContext, phrases: Phrases, session) -> None:
    if not message.text or not message.text.strip().isdigit():
        await update_dialog_message(message, context, phrases["registration"]["age_invalid"])
        return

    age_value = int(message.text.strip())
    if age_value < 16 or age_value > 100:
        await update_dialog_message(message, context, phrases["registration"]["age_invalid"])
        return

    await state.update_data(age=age_value)
    await state.set_state(RegistrationState.faculty)
    faculties = [Faculty.from_model(f) for f in await FacultyRepository(session).list_faculties()]
    await update_dialog_message(message, context, phrases["registration"]["faculty"], reply_markup=keyboards.faculty_keyboard(faculties))


@router.callback_query(RegistrationState.faculty, F.data.startswith("faculty:"))
async def set_faculty(callback: CallbackQuery, state: FSMContext, context: CoreContext, phrases: Phrases, session) -> None:
    await callback.answer()
    faculty_id = callback.data.split(":", maxsplit=1)[1]
    faculty_repo = FacultyRepository(session)
    faculty = await faculty_repo.get_by_id(faculty_id)
    if faculty is None:
        faculties = [Faculty.from_model(f) for f in await faculty_repo.list_faculties()]
        await update_dialog_message(
            callback,
            context,
            phrases["registration"]["faculty_invalid"],
            reply_markup=keyboards.faculty_keyboard(faculties),
        )
        return

    await state.update_data(faculty_id=faculty.id)
    await state.set_state(RegistrationState.description)
    await update_dialog_message(callback, context, phrases["registration"]["description"])


@router.message(RegistrationState.description)
async def set_description(message: Message, state: FSMContext, context: CoreContext, phrases: Phrases) -> None:
    if not message.text or not message.text.strip():
        await update_dialog_message(message, context, phrases["registration"]["description_invalid"])
        return

    await state.update_data(description=message.text.strip(), photo_ids=[])
    await state.set_state(RegistrationState.photos)
    await update_dialog_message(
        message,
        context,
        phrases["registration"]["photos"],
        reply_markup=keyboards.photos_keyboard(phrases, has_photos=False),
    )


@router.message(RegistrationState.photos)
async def set_photos(message: Message, state: FSMContext, context: CoreContext, phrases: Phrases, session) -> None:
    data = await state.get_data()
    photo_ids: list[str] = list(data.get("photo_ids", []))

    if not message.photo:
        await update_dialog_message(
            message,
            context,
            phrases["registration"]["photos_invalid"],
            reply_markup=keyboards.photos_keyboard(phrases, has_photos=bool(photo_ids)),
        )
        return

    photo_id = message.photo[-1].file_id
    photo_ids.append(photo_id)
    await state.update_data(photo_ids=photo_ids)
    await update_dialog_message(
        message,
        context,
        phrases["registration"]["photos_saved"],
        reply_markup=keyboards.photos_keyboard(phrases, has_photos=True),
    )


@router.callback_query(RegistrationState.photos, F.data == "photos:done")
async def finish_photos(callback: CallbackQuery, state: FSMContext, context: CoreContext, phrases: Phrases, session) -> None:
    await callback.answer()
    data = await state.get_data()
    photo_ids: list[str] = list(data.get("photo_ids", []))

    if not photo_ids:
        await update_dialog_message(
            callback,
            context,
            phrases["registration"]["photos_missing_on_finish"],
            reply_markup=keyboards.photos_keyboard(phrases, has_photos=False),
        )
        return

    user_repo = UserRepository(session)
    await user_repo.upsert_user(
        telegram_id=callback.from_user.id,
        username=callback.from_user.username,
        name=data["name"],
        sex=data["sex"],
        search_sex=data["search_sex"],
        language=data.get("language", "ru"),
        age=data["age"],
        faculty_id=data["faculty_id"],
        description=data["description"],
        photo_ids=photo_ids,
    )

    await update_dialog_message(
        callback,
        context,
        phrases["registration"]["completed"],
        reply_markup=keyboards.main_menu(phrases),
    )

