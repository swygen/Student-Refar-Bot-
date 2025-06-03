import json
import asyncio
import os
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from keep_alive import keep_alive

# ==== Bot Config ====
TOKEN = "7627130832:AAF-09sxinEObzwlbMRMHALpW_x4EOsFS2w"
ADMIN_ID = 7647930808  # Admin user ID
GROUP_IDS = ['-1002414769217', '-1002676258756', '-1002657235869']  # Replace with your group IDs

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

DB_FILE = "database.json"

# === Database Handling ===
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

def user_profile(uid, data):
    u = data["users"].get(str(uid), {})
    return f"""👤 নাম: {u.get("name")}
🆔 ইউজার আইডি: {uid}
💰 ব্যালেন্স: {u.get("balance", 0)} টাকা
📅 জয়েন তারিখ: {u.get("joined")}
"""

# === Commands ===
@dp.message_handler(commands=['start'])
async def start_cmd(msg: types.Message):
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

    keyboard = InlineKeyboardMarkup().add(
        InlineKeyboardButton("✅ Join Check", callback_data="check_groups")
    )
    await msg.answer("🎉 স্বাগতম! অনুগ্রহ করে নিচের গ্রুপগুলোতে যুক্ত হন:", reply_markup=keyboard)

# === Group Join Check ===
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
        await call.message.edit_text("✅ সব গ্রুপে যুক্ত হয়েছেন!", reply_markup=keyboard)
    except:
        await call.message.edit_text("❗ অনুগ্রহ করে সব গ্রুপে যুক্ত হন ও আবার চেষ্টা করুন।")

# === Callback Handlers ===
@dp.callback_query_handler(lambda c: c.data == "profile")
async def profile(call: types.CallbackQuery):
    data = load_db()
    await call.message.edit_text(user_profile(call.from_user.id, data))

@dp.callback_query_handler(lambda c: c.data == "refer")
async def refer(call: types.CallbackQuery):
    data = load_db()
    uid = str(call.from_user.id)
    u = data["users"][uid]
    link = get_referral_link(uid)
    await call.message.edit_text(f"""📣 বন্ধুদের রেফার করুন!

🔗 আপনার রেফার লিংক: {link}
✅ সফল রেফার: {u.get('referrals', 0)}""")

user_withdraw_state = {}

@dp.callback_query_handler(lambda c: c.data == "withdraw")
async def withdraw(call: types.CallbackQuery):
    data = load_db()
    uid = str(call.from_user.id)
    u = data["users"][uid]
    if u.get("referrals", 0) < 20:
        await call.message.edit_text("❗ উত্তোলনের জন্য কমপক্ষে ২০টি রেফার প্রয়োজন।")
    else:
        await call.message.answer("📥 বিকাশ/নগদ নম্বর পাঠান:")
        user_withdraw_state[uid] = True

@dp.message_handler()
async def handle_withdraw_number(msg: types.Message):
    uid = str(msg.from_user.id)
    if user_withdraw_state.get(uid):
        data = load_db()
        u = data["users"][uid]
        await bot.send_message(ADMIN_ID, f"📥 উত্তোলন:\nনাম: {msg.from_user.full_name}\nID: {uid}\nNumber: {msg.text}\nAmount: {u['balance']} টাকা")
        u["balance"] = 0
        save_db(data)
        await msg.answer("✅ রিকোয়েস্ট গ্রহণ করা হয়েছে।")
        user_withdraw_state.pop(uid)

@dp.callback_query_handler(lambda c: c.data == "notice")
async def notice(call: types.CallbackQuery):
    await call.message.edit_text("📢 সব নিয়ম মেনে কাজ করুন।")

@dp.callback_query_handler(lambda c: c.data == "support")
async def support(call: types.CallbackQuery):
    await call.message.edit_text("🆘 Admin: @YourSupportUsername")

@dp.callback_query_handler(lambda c: c.data == "free100")
async def free100(call: types.CallbackQuery):
    data = load_db()
    uid = str(call.from_user.id)
    if uid in data["claimed_100"]:
        await call.message.edit_text("❌ আপনি আগে এই অফার নিয়েছেন।")
        return
    keyboard = InlineKeyboardMarkup().add(
        InlineKeyboardButton("🌐 Go To Web", url="https://yourwebsite.com"),
        InlineKeyboardButton("✅ Submit", callback_data="submit100")
    )
    await call.message.answer("🎁 অফার পেতে ওয়েবসাইটে একাউন্ট খুলে Submit দিন।", reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data == "submit100")
async def submit100(call: types.CallbackQuery):
    data = load_db()
    uid = str(call.from_user.id)
    if uid in data["claimed_100"]:
        await call.message.edit_text("❌ আপনি আগে ক্লেইম করেছেন।")
        return
    data["claimed_100"].append(uid)
    data["users"][uid]["balance"] += 50
    save_db(data)
    await call.message.edit_text("✅ ৫০ টাকা আপনার ব্যালেন্সে যোগ হয়েছে।")

# ==== Run Bot ====
if __name__ == "__main__":
    keep_alive()  # Flask server for uptime
    loop = asyncio.get_event_loop()

    async def main():
        print("🤖 Bot is running...")
        await dp.start_polling()

    loop.create_task(main())
    loop.run_forever()
