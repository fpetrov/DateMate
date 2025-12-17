from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, Message

from datemate.domain.repositories import MatchRepository, UserRepository
from datemate.tgbot.functional import CoreContext, Phrases, keyboards
from datemate.tgbot.handlers.common import (
    ensure_registered_user,
    show_main_menu,
    show_profile,
    update_dialog_message,
)

router = Router()


class OnboardingState(StatesGroup):
    language = State()


async def _show_next_candidate(
    event: Message | CallbackQuery,
    context: CoreContext,
    phrases: Phrases,
    match_repo: MatchRepository,
    current_user,
):
    candidate = await match_repo.get_next_candidate(current_user)
    if candidate is None:
        await update_dialog_message(
            event,
            context,
            phrases["search"]["no_candidates"],
            reply_markup=keyboards.back_to_menu(phrases),
        )
        return None

    await show_profile(
        event,
        context,
        candidate,
        phrases,
        reply_markup=keyboards.candidate_actions(phrases, str(candidate.id)),
    )
    return candidate


async def _show_match_by_index(
    event: Message | CallbackQuery,
    context: CoreContext,
    phrases: Phrases,
    match_repo: MatchRepository,
    user,
    index: int,
):
    safe_index = max(index, 0)
    pairs, total = await match_repo.list_matches(user.id, offset=safe_index, limit=1)

    if total == 0:
        await update_dialog_message(event, context, phrases["matches"]["empty"], reply_markup=keyboards.main_menu(phrases))
        return

    if not pairs and safe_index >= total:
        await update_dialog_message(
            event,
            context,
            phrases["matches"]["out_of_range"],
            reply_markup=keyboards.matches_navigation(phrases, total - 1, total),
        )
        return

    if not pairs:
        await update_dialog_message(
            event,
            context,
            phrases["matches"]["not_available"],
            reply_markup=keyboards.matches_navigation(phrases, safe_index, total),
        )
        return

    match, other_user = pairs[0]
    username = await _resolve_username(other_user, context)
    await show_profile(
        event,
        context,
        other_user,
        phrases,
        match_time=match.created_at,
        username=username,
        reply_markup=keyboards.matches_navigation(phrases, safe_index, total),
    )


async def _resolve_username(user, context: CoreContext) -> str | None:
    username = getattr(user, "username", None)
    if username:
        return f"@{username.lstrip('@')}"

    if context.bot is None:
        return None

    try:
        chat = await context.bot.get_chat(user.telegram_id)
    except TelegramBadRequest:
        return None

    return f"@{chat.username}" if chat.username else None


@router.message(CommandStart())
async def cmd_start(
    message: Message,
    state: FSMContext,
    context: CoreContext,
    phrases: Phrases,
    session,
    phrases_provider: Phrases,
) -> None:
    await context.delete_core_message()
    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(message.from_user.id)

    if user:
        await context.update_language(user.language)
    elif not context.language_defined():
        await state.set_state(OnboardingState.language)
        await update_dialog_message(
            message,
            context,
            phrases["registration"]["language"]["ask"],
            reply_markup=keyboards.language_keyboard(phrases),
        )
        return

    localized_phrases = phrases_provider.for_language(
        user.language if user else (context.get_language() if context.language_defined() else None)
    )
    await show_main_menu(message, context, localized_phrases, is_registered=user is not None)


@router.callback_query(F.data == "action:menu")
async def back_to_menu(callback: CallbackQuery, state, context: CoreContext, phrases: Phrases, session) -> None:
    await callback.answer()
    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(callback.from_user.id)
    await show_main_menu(callback, context, phrases, is_registered=user is not None)


@router.callback_query(OnboardingState.language)
async def set_initial_language(
    callback: CallbackQuery,
    state: FSMContext,
    context: CoreContext,
    phrases: Phrases,
    phrases_provider: Phrases,
    session,
) -> None:
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
    await context.update_language(language_code)
    await state.set_state(None)

    localized_phrases = phrases_provider.for_language(language_code)
    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(callback.from_user.id)

    await show_main_menu(callback, context, localized_phrases, is_registered=user is not None)


@router.callback_query(F.data == "action:search")
async def search_profiles(callback: CallbackQuery, context: CoreContext, phrases: Phrases, session) -> None:
    await callback.answer()
    user_repo = UserRepository(session)
    user = await ensure_registered_user(callback, context, phrases, user_repo, callback.from_user.id)
    if user is None:
        return

    match_repo = MatchRepository(session)
    await update_dialog_message(callback, context, phrases["search"]["loading"], reply_markup=keyboards.back_to_menu(phrases))
    await _show_next_candidate(callback, context, phrases, match_repo, user)


@router.callback_query(F.data.startswith("rate:"))
async def rate_candidate(callback: CallbackQuery, context: CoreContext, phrases: Phrases, session) -> None:
    parts = callback.data.split(":")
    if len(parts) != 3:
        await update_dialog_message(
            callback,
            context,
            phrases["search"]["candidate_not_found"],
            reply_markup=keyboards.back_to_menu(phrases),
        )
        return

    _, action, candidate_id_raw = parts
    try:
        candidate_id = int(candidate_id_raw)
    except ValueError:
        await update_dialog_message(
            callback,
            context,
            phrases["search"]["candidate_not_found"],
            reply_markup=keyboards.back_to_menu(phrases),
        )
        return

    user_repo = UserRepository(session)
    user = await ensure_registered_user(callback, context, phrases, user_repo, callback.from_user.id)
    if user is None:
        return

    candidate = await user_repo.get_by_id(candidate_id)
    if candidate is None:
        await update_dialog_message(
            callback,
            context,
            phrases["search"]["candidate_not_found"],
            reply_markup=keyboards.back_to_menu(phrases),
        )
        return

    match_repo = MatchRepository(session)
    _, matched = await match_repo.set_reaction(user.id, candidate.id, is_like=action == "like")

    response_text = None
    if matched:
        response_text = phrases["search"]["match"]
    elif action == "like":
        response_text = phrases["search"]["like_saved"]
    else:
        response_text = phrases["search"]["skip_saved"]

    await _show_next_candidate(callback, context, phrases, match_repo, user)
    if response_text:
        await callback.answer(response_text)


@router.callback_query(F.data.startswith("search:next"))
async def skip_candidate(callback: CallbackQuery, context: CoreContext, phrases: Phrases, session) -> None:
    await callback.answer()
    parts = callback.data.split(":")
    candidate_id_raw = parts[2] if len(parts) >= 3 else None

    user_repo = UserRepository(session)
    user = await ensure_registered_user(callback, context, phrases, user_repo, callback.from_user.id)
    if user is None:
        return

    match_repo = MatchRepository(session)

    if candidate_id_raw:
        try:
            candidate_id = int(candidate_id_raw)
            await match_repo.set_reaction(user.id, candidate_id, is_like=False)
        except ValueError:
            pass

    await _show_next_candidate(callback, context, phrases, match_repo, user)


@router.callback_query(F.data == "action:matches")
async def show_matches(callback: CallbackQuery, context: CoreContext, phrases: Phrases, session) -> None:
    await callback.answer()
    user_repo = UserRepository(session)
    user = await ensure_registered_user(
        callback,
        context,
        phrases,
        user_repo,
        callback.from_user.id,
        not_registered_text=phrases["matches"]["not_registered"],
    )
    if user is None:
        return

    match_repo = MatchRepository(session)
    await _show_match_by_index(callback, context, phrases, match_repo, user, 0)


@router.callback_query(F.data.startswith("matches:page:"))
async def paginate_matches(callback: CallbackQuery, context: CoreContext, phrases: Phrases, session) -> None:
    await callback.answer()
    parts = callback.data.split(":")
    try:
        target_index = int(parts[-1])
    except (ValueError, IndexError):
        await callback.answer(phrases["matches"]["out_of_range"])
        return

    user_repo = UserRepository(session)
    user = await ensure_registered_user(
        callback,
        context,
        phrases,
        user_repo,
        callback.from_user.id,
        not_registered_text=phrases["matches"]["not_registered"],
    )
    if user is None:
        return

    match_repo = MatchRepository(session)
    await _show_match_by_index(callback, context, phrases, match_repo, user, target_index)


@router.callback_query(F.data == "matches:noop")
async def noop(callback: CallbackQuery) -> None:
    await callback.answer()


@router.message()
async def undefined(message: Message, context: CoreContext, phrases: Phrases):
    await update_dialog_message(message, context, phrases["undefined_command"], reply_markup=keyboards.main_menu(phrases))

