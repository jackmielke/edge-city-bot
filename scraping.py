import os
import sys
from os.path import join
import requests

url = sys.argv[1]
slug = os.path.basename(url)

from newspaper import Article

article = Article(url)
article.download()
article.parse()

content = article.text

with open(join("blog", slug + ".txt"), "w") as file:
    file.write(content)
