import time
from datetime import datetime
import os
from os.path import join
from dotenv import load_dotenv

if os.path.exists("secrets.env"):
	load_dotenv("secrets.env")

from openai import OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes

from constants import assistant_id, vector_store_id

threads = dict()

async def feedback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    username = update.effective_user.name
    message = update.message.text
    timestamp = datetime.now().isoformat()
    with open("./logs/feedback.txt", "a") as file:
        file.write(f"user: {username}\ndatetime: {timestamp}\nmessage: {message}\n\n")
    await update.message.reply_text("Thanks for your feedback! I've shared it with the developers.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
	user = update.effective_user
	if user.id in threads:
		del threads[user.id]
	START_MESSAGE = f"Hello there, {user.first_name}! I am the Edge Esmeralda Bot. I can tell you all about Edge Esmeralda, a pop-up village happening June 2024. Ask me anything!\n\nIf you want to restart me, just say '/start'. And if you want to give me feedback, start your message with '/feedback'."
	await update.message.reply_text(START_MESSAGE)

async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
	thread = None
	user = update.effective_user
	if update.effective_user.id in threads:
		thread = threads[update.effective_user.id]
	else:
		thread = client.beta.threads.create()
		threads[update.effective_user.id] = thread
	message = client.beta.threads.messages.create(
		thread_id=thread.id,
		role="user",
		content=update.message.text
	)
	print(f"New message from {user.first_name}: {update.message.text}")
	run = client.beta.threads.runs.create_and_poll(
		thread_id=thread.id,
		assistant_id=assistant_id,
	)
	response_text = "[response goes here]"
	if run.status == 'completed':
		messages = client.beta.threads.messages.list(
			thread_id=thread.id
		)
		last_message = messages.data[0]
		response_text = last_message.content[0].text.value
	else:
		print("run not completed:", run.status)
	print(f"Responding to {user.first_name}: {response_text}")
	await update.message.reply_text(response_text)

app = ApplicationBuilder().token(os.getenv("TELEGRAM_API_TOKEN")).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("feedback", feedback))
# app.add_handler(CommandHandler("get_feedback"))
app.add_handler(MessageHandler(None, handler))


print("Waiting 10 seconds")
time.sleep(10)
print("Running")

app.run_polling()
