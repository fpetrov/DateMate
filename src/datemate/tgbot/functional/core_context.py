import logging
from typing import Any, Dict

from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InputFile, InputMediaPhoto, Message

from .core_message import CoreMessage


# TODO: Добавить cleanup_list для удаления предыдущих сообщений
class CoreContext:
    CORE_MESSAGE_KEY: str = "core_message"
    LANGUAGE_KEY: str = "language"
    DEFAULT_FALLBACK_TEXT: str = "🔙 Нажми /start, чтобы вернуться в меню"

    __create_key = object()

    def __init__(self, create_key: object):
        if create_key is not CoreContext.__create_key:
            raise ValueError("CoreContext can be created only with CoreContext.create() method!")

        self.bot: Bot | None = None
        self.state: FSMContext | None = None
        self.data: Dict[str, Any] | None = None
        self.fallback_text: str = self.DEFAULT_FALLBACK_TEXT

    @classmethod
    async def create(cls, bot: Bot, state: FSMContext, fallback_text: str | None = None):
        self = cls(CoreContext.__create_key)
        self.bot = bot
        self.state = state
        self.data = await state.get_data()
        self.fallback_text = fallback_text or cls.DEFAULT_FALLBACK_TEXT

        return self

    def _event_message(self, event: Message | CallbackQuery) -> Message:
        return event.message if isinstance(event, CallbackQuery) else event

    def message_exists(self) -> bool:
        return self.CORE_MESSAGE_KEY in self.data

    def get_message(self) -> CoreMessage:
        return self.data[self.CORE_MESSAGE_KEY]

    async def update_message(self, message: CoreMessage):
        await self.state.update_data({self.CORE_MESSAGE_KEY: message})
        self.data[self.CORE_MESSAGE_KEY] = message

    async def delete_core_message(self) -> None:
        if not self.message_exists():
            return

        core_message = self.get_message()
        try:
            await self.bot.delete_message(chat_id=core_message.chat_id, message_id=core_message.message_id)
        except TelegramBadRequest:
            pass

        updated_data = await self.state.get_data()
        updated_data.pop(self.CORE_MESSAGE_KEY, None)
        await self.state.set_data(updated_data)
        self.data = updated_data

    async def respond_text(
        self,
        event: Message | CallbackQuery,
        text: str,
        reply_markup=None,
        parse_mode: ParseMode | str | None = ParseMode.HTML,
        disable_web_page_preview: bool = True,
        fallback_text: str | None = None,
    ) -> CoreMessage:
        message = self._event_message(event)
        target_text = text
        fallback = fallback_text if fallback_text is not None else text

        if self.message_exists():
            core_message = self.get_message()
            try:
                await self.bot.edit_message_text(
                    chat_id=core_message.chat_id,
                    message_id=core_message.message_id,
                    text=text,
                    reply_markup=reply_markup,
                    parse_mode=parse_mode,
                    disable_web_page_preview=disable_web_page_preview,
                )
                return core_message
            except TelegramBadRequest as text_error:
                logging.error(text_error.message)
                if text_error.message == "Bad Request: message is not modified":
                    return core_message

                target_text = fallback
                await self.delete_core_message()

        logging.log(level=logging.WARNING, msg=f"Creating a new message to {target_text}...")
        new_message = await self.bot.send_message(
            message.chat.id,
            target_text,
            reply_markup=reply_markup,
            parse_mode=parse_mode,
            disable_web_page_preview=disable_web_page_preview,
        )
        core_message = CoreMessage(new_message.chat.id, new_message.message_id, message.from_user.id, new_message.date)
        await self.update_message(core_message)
        return core_message

    async def respond_photo(
        self,
        event: Message | CallbackQuery,
        photo: str | InputFile,
        caption: str | None = None,
        reply_markup=None,
        parse_mode: ParseMode | str | None = ParseMode.HTML,
        fallback_text: str | None = None,
    ) -> CoreMessage:
        message = self._event_message(event)
        fallback = fallback_text or self.fallback_text
        caption_to_send = caption

        if self.message_exists():
            core_message = self.get_message()
            try:
                await self.bot.edit_message_media(
                    chat_id=core_message.chat_id,
                    message_id=core_message.message_id,
                    media=InputMediaPhoto(media=photo, caption=caption, parse_mode=parse_mode),
                    reply_markup=reply_markup,
                )
                return core_message
            except TelegramBadRequest:
                caption_to_send = fallback
                await self.delete_core_message()

        new_message = await self.bot.send_photo(
            message.chat.id,
            photo=photo,
            caption=caption_to_send,
            reply_markup=reply_markup,
            parse_mode=parse_mode,
        )
        core_message = CoreMessage(new_message.chat.id, new_message.message_id, message.from_user.id, new_message.date)
        await self.update_message(core_message)
        return core_message

    def language_defined(self) -> bool:
        return self.LANGUAGE_KEY in self.data

    def get_language(self) -> str:
        return self.data[self.LANGUAGE_KEY]

    async def update_language(self, language: str):
        await self.state.update_data({self.LANGUAGE_KEY: language})
        self.data[self.LANGUAGE_KEY] = language
