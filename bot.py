import json
import asyncio
import os
from datetime import datetime

from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from keep_alive import keep_alive  # Uptime server (like Replit)

# ==== Bot Configuration ====
TOKEN = "7326530944:AAEj883zJaEfC1uj0B3UelL9Y9Q0_WAxy3Y"  # Replace with actual bot token
ADMIN_ID = 7647930808  # Replace with your Telegram ID

GROUPS = {
    "Join 1": "https://t.me/CashShortcutBD",
    "Join 2": "https://t.me/EarningZone0BD",
    "Join 3": "https://t.me/EarnopediaBD"
}
GROUP_IDS = [
    "-1002676258756",
    "-1002657235869",
    "-1002414769217"
]  # Replace with actual group/channel IDs

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)
DB_FILE = "database.json"

# ==== Database Operations ====
def load_db():
    if not os.path.exists(DB_FILE):
        return {"users": {}, "claimed_100": []}
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {"users": {}, "claimed_100": []}

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=2)

def get_referral_link(user_id):
    return f"https://t.me/Student_refer_bot?start={user_id}"

def format_profile(uid, data):
    u = data["users"].get(str(uid), {})
    return f"""👤 নাম: {u.get("name")}
🆔 ইউজার আইডি: {uid}
💰 ব্যালেন্স: {u.get("balance", 0)} টাকা
📅 জয়েন তারিখ: {u.get("joined")}"""

# ==== Bot Commands ====
@dp.message_handler(commands=['start'])
async def start_command(msg: types.Message):
    uid = str(msg.from_user.id)
    data = load_db()

    if uid not in data["users"]:
        ref = msg.get_args()
        if ref and ref != uid and ref in data["users"]:
            data["users"][ref]["referrals"] = data["users"][ref].get("referrals", 0) + 1
            data["users"][ref]["balance"] = data["users"][ref].get("balance", 0) + 50

        data["users"][uid] = {
            "name": msg.from_user.full_name,
            "balance": 0,
            "joined": datetime.now().strftime("%Y-%m-%d"),
            "referrals": 0
        }
        save_db(data)

    buttons = [InlineKeyboardButton(text=name, url=url) for name, url in GROUPS.items()]
    buttons.append(InlineKeyboardButton("✅ Continue 🟢", callback_data="check_groups"))
    keyboard = InlineKeyboardMarkup(row_width=1).add(*buttons)

    await msg.answer("🔰 প্রথমে নিচের গ্রুপগুলোতে যোগ দিন:", reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data == "check_groups")
async def check_groups(call: types.CallbackQuery):
    user_id = call.from_user.id
    try:
        for gid in GROUP_IDS:
            member = await bot.get_chat_member(gid, user_id)
            if member.status not in ["member", "administrator", "creator"]:
                raise Exception()

        keyboard = InlineKeyboardMarkup(row_width=2).add(
            InlineKeyboardButton("📄 প্রোফাইল", callback_data="profile"),
            InlineKeyboardButton("📣 রেফার", callback_data="refer"),
            InlineKeyboardButton("💳 উত্তোলন", callback_data="withdraw"),
            InlineKeyboardButton("🎁 ফ্রি ৫০ টাকা", callback_data="free100"),
            InlineKeyboardButton("📢 নোটিশ", callback_data="notice"),
            InlineKeyboardButton("🆘 সাপোর্ট", callback_data="support")
        )
        await call.message.edit_text("✅ সফলভাবে যুক্ত হয়েছেন! মেনু থেকে অপশন বেছে নিন:", reply_markup=keyboard)
    except:
        await call.message.edit_text("❌ অনুগ্রহ করে সবগুলো গ্রুপে যুক্ত হন এবং পুনরায় চেষ্টা করুন।")

@dp.callback_query_handler(lambda c: c.data == "profile")
async def profile(call: types.CallbackQuery):
    data = load_db()
    await call.message.edit_text(format_profile(call.from_user.id, data))

@dp.callback_query_handler(lambda c: c.data == "refer")
async def refer(call: types.CallbackQuery):
    data = load_db()
    uid = str(call.from_user.id)
    link = get_referral_link(uid)
    referrals = data["users"][uid].get("referrals", 0)
    await call.message.edit_text(f"📣 রেফার লিংক: 🔗 {link}\n✅ সফল রেফার: {referrals}")

user_withdraw_state = {}

@dp.callback_query_handler(lambda c: c.data == "withdraw")
async def withdraw(call: types.CallbackQuery):
    uid = str(call.from_user.id)
    data = load_db()
    user = data["users"].get(uid, {})
    if user.get("referrals", 0) < 20:
        await call.message.edit_text("❗ উত্তোলনের জন্য অন্তত ২০টি রেফার লাগবে।")
    else:
        await call.message.answer("📥 আপনার বিকাশ/নগদ নম্বর পাঠান:")
        user_withdraw_state[uid] = True

@dp.message_handler()
async def handle_number(msg: types.Message):
    uid = str(msg.from_user.id)
    if user_withdraw_state.get(uid):
        data = load_db()
        user = data["users"][uid]
        await bot.send_message(ADMIN_ID, f"📤 উত্তোলন রিকোয়েস্ট\nনাম: {msg.from_user.full_name}\nID: {uid}\nনম্বর: {msg.text}\nপরিমাণ: {user['balance']} টাকা")
        user["balance"] = 0
        save_db(data)
        await msg.answer("✅ রিকোয়েস্ট গ্রহণ করা হয়েছে।")
        user_withdraw_state.pop(uid)

@dp.callback_query_handler(lambda c: c.data == "notice")
async def notice(call: types.CallbackQuery):
    await call.message.edit_text("📌 নিয়মিতভাবে গ্রুপগুলোতে সক্রিয় থাকুন।")

@dp.callback_query_handler(lambda c: c.data == "support")
async def support(call: types.CallbackQuery):
    await call.message.edit_text("🆘 সাপোর্টের জন্য যোগাযোগ করুন: @YourSupportUsername")

@dp.callback_query_handler(lambda c: c.data == "free100")
async def free100(call: types.CallbackQuery):
    data = load_db()
    uid = str(call.from_user.id)
    if uid in data["claimed_100"]:
        await call.message.edit_text("❌ আপনি এই অফারটি ইতিমধ্যে গ্রহণ করেছেন।")
        return

    keyboard = InlineKeyboardMarkup().add(
        InlineKeyboardButton("🌐 Visit Website", url="http://invest-sure.netlify.app"),
        InlineKeyboardButton("✅ Submit", callback_data="submit100")
    )
    await call.message.answer("🎁 ওয়েবসাইটে গিয়ে রেজিস্ট্রেশন সম্পন্ন করে Submit দিন:", reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data == "submit100")
async def submit100(call: types.CallbackQuery):
    data = load_db()
    uid = str(call.from_user.id)
    if uid in data["claimed_100"]:
        await call.message.edit_text("❌ আপনি ইতিমধ্যে ক্লেইম করেছেন।")
        return

    data["claimed_100"].append(uid)
    data["users"][uid]["balance"] += 50
    save_db(data)
    await call.message.edit_text("✅ ৫০ টাকা ব্যালেন্সে যোগ হয়েছে।")

# ==== Start Bot ====
if __name__ == "__main__":
    keep_alive()

    loop = asyncio.get_event_loop()

    async def main():
        print("🤖 Bot is running...")
        await dp.start_polling()

    loop.create_task(main())
    loop.run_forever()
