import time
from datetime import datetime
import sys
import os
from os.path import join
from dotenv import load_dotenv
from gql import get_events
import json

if os.path.exists("secrets.env"):
	load_dotenv("secrets.env")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TELEGRAM_API_KEY = os.getenv("TELEGRAM_API_TOKEN")

if OPENAI_API_KEY is None:
	print("Missing environment variable OPENAI_API_KEY")
	sys.exit(1)
if TELEGRAM_API_KEY is None:
	print("Missing environment variable TELEGRAM_API_TOKEN")
	sys.exit(1)

from openai import OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes

from constants import assistant_id, vector_store_id, dev_telegram_usernames

threads = dict()

import pytz

async def feedback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    username = update.effective_user.name
    message = update.message.text
    timestamp = datetime.now().isoformat()
    with open("feedback.txt", "a") as file:
        file.write(f"user: {username}\ndatetime: {timestamp}\nmessage: {message}\n\n")
    await update.message.reply_text("Thanks for your feedback! I've shared it with the developers.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
	user = update.effective_user
	if user.id in threads:
		del threads[user.id]
	START_MESSAGE = f"Hello there, {user.first_name}! I am the Edge City Lanna Bot. I can tell you all about this pop-up village happening in Chiang Mai from October 10th to November 10th. Ask me anything!\n\nIf you want to restart me, just say '/start'. And if you want to give me feedback, start your message with '/feedback'."
	await update.message.reply_text(START_MESSAGE)

async def get_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    username = update.effective_user.username
    print(f"got command `/getfeedback` from username {username}")
    if username not in dev_telegram_usernames:
        return
    with open("feedback.txt", "r") as file:
        all_feedback = file.read()
    await update.message.reply_text(all_feedback)

async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
	thread = None
	user = update.effective_user
	if update.effective_user.id in threads:
		thread = threads[update.effective_user.id]
	else:
		thread = client.beta.threads.create()
		threads[update.effective_user.id] = thread
	now = datetime.now().strftime("%A %Y-%m-%d %H:%M")
	message_content = f"{now} | {update.message.text}"
	message = client.beta.threads.messages.create(
		thread_id=thread.id,
		role="user",
		content=now + " | " + update.message.text
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

	if run.status == "requires_action":
		print("Message requires action")
		tool_outputs = []

		for tool in run.required_action.submit_tool_outputs.tool_calls:
			if tool.function.name == "get_events":
				args = json.loads(tool.function.arguments)
				result = get_events(args)
				tool_outputs.append({
					"tool_call_id": tool.id,
					"output": str(result)
				})

		if tool_outputs:
			try:
				run = client.beta.threads.runs.submit_tool_outputs_and_poll(
					thread_id=thread.id,
					run_id=run.id,
					tool_outputs=tool_outputs
				)
				print("Tool outputs submitted successfully.")
			except Exception as e:
				print("Failed to submit tool outputs:", e)
		else:
			print("No tool outputs to submit.")

		if run.status == 'completed':
			messages = client.beta.threads.messages.list(
				thread_id=thread.id
			)
			last_message = messages.data[0]
			response_text = last_message.content[0].text.value
		else:
			print(run.status)

	print(f"Responding to {user.first_name}: {response_text}")
	await update.message.reply_text(response_text)

app = ApplicationBuilder().token(os.getenv("TELEGRAM_API_TOKEN")).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("feedback", feedback))
app.add_handler(CommandHandler("getfeedback", get_feedback))
app.add_handler(MessageHandler(None, handler))

print("Running")

app.run_polling()
