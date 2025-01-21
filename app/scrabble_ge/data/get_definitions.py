import sqlite3 
import json
import requests
import time
import random



def get_endpoint(word):
	return f"https://api.dictionaryapi.dev/api/v2/entries/en/{word.lower().strip()}"

def get_definitions(response_data):
	meanings = []
	try:
		data = response_data.json()
		for meaning in data[0]["meanings"]:
			if len(meaning["definitions"]) > 3:
				meaning["definitions"] = meaning["definitions"][0:3]
			for definition in meaning["definitions"]:
				meanings.append(definition["definition"])
	except Exception as e:
		print(f"error {e}")
		return None
	return "\n".join(meanings)

def get_words_without_definitions(cursor, initial_offset, page_size, page_number):
    # Calculate offset
    offset = initial_offset + ((page_number - 1) * page_size)
    # Execute the query
    query = """
        SELECT id, word, definition
        FROM words
        WHERE definition IS NULL
        LIMIT ? OFFSET ?;
    """
    cursor.execute(query, (page_size, offset))
    results = cursor.fetchall()
    return results

# req = requests.get(get_endpoint("isfjadksgjfs"))
# print(req)
# if req.status_code == 200:
# 	print(get_definitions(req))
# else:
# 	print("Word not found, removing!")

def next_words(curs, initial_offset, page_size):
	current_page = 0
	words = get_words_without_definitions(curs, initial_offset, page_size, current_page)
	while len(words) > 0:
		yield words
		words = get_words_without_definitions(curs, initial_offset, page_size, current_page)
		current_page += 1
	
def check_delete_word(cursor, reason, word_data=(None,None,None)):
	delete_query = """
	DELETE FROM words WHERE id = ? AND word = ?;
	"""
	id, word, definition = word_data
	print(f"{word} + {id} | error: {reason}")
	return 
	x = input("delete? (y/n)")
	if x.lower()[0] == "y":
		print(f"deleting {word}\n")
		cursor.execute(delete_query, (id, word))

def add_definition(cursor, word_id, word, defintion):
	add_query = """
	UPDATE words
	SET definition = ?
	WHERE id = ? AND word = ?
	"""
	cursor.execute(add_query, (defintion, word_id, word))

def main ():
	connection = sqlite3.connect("./word_list.db")
	cursor = connection.cursor()
	page_size = 10;
	gen = next_words(cursor, 21000, page_size)
	try:
		words = next(gen)
		while len(words) > 0:
			for id, word, _ in words:
				request = requests.get(get_endpoint(word))
				while (request.status_code == 429):
					time.sleep(10)
					request = requests.get(get_endpoint(word))
				if request.status_code == 200:
					defintion = get_definitions(request)
					if defintion == None:
						check_delete_word(cursor, "Dictionary API reponse was not parsable.")
					else:
						add_definition(cursor, id, word, defintion)
				else:
					print(request.status_code)
					check_delete_word(cursor, "Dictionary API doesn't have this word.", (id, word, None))
				time.sleep(0.1)
			words = next(gen)
			connection.commit()
			time.sleep(20)
	finally:
		connection.commit()
		connection.close()


if __name__ == "__main__":
	main()