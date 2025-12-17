import logging
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from datemate.domain.repositories import UserRepository
from datemate.tgbot.functional import CoreContext, CoreMessage, Phrases


class InterfaceMiddleware(BaseMiddleware):
    def __init__(self, phrases: Phrases):
        super().__init__()
        self.phrases = phrases

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any],
    ) -> Any | None:
        state: FSMContext = data["state"]
        bot: Bot = data["bot"]
        phrases_provider: Phrases = data.get("phrases_provider", self.phrases)
        data["phrases_provider"] = phrases_provider
        user_language = None

        session = data.get("session")
        if session is not None:
            user_repo = UserRepository(session)
            user = await user_repo.get_by_telegram_id(event.from_user.id)
            if user:
                user_language = getattr(user, "language", None)

        state_data = await state.get_data()
        user_language = state_data.get("language", user_language)

        phrases = phrases_provider.for_language(user_language)
        data["phrases"] = phrases
        context = await CoreContext.create(bot, state, fallback_text=phrases["return_to_menu"])
        event_instance = event
        user_id = event.from_user.id

        # Add context to DI container
        data["context"] = context

        event_is_callback = isinstance(event, CallbackQuery)

        if event_is_callback:
            event_instance = event.message

        if context.message_exists():
            core_message = context.get_message()

            if (event_instance.date - core_message.date).total_seconds() > 2 * 24 * 60 * 60:
                logging.log(logging.WARNING, "Deleting old message")
                await bot.delete_message(chat_id=core_message.chat_id, message_id=core_message.message_id)
                await self.send_revert_state_message(state, bot, event_instance, context, phrases, user_id)

        if not event_is_callback:
            await bot.delete_message(chat_id=event_instance.chat.id, message_id=event_instance.message_id)

        return await handler(event, data)

    @staticmethod
    async def send_revert_state_message(
        state: FSMContext,
        bot: Bot,
        event: Message,
        context: CoreContext,
        phrases: Phrases,
        user_id: int,
    ) -> None:
        await state.set_state(None)

        new_message = await bot.send_message(event.chat.id, phrases["return_to_menu"])
        logging.log(logging.WARNING, "Sent new message in revert state")

        core_message = CoreMessage(
            new_message.chat.id,
            new_message.message_id,
            user_id,
            new_message.date,
        )

        await context.update_message(core_message)
