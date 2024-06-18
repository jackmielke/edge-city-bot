import os
from os.path import join
from dotenv import dotenv_values

config = dotenv_values("secrets.env")

from openai import OpenAI
client = OpenAI(api_key=config["OPENAI_API_KEY"])

from constants import vector_store_id

blog_folder_path = "blog"
file_streams = []

for root, dirs, files in os.walk(blog_folder_path):
    for file in files:
        file_path = join(root, file)
        file_streams.append(open(file_path, "rb"))

file_batch = client.beta.vector_stores.file_batches.upload_and_poll(
  vector_store_id=vector_store_id, files=file_streams
)

# You can print the status and the file counts of the batch to see the result of this operation.
print(file_batch.id)
print(file_batch.status)
print(file_batch.file_counts)

# Close all file streams
for file_stream in file_streams:
    file_stream.close()
