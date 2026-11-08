import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from yandex_cloud_ml_sdk import YCloudML
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker

# Загрузка .env
load_dotenv()
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# --- НАСТРОЙКА БАЗЫ ДАННЫХ ---
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, index=True)
    username = Column(String, nullable=True)

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    role = Column(String) # 'user' или 'assistant'
    text = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

# --- НАСТРОЙКА YANDEX CLOUD ---
TG_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
FOLDER_ID = os.getenv("YA_FOLDER_ID")
API_KEY = os.getenv("YA_API_KEY")
ASSISTANT_ID = os.getenv("YA_ASSISTANT_ID")

sdk = YCloudML(folder_id=FOLDER_ID, auth=API_KEY)

# --- ЛОГИКА БОТА ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = SessionLocal()
    tg_id = update.effective_user.id
    user = db.query(User).filter(User.telegram_id == tg_id).first()
    if not user:
        db.add(User(telegram_id=tg_id, username=update.effective_user.username))
        db.commit()
    db.close()
    await update.message.reply_text("Привет! Я эксперт по API Bitrix24. Задайте мне вопрос.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    tg_id = update.effective_user.id
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    db = SessionLocal()
    user = db.query(User).filter(User.telegram_id == tg_id).first()

    if user:
        db.add(Message(user_id=user.id, role="user", text=user_text))
        db.commit()

    try:
        # Обращение к Yandex Assistant
        assistant = sdk.assistants.get(ASSISTANT_ID)
        thread = sdk.threads.create(ttl_days=1)
        thread.write(user_text)
        
        run = assistant.run(thread)
        result = run.wait()
        answer = result.text

        if user:
            db.add(Message(user_id=user.id, role="assistant", text=answer))
            db.commit()

        # Отправка ответа в Telegram (разбивка, если текст длинный)
        if len(answer) > 4000:
            for i in range(0, len(answer), 4000):
                await update.message.reply_text(answer[i:i+4000])
        else:
            await update.message.reply_text(answer)

    except Exception as e:
        logger.error(f"Ошибка Yandex Cloud: {e}")
        await update.message.reply_text("Произошла ошибка при обращении к Yandex Assistant.")
    finally:
        db.close()

def main():
    if not ASSISTANT_ID:
        print("ОШИБКА: Не указан YA_ASSISTANT_ID в файле .env")
        return

    application = ApplicationBuilder().token(TG_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Бот запущен...")
    application.run_polling()

if __name__ == '__main__':
    main()