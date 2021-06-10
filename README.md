# mini-paginator
Mini-paginator for discord.py

# Install
```
python3 -m pip install -U git+https://github.com/LEv145/mini-paginator
```

# HOW TO USE
```py
import mini_paginaror

@bot.command()
async def test_paginate(ctx: commands.Context):
    pages = [
        Embed(title="Test page 1", description="Page1", color=0x111111),
        Embed(title="Test page 2", description="Page2", color=0x222222),
        Embed(title="Test page 3", description="Page3", color=0x333333)
    ]
    
    paginator = mini_paginaror.EmbedPaginator(
        ctx, 
        pages=pages, 
        page_format="[{}\{}]",
        control_emojis=("⏮", "◀", "▶", "⏭", "🔢", "❌"),
        separator=" * ",
        enter_page="Enter num page: "
    )
    await paginator.run(timeout=60)

@bot.command()
async def test_ckeck_paginator(ctx: commands.Context):
        embed = Embed(title="How are you?", color=0x111111)
        paginator = mini_paginaror.CheckPaginator(ctx, embed=embed)
        try:
                check = await paginator.run()
        except asyncio.TimeoutError:
                await ctx.send("Opss..Time is over.")
        else:
                if  check:
                        await ctx.send("Coool!!!")
                else:
                        await ctx.send("Oh..Good luck, I hope you feel better.")
        
```

