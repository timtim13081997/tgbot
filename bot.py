from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import sqlite3


# Ваш Telegram ID для проверки прав администратора
ADMIN_ID = 425592487  

# Сообщение при старте
WELCOME_MESSAGE = """Приветствую, самый классный и активный ученик ГБОУ СОШ ж.-д. ст. Звезда! 
Хочешь узнать количество баллов или увидеть общий рейтинг?"""

# Инициализация базы данных
def init_db():
    conn = sqlite3.connect("students.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            user_id INTEGER PRIMARY KEY,
            name TEXT,
            points INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Узнать свои баллы", callback_data="my_score")],
        [InlineKeyboardButton("Общий рейтинг", callback_data="leaderboard")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(WELCOME_MESSAGE, reply_markup=reply_markup)

# Обработка кнопок
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "my_score":
        await my_score(query, context)
    elif query.data == "leaderboard":
        await leaderboard(query, context)

# Узнать свои баллы
async def my_score(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.from_user.id
    conn = sqlite3.connect("students.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name, points FROM students WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()

    if result:
        name, points = result
        await update.message.reply_text(f"{name}, у вас {points} баллов.")
    else:
        await update.message.reply_text("Вы не зарегистрированы в системе.")

# Общий рейтинг
async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect("students.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name, points FROM students ORDER BY points DESC")
    results = cursor.fetchall()
    conn.close()

    if results:
        leaderboard_text = "🏆 Общий рейтинг учеников:\n\n"
        for i, (name, points) in enumerate(results, start=1):
            leaderboard_text += f"{i}. {name} — {points} баллов\n"
        await update.message.reply_text(leaderboard_text)
    else:
        await update.message.reply_text("Рейтинг пуст.")

# Добавить ученика (только для администратора)
async def add_student(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        await update.message.reply_text("У вас нет прав для этой команды.")
        return

    try:
        name = " ".join(context.args[:-1])
        user_id = int(context.args[-1])
        conn = sqlite3.connect("students.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO students (user_id, name) VALUES (?, ?)", (user_id, name))
        conn.commit()
        conn.close()
        await update.message.reply_text(f"Ученик {name} добавлен с ID {user_id}.")
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}")

# Добавить баллы (только для администратора)
async def add_points(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        await update.message.reply_text("У вас нет прав для этой команды.")
        return

    try:
        user_id = int(context.args[0])
        points = int(context.args[1])
        conn = sqlite3.connect("students.db")
        cursor = conn.cursor()
        cursor.execute("UPDATE students SET points = points + ? WHERE user_id = ?", (points, user_id))
        conn.commit()
        conn.close()
        await update.message.reply_text(f"Ученику с ID {user_id} добавлено {points} баллов.")
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}")

# Основная функция
def main():
    init_db()

    application = Application.builder().token("7907519749:AAGU9zE-mEvkKB4fpEpl331cNRrvx9WQJa8").build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("add_student", add_student))
    application.add_handler(CommandHandler("add_points", add_points))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, leaderboard))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, my_score))
    application.add_handler(CallbackQueryHandler(button_handler))

    application.run_polling()

if __name__ == "__main__":
    main()
