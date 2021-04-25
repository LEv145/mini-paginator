import asyncio
from typing import List, Tuple, Optional, Coroutine
from copy import deepcopy

import discord

class Dialog():
    """Базовый класс, определяющий общее встроенное диалоговое взаимодействие."""

    def __init__(self, **kw):
        self.embed: Optional[discord.Embed] = None
        self.message: Optional[discord.Message] = None
        self.color: hex = kw.get("color") or kw.get("colour") or 0x000000

    async def quit(self, text: str = None) -> Coroutine:
        """
        Диалог выхода
        """

        if text is None:
            await self.message.delete()
        else:
            await self.message.edit(content=text, embed=None)
            await self.message.clear_reactions()

    async def update(self, text: str, color: hex = None, hide_author: bool = False) -> Coroutine:
        """
        Обновление диалога
        """

        if color is None:
            color = self.color

        self.embed.colour = color
        self.embed.title = text

        if hide_author:
            self.embed.set_author(name="")

        await self.edit(embed=self.embed)

    async def edit(self, text: str = None, embed: discord.Embed = None) -> Coroutine:
        """
        Редактирование диалога
        """

        await self.message.edit(content=text, embed=embed)

class EmbedPaginator(Dialog):
    """
    Представляет собой интерактивное меню, содержащее несколько вложений
    """

    def __init__(
        self,
        ctx: discord.ext.commands.Context,
        pages: List[discord.Embed],
        message: discord.Message = None,
        control_emojis: Tuple[str, str, str, str, str] = ("⏮", "◀", "▶", "⏭", "🔢", "📛"),
        page_format: str = "({}/{})",
        separator: str = " • ",
        enter_page: str = "`Введите номер стринички, куда хотите быстро переместиться: `"
    ):
        """
        Инициализируем новый пагинатор
        """
        super().__init__()

        self.ctx            = ctx
        self.pages          = pages
        self.message        = message
        self.page_format    = page_format
        self.separator      = separator
        self.control_emojis = control_emojis
        self.enter_page     = enter_page

    @property
    def formatted_pages(self) -> List[discord.Embed]:
        """
        Форматируем карасиво странички
        """

        pages = deepcopy(self.pages)
        max_page = len(pages)

        for index, page in enumerate(pages):
            text = self.page_format.format(index+1, max_page)

            if page.footer.text == discord.Embed.Empty:
                page.set_footer(text=text)
            else:
                text = f"{page.footer.text}{self.separator}{text}"

                if page.footer.icon_url == discord.Embed.Empty:
                    page.set_footer(text=text)
                else:
                    page.set_footer(
                        icon_url=page.footer.icon_url,
                        text=text
                    )
        return pages

    async def run(
        self,
        users: List[discord.User] = None,
        channel: discord.TextChannel = None,
        timeout: int  = 100
    ):
        """
        Запускаем
        """

        if users is None:
            users = [self.ctx.author]

        if channel is None:
            channel = self.ctx.channel

        self.embed = self.pages[0]

        if len(self.pages) == 1:
            self.message = await channel.send(embed=self.embed)
            return

        self.message = await channel.send(embed=self.formatted_pages[0])
        current_page_index = 0

        for emoji in self.control_emojis:
            await self.message.add_reaction(emoji)

        def check(r: discord.Reaction, u: discord.User) -> bool:
            res = (r.message.id == self.message.id) and (r.emoji in self.control_emojis)

            if len(users) > 0:
                res = res and u.id in [u1.id for u1 in users]
            return res

        while True:
            try:
                reaction, user = await self.ctx.bot.wait_for(
                    "reaction_add", check=check, timeout=timeout
                )
            except asyncio.TimeoutError:
                if not isinstance(
                    channel, discord.channel.DMChannel
                ) and not isinstance(channel, discord.channel.GroupChannel):
                    try:
                        await self.message.clear_reactions()
                    except discord.Forbidden:
                        pass
                return

            emoji = reaction.emoji
            max_index = len(self.pages) - 1

            if emoji == self.control_emojis[0]:
                load_page_index = 0

            elif emoji == self.control_emojis[1]:
                load_page_index = (
                    current_page_index - 1
                    if current_page_index > 0
                    else max_index
                )

            elif emoji == self.control_emojis[2]:
                load_page_index = (
                    current_page_index + 1
                    if current_page_index < max_index
                    else 0
                )

            elif emoji == self.control_emojis[3]:
                load_page_index = max_index

            elif emoji == self.control_emojis[4]:
                msg = await self.ctx.send(self.enter_page)
                load_page_index = await self.__get_page(users, current_page_index, max_index)
                await msg.delete()


            else:
                await self.message.delete()
                return

            await self.message.edit(embed=self.formatted_pages[load_page_index])
            if not isinstance(channel, discord.channel.DMChannel) and not isinstance(
                channel, discord.channel.GroupChannel
            ):
                try:
                    await self.message.remove_reaction(reaction, user)
                except discord.Forbidden:
                    pass

            current_page_index = load_page_index

    async def __get_page(self, users, current_page_index, max_index) -> int:
        """
        Получаем страничку путём ввода числа пользователем
        """

        def check(msg: discord.Message) -> bool:
            res = (msg.channel == self.ctx.channel)

            if len(users) > 0:
                res = res and msg.author.id in [user.id for user in users]
            return res

        try:
            msg = await self.ctx.bot.wait_for(
                "message", check=check, timeout=30
            )
        except asyncio.TimeoutError:
            return current_page_index
        else:
            content: str = msg.content
            if content.isdigit() and 0 <= int(content)-1 <= max_index:
                return int(content)-1
            else:
                return current_page_index


    @staticmethod
    def generate_sub_lists(origin_list: list, max_len: int = 25) -> List[list]:
        """
        Берет список элементов и преобразует его в список подсписков этих
        элементов с каждым подсписком, содержащим макс. элементы `max_len`
        Это может быть использовано для легкого разделения содержимого для встраиваемых полей на несколько страниц
        """

        if len(origin_list) > max_len:
            sub_lists = []

            while len(origin_list) > max_len:
                sub_lists.append(origin_list[:max_len])
                del origin_list[:max_len]
            sub_lists.append(origin_list)

        else:
            sub_lists = [origin_list]

        return sub_lists 
