import sqlite3 
import json
import requests
import time

file = "./words_dictionary.json"

json_data = None

with open(file, "r") as f:
	json_data = json.load(f)

print(f"Words : {len(json_data.keys())}")

connection = sqlite3.connect("./word_list.db")
cursor = connection.cursor()

index = 0
for word in json_data.keys():
	cursor.execute("INSERT OR IGNORE INTO words (word) VALUES (?)", (word,))
	index += 1
	if (index % 10000 == 0):
		print(f"Index now at: {index} with word {word}")
		connection.commit()

connection.commit()
connection.close()
