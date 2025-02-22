import os
import torch
from typing import List
# Requires transformers>=4.48.0
from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim
from dotenv import load_dotenv, set_key

load_dotenv(".vars.env", override=True)
# this one only use when testing code standalone
# load_dotenv("../.vars.env", override=True)


def similarity_check_on_the_fly(menu_item_names: List, message_order_item: str, similarity_threshold: float = float(os.getenv("SIMILARITY_THRESHOLD"))) -> dict:
  '''
  evaluates the similarity score for item orders against menu item names

  params:
  menu_item_names List: a list of all the menu item names
  message_order_item str: a menu item taken coming from the order message
  similarity_threshold float: an float determining the percentage threshold in decimal number for the similarity to pass the test

  outputs:
  dict: index of item, item name, similary score when one has passed test, otherwise failed message and similarity score
  '''

  # dimension of `Alibaba-NLP/gte-modernbert-base` embeddings is `768`
  model = SentenceTransformer("Alibaba-NLP/gte-modernbert-base")
  # put the order item that we need to check if similar of what we have at the end of the list of menu item names
  # then we will use index -1 check that against the full list
  menu_item_names.append(message_order_item)

  similarity_test_list = menu_item_names
  print(similarity_test_list)

  try:
    embeddings_menu_item_names_with_order_item_to_test = model.encode(similarity_test_list)

    # now compute the similarity score
    similarities = cos_sim(embeddings_menu_item_names_with_order_item_to_test[-1], embeddings_menu_item_names_with_order_item_to_test[:-1])
    max_similar = similarities.max().item()
    print("max_similar: ", max_similar)
    # we check if the score is pass the threshold test
    if max_similar:
      if max_similar >= similarity_threshold:
        # if it is passing the threshold test we get the index corredponding to the `key` text we want to pass to next agent
        for idx in range(len(similarities[0])):
          if similarities[0][idx] == max_similar:
            print(f"{idx} - {similarities[0][idx]} - {menu_item_names[idx]}")
            return {
              "idx": idx,
              "menu_item_name": menu_item_names[idx],
              "score": max_similar,
            }
    return {
      "failed": "failed to pass similarity test.",
      "score": max_similar,
    }

  except Exception as e:
    return {"error": f"An error occured while trying to pass similarity score test: {e}"}

'''
if __name__ == "__main__":
  input_texts = [
    "what is a manga kissa?",
    "Is Hachiko story real? did he have a piece of paper and a pen next to Shibuya JR station?",
    "I like Udon from Kyushu.",
    "where is the manga kissa?",
    "what is a manga kissa coffee?",
    "I love udon from Kyushu",
    "It is the story of someone waiting at JR station, next to Hachiko with a pen paper."
  ]
  print(similarity_check_on_the_fly(input_texts, "nihongo ha totemo muwukashii desune , kanji ga oboenai deshoyu neeee"))
'''
