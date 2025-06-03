import json
import asyncio
import os
from datetime import datetime

from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.exceptions import ChatNotFound, BadRequest
from keep_alive import keep_alive  # তোমার সার্ভার যদি থাকে

TOKEN = "7902453976:AAFaxX_P92W8jpOCrkMrM2DaKB3xzvkSQus"
ADMIN_ID = 7647930808  # তোমার আইডি

GROUPS = {
    "Group 1": "https://t.me/CashShortcutBD",
    "Group 2": "https://t.me/EarningZone0BD",
    "Group 3": "https://t.me/EarnopediaBD"
}

GROUP_IDS = [
    "-1002676258756",
    "-1002657235869",
    "-1002414769217"
]

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)
DB_FILE = "database.json"


def load_db():
    if not os.path.exists(DB_FILE):
        return {"users": {}, "claimed_50": [], "joined_users": []}
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {"users": {}, "claimed_50": [], "joined_users": []}


def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=2)


def format_profile(uid, data):
    user = data["users"].get(str(uid), {})
    name = user.get("name", "অজানা")
    balance = user.get("balance", 0)
    referrals = user.get("referrals", 0)
    joined = user.get("joined", "N/A")

    text = (
        f"👤 নাম: {name}\n"
        f"🆔 ইউজার আইডি: {uid}\n"
        f"💰 ব্যালেন্স: {balance} টাকা\n"
        f"✅ সফল রেফার: {referrals}\n"
        f"📅 জয়েন তারিখ: {joined}"
    )
    return text


def get_referral_link(user_id):
    return f"https://t.me/Student_Refer_bot?start={user_id}"


@dp.message_handler(commands=["start"])
async def start_handler(msg: types.Message):
    uid = str(msg.from_user.id)
    name = msg.from_user.full_name
    data = load_db()

    # নতুন ইউজার হলে ডাটাবেজে যুক্ত করো (রেফারেল চেক সহ)
    if uid not in data["users"]:
        ref = msg.get_args()
        if ref and ref != uid and ref in data["users"]:
            data["users"][ref]["referrals"] = data["users"][ref].get("referrals", 0) + 1
            data["users"][ref]["balance"] = data["users"][ref].get("balance", 0) + 50

        data["users"][uid] = {
            "name": name,
            "balance": 0,
            "joined": datetime.now().strftime("%Y-%m-%d"),
            "referrals": 0
        }
        save_db(data)

    # যদি আগেই জয়েন করা থাকে, সরাসরি মেনু দেখাও
    if uid in data.get("joined_users", []):
        profile_text = format_profile(uid, data)
        menu_text = (
            f"স্বাগতম, {name}!\n\n"
            f"{profile_text}\n\n"
            "📄 প্রোফাইল দেখতে /profile\n"
            "📣 রেফার করতে /refer\n"
            "💳 উত্তোলন করতে /withdraw\n"
            "🎁 ফ্রি ৫০ টাকা পেতে /free50\n"
            "📢 নোটিশ পেতে /notice\n"
            "🆘 সাপোর্ট পেতে /support"
        )
        await msg.answer(menu_text)
        return

    # জয়েন করতে হবে, তাই গ্রুপ বাটন ও JOINED DONE 👍🏻 বাটন দেখাও
    buttons = [InlineKeyboardButton(text=name, url=url) for name, url in GROUPS.items()]
    buttons.append(InlineKeyboardButton("JOINED DONE 👍🏻", callback_data="check_join"))
    keyboard = InlineKeyboardMarkup(row_width=1).add(*buttons)

    await msg.answer(
        f"প্রিয় {name}, প্রথমে নিচের গ্রুপগুলোতে জয়েন করুন এবং তারপর 'JOINED DONE 👍🏻' বাটনে ক্লিক করুন।",
        reply_markup=keyboard
    )


@dp.callback_query_handler(lambda c: c.data == "check_join")
async def check_join_handler(call: types.CallbackQuery):
    uid = call.from_user.id
    uid_str = str(uid)
    data = load_db()

    not_joined_groups = []

    for gid in GROUP_IDS:
        try:
            member = await bot.get_chat_member(gid, uid)
            if member.status not in ["member", "administrator", "creator"]:
                not_joined_groups.append(gid)
        except (ChatNotFound, BadRequest):
            not_joined_groups.append(gid)

    if not_joined_groups:
        await call.answer("❌ আপনি এখনও সব গ্রুপে জয়েন হননি। দয়া করে সব গ্রুপ জয়েন করুন।", show_alert=True)
        return

    # জয়েন নিশ্চিত, ডাটাবেজে সেভ করো
    if uid_str not in data.get("joined_users", []):
        data.setdefault("joined_users", []).append(uid_str)
        save_db(data)

    profile_text = format_profile(uid_str, data)
    menu_text = (
        f"✅ শুভকামনা {call.from_user.full_name}, আপনি সফলভাবে সব গ্রুপ জয়েন করেছেন!\n\n"
        f"{profile_text}\n\n"
        "📄 প্রোফাইল দেখতে /profile\n"
        "📣 রেফার করতে /refer\n"
        "💳 উত্তোলন করতে /withdraw\n"
        "🎁 ফ্রি ৫০ টাকা পেতে /free50\n"
        "📢 নোটিশ পেতে /notice\n"
        "🆘 সাপোর্ট পেতে /support"
    )
    await call.message.edit_text(menu_text)


@dp.message_handler(commands=["profile"])
async def profile_handler(msg: types.Message):
    uid = str(msg.from_user.id)
    data = load_db()
    profile_text = format_profile(uid, data)
    await msg.answer(profile_text)


@dp.message_handler(commands=["refer"])
async def refer_handler(msg: types.Message):
    uid = str(msg.from_user.id)
    data = load_db()
    referrals = data["users"].get(uid, {}).get("referrals", 0)
    link = get_referral_link(uid)
    text = (
        f"📣 আপনার রেফার লিঙ্ক:\n{link}\n\n"
        f"✅ সফল রেফার: {referrals}"
    )
    await msg.answer(text)


user_withdraw_state = {}


@dp.message_handler(commands=["withdraw"])
async def withdraw_handler(msg: types.Message):
    uid = str(msg.from_user.id)
    data = load_db()
    user = data["users"].get(uid, {})
    if user.get("referrals", 0) < 20:
        await msg.answer("❗ উত্তোলনের জন্য অন্তত ২০টি রেফার লাগবে।")
        return

    await msg.answer("📥 দয়া করে আপনার বিকাশ/নগদ নম্বর পাঠান:")
    user_withdraw_state[uid] = True


@dp.message_handler()
async def handle_withdraw_number(msg: types.Message):
    uid = str(msg.from_user.id)
    if user_withdraw_state.get(uid):
        data = load_db()
        user = data["users"][uid]
        await bot.send_message(
            ADMIN_ID,
            f"📤 উত্তোলন রিকোয়েস্ট\nনাম: {msg.from_user.full_name}\nID: {uid}\nনম্বর: {msg.text}\nপরিমাণ: {user['balance']} টাকা"
        )
        user["balance"] = 0
        save_db(data)
        await msg.answer("✅ রিকোয়েস্ট গ্রহণ করা হয়েছে।")
        user_withdraw_state.pop(uid)


@dp.message_handler(commands=["free50"])
async def free50_handler(msg: types.Message):
    uid = str(msg.from_user.id)
    data = load_db()
    if uid in data.get("claimed_50", []):
        await msg.answer("❌ আপনি এই অফারটি ইতিমধ্যে গ্রহণ করেছেন।")
        return

    keyboard = InlineKeyboardMarkup(row_width=2).add(
        InlineKeyboardButton("🌐 Visit Website", url="http://invest-sure.netlify.app"),
        InlineKeyboardButton("✅ Submit", callback_data="submit_50")
    )
    await msg.answer("🎁 ওয়েবসাইটে গিয়ে রেজিস্ট্রেশন সম্পন্ন করে Submit দিন:", reply_markup=keyboard)


@dp.callback_query_handler(lambda c: c.data == "submit_50")
async def submit_50_handler(call: types.CallbackQuery):
    data = load_db()
    uid = str(call.from_user.id)
    if uid in data.get("claimed_50", []):
        await call.answer("❌ আপনি ইতিমধ্যে ক্লেইম করেছেন।", show_alert=True)
        return

    data.setdefault("claimed_50", []).append(uid)
    data["users"][uid]["balance"] += 50
    save_db(data)
    await call.message.edit_text("✅ ৫০ টাকা ব্যালেন্সে যোগ হয়েছে।")


@dp.message_handler(commands=["notice"])
async def notice_handler(msg: types.Message):
    await msg.answer("📌 নিয়মিতভাবে গ্রুপগুলোতে সক্রিয় থাকুন।")


@dp.message_handler(commands=["support"])
async def support_handler(msg: types.Message):
    await msg.answer("🆘 সাপোর্টের জন্য যোগাযোগ করুন: @CashShortcutAdmin")


if __name__ == "__main__":
    keep_alive()  # তোমার সার্ভার লাইভ রাখে

    print("🤖 Bot is running...")
    asyncio.run(dp.start_polling())
