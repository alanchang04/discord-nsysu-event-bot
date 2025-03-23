import discord
from discord.ext import commands, tasks
from discord.ext.commands import HybridCommand
from discord.ui import View, Button
from discord import Interaction, app_commands
import requests
from bs4 import BeautifulSoup as bs4
from datetime import datetime
import json
import os
from dotenv import load_dotenv # for bot security

# 設置 Bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

LAST_ANNOUNCEMENT_FILE = 'last_announcement.json'




# 儲存最新公告
def save_last_announcement(announcement):
    with open(LAST_ANNOUNCEMENT_FILE, 'w', encoding='utf-8') as f:
        json.dump(announcement, f, ensure_ascii=False)

def load_last_announcement():
    try:
        if os.path.exists(LAST_ANNOUNCEMENT_FILE):
            with open(LAST_ANNOUNCEMENT_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        return None
    return None

def normalize_date(date_str):
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').strftime('%Y-%m-%d')
    except:
        return date_str
async def scrape_announcements():
    """爬取公告資訊"""
    try:
        url = "https://www.nsysu.edu.tw/p/422-1000-1314.php?Lang=zh-tw"
        response = requests.get(url)
        response.encoding = 'utf-8'
        soup = bs4(response.text, "html.parser")

        rows = soup.select('div.minner table tbody tr')  # 確保選擇器正確匹配
        announcements = []

        for row in rows:
            # 提取日期
            date_tag = row.select_one('div.d-txt')
            date = date_tag.text.strip() if date_tag else "N/A"

            # 提取標題與連結
            link_tag = row.select_one('a')
            title = link_tag.text.strip() if link_tag else "無標題公告"
            link = link_tag['href'] if link_tag and 'href' in link_tag.attrs else "#"

            # 組裝完整連結
            full_link = f"https://www.nsysu.edu.tw{link}" if link.startswith("/") else link

            announcements.append({
                'date': normalize_date(date),
                'content': title,
                'link': full_link
            })

        return announcements
    except Exception as e:
        print(f"爬取資料時發生錯誤: {e}")
        return []

def search_keyword(announcements, keyword):
    """搜尋關鍵字"""
    results = []
    for announcement in announcements:
        if keyword in announcement['content']:
            results.append(announcement)
    return results

def split_message(message):
    """將長訊息分割成小於 2000 字元的片段"""
    messages = []
    current_message = ""
    
    for line in message.split('\n'):
        if len(current_message + line + '\n') > 1900:  # 留一些餘裕
            messages.append(current_message)
            current_message = line + '\n'
        else:
            current_message += line + '\n'
    
    if current_message:
        messages.append(current_message)
    
    return messages

@bot.hybrid_command(name='latest', description="顯示所有最新公告")
async def show_latest(ctx):
    """顯示所有最新公告"""
    try:
        announcements = await scrape_announcements()
        if not announcements:
            await ctx.send("抱歉，無法獲取公告資訊。")
            return

        # 讀取上次儲存的最新公告
        last_announcement = load_last_announcement()
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        response = f"📌 **中山大學最新公告（{current_time}）：**\n\n"

        separator_added = False  # 確保只插入一次「先前公告」
        new_announcements = []   # 收集新公告

        # 判斷公告是否為最新或先前公告
        for announcement in announcements:
            # 如果找到了與上次相同的公告，插入分隔線
            if (last_announcement and
                announcement['date'] == last_announcement['date'] and
                announcement['content'] == last_announcement['content']):
                separator_added = True
                break
            new_announcements.append(announcement)

        # 添加新公告
        if new_announcements:
            for i, announcement in enumerate(new_announcements):
                icons = ['📢', '📣', '🔔', '📋', '📝']
                current_icon = icons[i % len(icons)]
                link_text = f"[點擊查看詳情]({announcement['link']})"
                response += f"{current_icon} **{announcement['date']}** - {announcement['content']} {link_text}\n"

        # 插入分隔線
        response += "\n" + "=" * 50 + "\n📜 **以下為先前公告**\n" + "=" * 50 + "\n\n"

        # 添加「先前公告」
        for i, announcement in enumerate(announcements[len(new_announcements):]):
            icons = ['📢', '📣', '🔔', '📋', '📝']
            current_icon = icons[i % len(icons)]
            link_text = f"[點擊查看詳情]({announcement['link']})"
            response += f"{current_icon} **{announcement['date']}** - {announcement['content']} {link_text}\n"

        # 儲存最新的公告
        if announcements:
            save_last_announcement(announcements[0])

        # 分割長訊息並發送
        messages = split_message(response)
        for msg in messages:
            await ctx.send(msg)

    except Exception as e:
        await ctx.send(f"執行命令時發生錯誤: {e}")

@bot.hybrid_command(name='search', description="搜尋包含特定關鍵字的公告")
async def search_announcements(ctx, keyword: str):
    """搜尋特定關鍵字"""
    try:
        announcements = await scrape_announcements()
        results = [a for a in announcements if keyword in a['content']]

        if not results:
            await ctx.send(f"找不到包含關鍵字 '{keyword}' 的公告。")
            return

        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        response = f"🔍 **包含關鍵字 '{keyword}' 的公告（{current_time}）：**\n\n"

        for i, result in enumerate(results):
            icons = ['📢', '📣', '🔔', '📋', '📝']
            current_icon = icons[i % len(icons)]
            link_text = f"[點擊查看詳情]({result['link']})"
            response += f"{current_icon} **{result['date']}** - {result['content']} {link_text}\n"

        # 分割長訊息並發送
        messages = split_message(response)
        for msg in messages:
            await ctx.send(msg)
    except Exception as e:
        await ctx.send(f"搜尋時發生錯誤: {e}")


# 活動發起和報名
# 儲存活動資料
activities = {}

class ActivityView(discord.ui.View):
    def __init__(self, activity_id: int):
        super().__init__()
        self.activity_id = activity_id

    @discord.ui.button(label="報名參加", style=discord.ButtonStyle.green)
    async def join_activity(self, interaction: discord.Interaction, button: discord.ui.Button):
        """用戶按下報名按鈕時觸發"""
        activity = activities.get(self.activity_id)
        if activity:
            user_mention = interaction.user.mention
            if user_mention in activity["participants"]:
                await interaction.response.send_message("你已經報名過了！", ephemeral=True)
            else:
                activity["participants"].append(user_mention)  # 加入參與者清單
                # 更新 Embed 來顯示最新的參與者
                participants = ", ".join(activity["participants"]) if activity["participants"] else "無人報名"
                embed = discord.Embed(
                    title=f"活動：{activity['name']}",
                    description=(
                        f"**活動ID：{self.activity_id}**\n"
                        f"日期：{activity['date']}\n時間：{activity['time']}\n"
                        f"發起者：{activity['creator']}\n"
                        f"**目前參與者**：{participants}"
                    )
                )
                await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.send_message("找不到這個活動！", ephemeral=True)


    @discord.ui.button(label="取消報名", style=discord.ButtonStyle.red)
    async def unregister_button(self, interaction: Interaction, button: Button):
        """處理取消報名按鈕的交互"""
        activity = activities.get(self.activity_id)

        if not activity:
            await interaction.response.send_message("找不到這個活動！", ephemeral=True)
            return

        user_mention = interaction.user.mention  # 用 @用戶名 做為標識

        if user_mention in activity["participants"]:
            # 從參與者名單中移除
            activity["participants"].remove(user_mention)

            # 更新 Embed，顯示新的參與者名單
            participants = ", ".join(activity["participants"]) if activity["participants"] else "無人報名"
            embed = discord.Embed(
                title=f"活動：{activity['name']}",
                description=(
                    f"**活動ID：{self.activity_id}**\n"
                    f"日期：{activity['date']}\n時間：{activity['time']}\n"
                    f"發起者：{activity['creator']}\n"
                    f"**目前參與者**：{participants}"
                )
            )
            # 編輯原始訊息來顯示最新資訊
            await interaction.response.edit_message(embed=embed, view=self)
            await interaction.followup.send(f"{interaction.user.name} 已取消報名！", ephemeral=True)
        else:
            await interaction.response.send_message("您未報名，無法取消！", ephemeral=True)


@bot.tree.command(name="create_activity", description="創建一個新的活動 - 日期格式:YYYY/MM/DD 時間格式:24小時制")
@app_commands.rename(
    name="name",
    date="date_with_slash",
    time="time_24h"
)
async def create_activity(
    interaction: discord.Interaction,
    name: str,
    date: str,
    time: str
):
    """發起活動"""
    activity_id = len(activities) + 1
    activities[activity_id] = {
        "name": name,
        "date": date,
        "time": time,
        "creator": interaction.user.mention,
        "participants": []  # 初始參與者為空
    }
    # Embed 中增加目前參與者資訊
    embed = discord.Embed(
        title=f"活動：{name}",
        description=(
            f"**活動ID：{activity_id}**\n"
            f"日期：{date}\n時間：{time}\n"
            f"發起者：{interaction.user.mention}\n"
            f"**目前參與者**：無人報名"
        )
    )
    view = ActivityView(activity_id)  # 綁定互動按鈕
    await interaction.response.send_message(embed=embed, view=view)

@bot.hybrid_command(name="delete_activity", description="刪除指定活動")
async def delete_activity(ctx, activity_id: int):
    """刪除活動"""
    activity = activities.pop(activity_id, None)
    if activity:
        await ctx.send(f"活動 **{activity['name']}** 已被刪除！")
    else:
        await ctx.send("未找到該活動！")

@bot.hybrid_command(name="list_activities", description="列出所有活動")
async def list_activities(ctx):
    """列出所有活動"""
    if activities:
        response = "\n".join([
            f"**ID: {k}** | 名稱: {v['name']} | 日期: {v['date']} | 時間: {v['time']}\n"
            f"目前報名者：{', '.join(v['participants']) if v['participants'] else '無人報名'}"
            for k, v in activities.items()
        ])
        await ctx.send(f"目前活動列表：\n{response}")
    else:
        await ctx.send("目前沒有任何活動！")

#指令說明
@bot.hybrid_command(name='commands', description="顯示指令說明")
async def show_commands(ctx):
    """顯示指令說明"""
    commands_text = """
📢 **可用指令列表**：
1️⃣ 公告相關：
• **!latest** 或 **/latest** - 顯示所有最新公告
• **!search [關鍵字]** 或 **/search [關鍵字]** - 搜尋包含特定關鍵字的公告
  範例：!search 國科 或 /search 國科
• **!commands** 或 **/commands** - 顯示此指令說明

2️⃣ 活動相關：
• **/create_activity [活動名稱] [日期] [時間]** - 發起活動
  範例：/create_activity 團建 2024-12-10 18:30
• **!delete_activity [活動ID]** 或 **/delete_activity [活動ID]** - 刪除指定活動
  範例：!delete_activity 1
• **!list_activities** 或 **/list_activities** - 列出所有活動
"""
    await ctx.send(commands_text)
# Bot 事件和命令
GUILD_ID = discord.Object(id=1299351932502278234)  # 替換為您的伺服器 ID

@bot.event
async def on_ready():
    try:
        await bot.tree.sync(guild=GUILD_ID)  # 同步指令至指定伺服器
        print("sync already")
    except Exception as e:
        print(f"sync Error: {e}")

    print(f"Bot starts: {bot.user}")

@tasks.loop(hours=1)
async def check_updates():
    """定時檢查更新"""
    try:
        announcements = await scrape_announcements()
    except Exception as e:
        print(f"檢查更新時發生錯誤: {e}")

# 運行 Bot


load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
bot.run(TOKEN)


if __name__ == "__main__":
    run_bot()