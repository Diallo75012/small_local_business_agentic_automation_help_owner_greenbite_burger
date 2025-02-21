import os
import torch
from typing import List
# Requires transformers>=4.48.0
from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim
from dotenv import load_dotenv, set_key


load_dotenv(".vars.env", override=True)

def similarity_check_on_the_fly(menu_item_names: List, message_order_item: str, similarity_threshold: float = float(os.getenv("SIMILARITY_THRESHOLD"))) -> str:
  '''
  evaluates the similarity score for item orders against menu item names

  params:
  menu_item_names List: a list of all the menu item names
  message_order_item str: a menu item taken coming from the order message
  similarity_threshold float: an float determining the percentage threshold in decimal number for the similarity to pass the test

  outputs:
  str: if any the highest similary scored item name
  '''

  # dimension of `Alibaba-NLP/gte-modernbert-base` embeddings is `768`
  model = SentenceTransformer("Alibaba-NLP/gte-modernbert-base")
  # put the order item that we need to check if similar of what we have at the end of the list of menu item names
  # then we will use index -1 check that against the full list
  menu_item_names.append(message_order_item)

  similarity_test_list = menu_item_names
  print(similarity_test_list)
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


input_texts = [
    "what is a manga kissa?",
    "Is Hachiko story real? did he have a piece of paper and a pen next to Shibuya JR station?",
    "I like Udon from Kyushu.",
    "where is the manga kissa?",
    "what is a manga kissa coffee?",
    "I love udon from Kyushu",
    "It is the story of someone waiting at JR station, next to Hachiko with a pen paper."
]
'''
# dimension of `Alibaba-NLP/gte-modernbert-base` embeddings is `768`
model = SentenceTransformer("Alibaba-NLP/gte-modernbert-base")
embeddings = model.encode(input_texts)
#print(embeddings.shape)


similarities = cos_sim(embeddings[1], embeddings[:1])
similarities2 = cos_sim(embeddings[1], embeddings[2:])
print(similarities[0][0].nonzero(as_tuple=True)[0].item(), input_texts[similarities[0][0].nonzero(as_tuple=True)[0].item()])
print(similarities2[0][4].item())
print(similarities2)
print(similarities2.max().item())
for idx in range(len(similarities2[0])):
  if similarities2[0][idx] == similarities2.max().item():
    print(f"{idx} - {similarities2[0][idx]} - {input_texts[idx]}")
'''

similarity_check_on_the_fly(input_texts, "what is a manga kissa coffee?")
