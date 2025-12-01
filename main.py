
import logging
import json
import os
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup
from database import Database
from analyzer import analyze_test_result, build_global_profile
from report import generate_pdf_report

API_TOKEN = os.getenv("BOT_TOKEN", "YOUR_TOKEN")

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
db = Database()

TESTS = {}
TEST_TITLES = {}

def load_tests():
    global TESTS, TEST_TITLES
    tests_dir = "tests"
    for fname in os.listdir(tests_dir):
        if not fname.endswith(".json"):
            continue
        path = os.path.join(tests_dir, fname)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        key = fname.replace(".json", "")
        TESTS[key] = data
        TEST_TITLES[key] = data.get("title", data.get("name", key))

load_tests()

user_sessions = {}

def main_menu() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🧠 Тести", "📘 Мій профіль")
    kb.add("📄 PDF-паспорт")
    return kb

def tests_menu_kb() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    if "mbti_90" in TESTS:
        kb.add("MBTI 90")
    if "bigfive_120" in TESTS:
        kb.add("Big Five 120")
    if "temperament" in TESTS:
        kb.add("Темперамент")
    if "eysenck_epq" in TESTS:
        kb.add("Eysenck EPQ")
    if "leonhard_88" in TESTS:
        kb.add("Леонгард 88")
    if "ecr_r_36" in TESTS:
        kb.add("ECR-R (Прив’язаність)")
    kb.add("⬅️ Назад")
    return kb

@dp.message_handler(commands=["start"])
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 Вітаю в <b>PsycheVision</b> — AI-психологічні тести та HR-профілювання.\n"
        "Оберіть дію в меню нижче.",
        parse_mode="HTML",
        reply_markup=main_menu()
    )

@dp.message_handler(lambda m: m.text == "🧠 Тести")
async def tests_menu(message: types.Message):
    await message.answer("Оберіть тест:", reply_markup=tests_menu_kb())

@dp.message_handler(lambda m: m.text in [
    "MBTI 90", "Big Five 120", "Темперамент", "Eysenck EPQ", "Леонгард 88", "ECR-R (Прив’язаність)"
])
async def start_test(message: types.Message):
    text_to_key = {
        "MBTI 90": "mbti_90",
        "Big Five 120": "bigfive_120",
        "Темперамент": "temperament",
        "Eysenck EPQ": "eysenck_epq",
        "Леонгард 88": "leonhard_88",
        "ECR-R (Прив’язаність)": "ecr_r_36",
    }
    test_key = text_to_key[message.text]
    test = TESTS.get(test_key)
    if not test:
        await message.answer("Цей тест ще не налаштований.")
        return

    user_sessions[message.from_user.id] = {
        "test_key": test_key,
        "index": 0,
        "answers_idx": []
    }
    await send_question(message.chat.id, message.from_user.id)

async def send_question(chat_id: int, user_id: int):
    state = user_sessions.get(user_id)
    if not state:
        return
    test = TESTS.get(state["test_key"])
    items = test.get("items", [])
    idx = state["index"]
    if idx >= len(items):
        await finish_test(chat_id, user_id)
        return

    q = items[idx]
    text = f"Питання {idx+1} з {len(items)}:\n{q['q']}"
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    for opt in q["a"]:
        kb.add(opt)
    await bot.send_message(chat_id, text, reply_markup=kb)

async def finish_test(chat_id: int, user_id: int):
    state = user_sessions.get(user_id)
    if not state:
        return
    test_key = state["test_key"]
    test = TESTS.get(test_key)
    answers_idx = state["answers_idx"]

    result = analyze_test_result(test_key, answers_idx)
    score = result["score"]
    level = result["level"]
    summary = result["summary"]
    title = TEST_TITLES.get(test_key, test_key)

    db.save_result(
        user_id=user_id,
        username=None,
        test_id=test_key,
        test_title=title,
        raw_score=score,
        level=level,
        summary=summary,
        meta_json=json.dumps(result, ensure_ascii=False)
    )

    del user_sessions[user_id]

    await bot.send_message(
        chat_id,
        f"✅ Тест <b>{title}</b> завершено.\n"
        f"Ваш умовний бал: <b>{score:.1f}</b> (рівень: <b>{level}</b>)\n\n"
        f"{summary}",
        parse_mode="HTML",
        reply_markup=main_menu()
    )

@dp.message_handler(lambda m: m.text == "📘 Мій профіль")
async def my_profile(message: types.Message):
    results = db.get_user_results(message.from_user.id)
    profile_text = build_global_profile(results)
    await message.answer(profile_text, parse_mode="HTML")

@dp.message_handler(lambda m: m.text == "📄 PDF-паспорт")
async def pdf_passport(message: types.Message):
    results = db.get_user_results(message.from_user.id)
    profile_text = build_global_profile(results)
    pdf_path = generate_pdf_report(message.from_user.id, profile_text)
    await message.answer_document(open(pdf_path, "rb"))

@dp.message_handler()
async def generic_answer(message: types.Message):
    uid = message.from_user.id
    if uid not in user_sessions:
        if message.text == "⬅️ Назад":
            await message.answer("Повернення в головне меню.", reply_markup=main_menu())
        elif message.text in ["🧠 Тести", "📘 Мій профіль", "📄 PDF-паспорт"]:
            # їх перехоплять відповідні хендлери
            return
        else:
            await message.answer("Скористайтесь меню нижче.", reply_markup=main_menu())
        return

    state = user_sessions[uid]
    test = TESTS.get(state["test_key"])
    items = test.get("items", [])
    idx = state["index"]

    if idx >= len(items):
        await finish_test(message.chat.id, uid)
        return

    q = items[idx]
    options = q["a"]
    if message.text not in options:
        await message.answer("Оберіть один із варіантів відповідей з клавіатури.")
        return

    answer_index = options.index(message.text)
    state["answers_idx"].append(answer_index)
    state["index"] += 1

    await send_question(message.chat.id, uid)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("PsycheVision v7 bot starting...")
    executor.start_polling(dp, skip_updates=True)
