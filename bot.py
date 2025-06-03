import json
import asyncio
import os
from datetime import datetime

from aiogram import Bot, Dispatcher, types
from keep_alive import keep_alive  # যদি তোমার প্রজেক্টে থাকে

# ==== Bot Configuration ====
TOKEN = "8068195499:AAGDIel94FTmiXRLe-TGwVJI63GW1y03qxo"  # তোমার বট টোকেন
ADMIN_ID = 7647930808  # তোমার টেলিগ্রাম আইডি

GROUP_IDS = [
    "-1002676258756",
    "-1002657235869",
    "-1002414769217"
]

GROUP_MAP = {
    "-1002676258756": "CashShortcutBD",
    "-1002657235869": "EarningZone0BD",
    "-1002414769217": "EarnopediaBD"
}

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)
DB_FILE = "database.json"


# ==== Database Operations ====
def load_db():
    if not os.path.exists(DB_FILE):
        return {"users": {}, "claimed_50": [], "joined_users": []}
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
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
        f"📅 জয়েন তারিখ: {joined}\n"
        f"✅ সফল রেফার: {referrals}"
    )
    return text


def get_referral_link(user_id):
    return f"https://t.me/Student_Refer_bot?start={user_id}"


# ==== Handlers ====

@dp.message_handler(commands=["start"])
async def start_handler(msg: types.Message):
    uid = str(msg.from_user.id)
    name = msg.from_user.full_name
    data = load_db()

    # ইউজার ডাটাবেজে না থাকলে যোগ করো
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

    # যদি ইউজার আগেই গ্রুপ জয়েন করে থাকে, আর join check হয়ে থাকে, তাহলে মেনু দেখাও
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

    # গ্রুপ জয়েন চেক করো
    not_joined = []
    for gid in GROUP_IDS:
        try:
            member = await bot.get_chat_member(gid, msg.from_user.id)
            if member.status not in ["member", "administrator", "creator"]:
                not_joined.append(GROUP_MAP.get(gid, "অজানা গ্রুপ"))
        except Exception:
            not_joined.append(GROUP_MAP.get(gid, "অজানা গ্রুপ"))

    if not_joined:
        await msg.answer(
            f"প্রিয় {name}, আপনি নিচের গ্রুপগুলোতে জয়েন করুন:\n" +
            "\n".join(f"• {g}" for g in not_joined) +
            "\n\nজয়েন করার পর আবার /start দিন।"
        )
        return

    # জয়েন চেক সফল হলে ডাটাবেজে যোগ করো
    if uid not in data.get("joined_users", []):
        data.setdefault("joined_users", []).append(uid)
        save_db(data)

    profile_text = format_profile(uid, data)
    menu_text = (
        f"ধন্যবাদ {name}, আপনি সফলভাবে সব গ্রুপে জয়েন করেছেন!\n\n"
        f"{profile_text}\n\n"
        "📄 প্রোফাইল দেখতে /profile\n"
        "📣 রেফার করতে /refer\n"
        "💳 উত্তোলন করতে /withdraw\n"
        "🎁 ফ্রি ৫০ টাকা পেতে /free50\n"
        "📢 নোটিশ পেতে /notice\n"
        "🆘 সাপোর্ট পেতে /support"
    )
    await msg.answer(menu_text)


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
    await msg.answer(
        f"📣 প্রিয় {msg.from_user.full_name},\n"
        f"তোমার রেফারেল লিঙ্ক: {link}\n"
        f"✅ সফল রেফার: {referrals} জন"
    )


user_withdraw_state = set()


@dp.message_handler(commands=["withdraw"])
async def withdraw_handler(msg: types.Message):
    uid = str(msg.from_user.id)
    data = load_db()
    user = data["users"].get(uid, {})
    if user.get("referrals", 0) < 20:
        await msg.answer(
            f"❗ প্রিয় {msg.from_user.full_name}, উত্তোলনের জন্য অন্তত ২০ জন রেফার লাগবে। "
            f"আপনার সফল রেফার সংখ্যা: {user.get('referrals', 0)}"
        )
    elif user.get("balance", 0) <= 0:
        await msg.answer(f"❗ প্রিয় {msg.from_user.full_name}, আপনার ব্যালেন্স শূন্য।")
    else:
        await msg.answer("📥 বিকাশ/নগদ নম্বর পাঠান:")
        user_withdraw_state.add(uid)


@dp.message_handler()
async def process_withdraw_number(msg: types.Message):
    uid = str(msg.from_user.id)
    if uid in user_withdraw_state:
        data = load_db()
        user = data["users"].get(uid, {})
        amount = user.get("balance", 0)

        if amount <= 0:
            await msg.answer("❗ আপনার ব্যালেন্স শূন্য বা অবৈধ।")
            user_withdraw_state.discard(uid)
            return

        text = (
            f"📤 নতুন উত্তোলন রিকোয়েস্ট:\n"
            f"নাম: {msg.from_user.full_name}\n"
            f"ID: {uid}\n"
            f"বিকাশ/নগদ নম্বর: {msg.text}\n"
            f"পরিমাণ: {amount} টাকা"
        )
        await bot.send_message(ADMIN_ID, text)
        user["balance"] = 0
        save_db(data)
        await msg.answer("✅ রিকোয়েস্ট গ্রহণ করা হয়েছে। ধন্যবাদ!")
        user_withdraw_state.discard(uid)


@dp.message_handler(commands=["free50"])
async def free50_handler(msg: types.Message):
    uid = str(msg.from_user.id)
    data = load_db()

    if uid in data.get("claimed_50", []):
        await msg.answer("❌ আপনি ইতিমধ্যে ফ্রি ৫০ টাকা ক্লেইম করেছেন।")
        return

    # এখানে ওয়েবসাইট লিংক দেখাও এবং ক্লেইম করার নির্দেশ দাও
    text = (
        f"🎁 প্রিয় {msg.from_user.full_name}, ফ্রি ৫০ টাকা পেতে নিচের ওয়েবসাইটে গিয়ে "
        "রেজিস্ট্রেশন সম্পন্ন করুন।\n\n"
        "ওয়েবসাইট: http://invest-sure.netlify.app\n\n"
        "রেজিস্ট্রেশন শেষ হলে নিচের কমান্ড দিয়ে ক্লেইম করুন:\n"
        "/claim50"
    )
    await msg.answer(text)


@dp.message_handler(commands=["claim50"])
async def claim50_handler(msg: types.Message):
    uid = str(msg.from_user.id)
    data = load_db()

    if uid in data.get("claimed_50", []):
        await msg.answer("❌ আপনি ইতিমধ্যে ফ্রি ৫০ টাকা ক্লেইম করেছেন।")
        return

    data.setdefault("claimed_50", []).append(uid)
    if uid in data["users"]:
        data["users"][uid]["balance"] = data["users"][uid].get("balance", 0) + 50
    else:
        data["users"][uid] = {
            "name": msg.from_user.full_name,
            "balance": 50,
            "joined": datetime.now().strftime("%Y-%m-%d"),
            "referrals": 0
        }
    save_db(data)

    await msg.answer(
        f"✅ প্রিয় {msg.from_user.full_name}, আপনার ব্যালেন্সে ৫০ টাকা যোগ হয়েছে!"
    )


@dp.message_handler(commands=["notice"])
async def notice_handler(msg: types.Message):
    await msg.answer(
        "📢 নিয়মিতভাবে গ্রুপগুলোতে সক্রিয় থাকুন এবং নতুন আপডেট পেতে আমাদের সঙ্গে থাকুন।"
    )


@dp.message_handler(commands=["support"])
async def support_handler(msg: types.Message):
    await msg.answer(
        "🆘 সাপোর্টের জন্য যোগাযোগ করুন: @CashShortcutAdmin"
    )


# ==== Start Bot ====
if __name__ == "__main__":
    keep_alive()  # যদি দরকার না হয়, তাহলে মুছে ফেলো

    loop = asyncio.get_event_loop()

    async def main():
        print("🤖 Bot is running...")
        await dp.start_polling()

    loop.create_task(main())
    loop.run_forever()
