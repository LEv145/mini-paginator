import asyncio
from contextlib import suppress
from typing import List, Optional, Tuple

from discord import (
	Embed,
	Message,
	User,
	Reaction,
	TextChannel
)
from discord.ext import commands
from discord.errors import DiscordException
from more_itertools import chunked


class ForwardBackwardList(object):
	def __init__(self, items: list):
		self.items = items
		self.max_index = len(self)-1
		self.index = 0

	def forward(self):
		if self.index+1 > self.max_index:
			self.index = 0
		else:
			self.index += 1

	def back(self):
		if self.index-1 < 0:
			self.index = self.max_index
		else:
			self.index -= 1

	def set(self, index: int):
		assert 0 <= index <= self.max_index
		self.index = index

	@property
	def current(self):
		return self.items[self.index]

	def __len__(self):
		return len(self.items)

class Dialog(object):
	"""Базовый класс, определяющий общее встроенное диалоговое взаимодействие."""
	embed: Embed
	message: Message

	async def edit(self, text: Optional[str] = None, embed: Optional[Embed] = None) -> None:
		"""
		Редактирование диалога
		"""

		await self.message.edit(content=text, embed=embed)

	async def quit(self, text: Optional[str] = None) -> None:
		"""
		Диалог выхода
		"""

		with suppress(DiscordException):
			if text is None:
				await self.message.delete()
			else:
				await self.message.edit(content=text, embed=None)
				await self.message.clear_reactions()

class CheckPaginator(Dialog):
	"""
	Интерактивное меню с ожидаем ответ пользователя да или нет
	"""

	def __init__(
		self,
		ctx: commands.Context,
		embed: Embed,
		control_emojis: Tuple[str, str] = ('✅', '📛')
	):
		self.ctx = ctx
		self.embed = embed
		self.control_emojis = control_emojis

	async def run(
		self,
		maybe_users: Optional[List[User]] = None,
		maybe_channel: Optional[TextChannel] = None,
		timeout: int = 100
	) -> bool:
		"""
		Запускаем
		"""

		users = maybe_users or [self.ctx.author]
		channel = maybe_channel or self.ctx.channel

		self.message: Message = await channel.send(embed=self.embed)

		for i in self.control_emojis:
			await self.message.add_reaction(i)

		def check(reaction: Reaction, user: User):
			return (
				user.id in users and
				reaction.emoji in self.control_emojis and
				self.message.id == reaction.message.id
			)

		try:
			reaction, _ = await self.ctx.bot.wait_for('reaction_add', timeout=timeout, check=check)
		except asyncio.TimeoutError as error:
			with suppress(DiscordException):
				await self.message.clear_reactions()
			raise error
		else:
			with suppress(DiscordException):
				await self.message.clear_reactions()

			return reaction.emoji == self.control_emojis[0]


class EmbedPaginator(Dialog):
	"""
	Представляет собой интерактивное меню, содержащее несколько вложений
	"""

	def __init__(
		self,
		ctx: commands.Context,
		pages: List[Embed],
		control_emojis: Tuple[str, str, str, str, str, str] = ("⏮", "◀", "▶", "⏭", "🔢", "📛"),
		page_format: str = "({}/{})",
		separator: str = " • ",
		enter_page: str = "`Введите номер стринички, куда хотите быстро переместиться: `",
		quit_text: Optional[str] = None
	):
		self.ctx = ctx
		self.pages = pages
		self.page_format = page_format
		self.separator = separator
		self.control_emojis = control_emojis
		self.enter_page = enter_page
		self.quit_text = quit_text

	def formatting_pages(self) -> ForwardBackwardList:
		"""
		Форматируем красиво странички
		"""
		max_page = len(self.pages)

		for index, page in enumerate(self.pages):
			text = self.page_format.format(index+1, max_page)

			if page.footer.text == Embed.Empty:
				page.set_footer(text=text)
			else:
				text = f"{page.footer.text}{self.separator}{text}"

				if page.footer.icon_url == Embed.Empty:
					page.set_footer(text=text)
				else:
					page.set_footer(
						icon_url=page.footer.icon_url,
						text=text
					)
		return ForwardBackwardList(self.pages)

	async def run(
		self,
		maybe_users: Optional[List[User]] = None,
		maybe_channel: Optional[TextChannel] = None,
		timeout: int  = 100
	) -> None:
		"""
		Запускаем
		"""

		users = maybe_users or [self.ctx.author]
		channel = maybe_channel or self.ctx.channel

		# Форматируем странички
		pages = self.formatting_pages()

		if len(self.pages) == 1:
			self.message = await channel.send(embed=pages.current)
			return

		self.message: Message = await channel.send(embed=pages.current)

		for emoji in self.control_emojis:
			await self.message.add_reaction(emoji)

		def check(reaction: Reaction, user: User):
			result = reaction.message.id == self.message.id and reaction.emoji in self.control_emojis

			if users:
				return result and user in users
			else:
				return result

		while True:
			try:
				reaction, user = await self.ctx.bot.wait_for(
					"reaction_add", check=check, timeout=timeout
				)
			except asyncio.TimeoutError:
				with suppress(DiscordException):
					await self.message.clear_reactions()
				return
			emoji = reaction.emoji

			if emoji == self.control_emojis[0]:
				pages.set(0)

			elif emoji == self.control_emojis[1]:
				pages.back()

			elif emoji == self.control_emojis[2]:
				pages.forward()

			elif emoji == self.control_emojis[3]:
				pages.set(pages.max_index)

			elif emoji == self.control_emojis[4]:
				enter_page_message: Message = await self.ctx.send(self.enter_page)
				index = await self._get_page(users)
				if index:
					with suppress(AssertionError):
						pages.set(index)
				await enter_page_message.delete()

			else:
				await self.quit(self.quit_text)

			await self.message.edit(embed=pages.current)
			with suppress(DiscordException):
				await self.message.remove_reaction(reaction, user)

	@staticmethod
	def generate_sub_lists(iterable: list, max_len: int = 25) -> List[list]:
		"""
		Берет список элементов и преобразует его в список подсписков этих
		элементов с каждым подсписком, содержащим макс. элементы `max_len`
		Это может быть использовано для легкого разделения содержимого для встраиваемых полей на несколько страниц
		"""
		return list(chunked(iterable, max_len))

	async def _get_page(self, users: List[User]) -> Optional[int]:
		"""
		Получаем страничку путём ввода числа пользователем
		"""

		def check(msg: Message):
			res = (msg.channel == self.ctx.channel)

			if len(users) > 0:
				res = res and msg.author.id in [user.id for user in users]
			return res

		try:
			msg = await self.ctx.bot.wait_for(
				"message", check=check, timeout=30
			)
		except asyncio.TimeoutError:
			return None
		else:
			content: str = msg.content
			if content.isdigit():
				return int(content)-1
			else:
				return None
