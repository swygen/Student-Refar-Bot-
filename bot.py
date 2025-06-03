import json
import asyncio
import os
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from keep_alive import keep_alive  # Flask সার্ভার চালানোর জন্য

# ==== Bot Config ====
TOKEN = "8067498359:AAEwY3O6A2CVueEm4LKSIaMp4F__ypL6ZdI"  # এখানে তোমার BotFather token বসাও
ADMIN_ID = 7647930808  # তোমার Telegram ID (যেখানে উত্তোলন মেসেজ যাবে)
GROUP_IDS = ['-1002414769217', '-1002676258756', '-1002657235869']

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

DB_FILE = "database.json"

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
📅 জয়েন তারিখ: {u.get("joined")}
"""

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
        InlineKeyboardButton("✅ Joined 🟢", callback_data="check_groups")
    )
    await msg.answer("🎉 স্বাগতম!\n\nঅনুগ্রহ করে নিচের তিনটি গ্রুপে যোগ দিন:", reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data == "check_groups")
async def check_groups(call: types.CallbackQuery):
    user_id = call.from_user.id
    try:
        for gid in GROUP_IDS:
            member = await bot.get_chat_member(gid, user_id)
            if member.status not in ["member", "administrator", "creator"]:
                raise Exception()

        keyboard = InlineKeyboardMarkup(row_width=2).add(
            InlineKeyboardButton("প্রোফাইল", callback_data="profile"),
            InlineKeyboardButton("রেফার করুন", callback_data="refer"),
            InlineKeyboardButton("উত্তোলন করুন", callback_data="withdraw"),
            InlineKeyboardButton("নোটিশ", callback_data="notice"),
            InlineKeyboardButton("সাপোর্ট", callback_data="support"),
            InlineKeyboardButton("ফ্রি ১০০ টাকা", callback_data="free100")
        )
        await call.message.edit_text("✅ আপনি সফলভাবে সব গ্রুপে যুক্ত হয়েছেন!", reply_markup=keyboard)
    except:
        await call.message.edit_text("❗ দয়া করে সবগুলো গ্রুপে যুক্ত হোন এবং আবার চেষ্টা করুন।")

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
    await call.message.edit_text(f"""📣 বন্ধুদের রেফার করুন এবং প্রতি সফল রেফারে ৫০ টাকা ইনকাম করুন!

🔗 আপনার রেফার লিংক: {link}

✅ মোট সফল রেফার: {u.get('referrals', 0)} """)

# ====== Withdraw Request Handling ======
user_withdraw_state = {}

@dp.callback_query_handler(lambda c: c.data == "withdraw")
async def withdraw(call: types.CallbackQuery):
    data = load_db()
    uid = str(call.from_user.id)
    u = data["users"][uid]

    if u.get("referrals", 0) < 20:
        await call.message.edit_text("❗ উত্তোলনের জন্য ন্যূনতম ২০টি সফল রেফার প্রয়োজন।")
    else:
        await call.message.answer("💳 আপনার বিকাশ/নগদ নম্বর পাঠান:")
        user_withdraw_state[uid] = True

@dp.message_handler()
async def handle_withdraw_number(msg: types.Message):
    uid = str(msg.from_user.id)
    if user_withdraw_state.get(uid):
        data = load_db()
        u = data["users"][uid]
        await bot.send_message(ADMIN_ID, f"📥 উত্তোলন রিকোয়েস্ট:\n\nUser: {msg.from_user.full_name}\nID: {msg.from_user.id}\nNumber: {msg.text}\nAmount: {u.get('balance')} টাকা")
        u["balance"] = 0
        save_db(data)
        await msg.answer("✅ উত্তোলন রিকোয়েস্ট সফলভাবে গ্রহণ করা হয়েছে।")
        user_withdraw_state.pop(uid)

@dp.callback_query_handler(lambda c: c.data == "notice")
async def notice(call: types.CallbackQuery):
    await call.message.edit_text("📌 গ্রুপগুলোতে যুক্ত থাকুন এবং নিয়ম মেনে কাজ করুন।")

@dp.callback_query_handler(lambda c: c.data == "support")
async def support(call: types.CallbackQuery):
    await call.message.edit_text("🆘 সাপোর্টের জন্য যোগাযোগ করুন:\n@CashShortcutAdmin")

@dp.callback_query_handler(lambda c: c.data == "free100")
async def free100(call: types.CallbackQuery):
    data = load_db()
    uid = str(call.from_user.id)
    if uid in data["claimed_100"]:
        await call.message.edit_text("❌ আপনি ইতিমধ্যে এই অফার গ্রহণ করেছেন।")
        return

    img_url = "https://i.postimg.cc/9Fw3SnvV/i-m-rich-portrait-young-freelancer-businessman-home-office-throws-cash-successful-deal-earnings-onli.jpg"
    keyboard = InlineKeyboardMarkup().add(
        InlineKeyboardButton("🌐 Go To Web", url="https://invest-sure.netlify.app/"),
        InlineKeyboardButton("✅ Submit", callback_data="submit100")
    )
    await bot.send_photo(chat_id=call.from_user.id, photo=img_url)
    await call.message.answer("""
🔔 সতর্কবার্তা 🔔
দয়া করে প্রথমে "Go To Web" এ গিয়ে একটি বৈধ একাউন্ট খুলুন এবং তারপরই তথ্য Submit করুন। ✅ অনুগ্রহ করে নিয়ম মেনে চলুন।
""", reply_markup=keyboard)

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
    await call.message.edit_text("✅ সফলভাবে ৫০ টাকা আপনার একাউন্টে যোগ হয়েছে।")

# ==== Run Bot ====
if __name__ == "__main__":
    keep_alive()  # Flask server চালু (Render/Replit এর জন্য)
    loop = asyncio.get_event_loop()

    async def main():
        print("🤖 Bot is starting...")
        await dp.start_polling()

    loop.create_task(main())
    loop.run_forever()
