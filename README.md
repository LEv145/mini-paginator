# mini-paginator
Mini-paginator for discord.py

# Install

```
python3 -m pip install -U mini-paginator
```
```
python3 -m pip install -U git+https://github.com/LEv145/mini-paginator
```

# HOW TO USE
```py
import mini_paginaror

@bot.command()
async def test_paginate(ctx):
    pages = [
        Embed(title="test page 1", description="Page1", color=0x115599),
        Embed(title="test page 2", description="Page2.", color=0x5599ff),
        Embed(title="test page 3", description="Page3", color=0x191638)
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
```

# TODO
- Поднять свою ленивую задницу и написать мини доки
