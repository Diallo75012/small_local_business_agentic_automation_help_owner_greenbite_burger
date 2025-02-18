import os
from langchain_groq import ChatGroq
from dotenv import load_dotenv


# load env vars
load_dotenv(dotenv_path='.env', override=False)

# GROQ_TEMPERATURE_CREATIVE exist and is at 0.8

# LLMs
groq_llm_mixtral_7b = ChatGroq(
  temperature=float(os.getenv("GROQ_TEMPERATURE")),
  groq_api_key=os.getenv("GROQ_API_KEY"),
  model_name=os.getenv("MODEL_MIXTRAL_7B"),
  max_tokens=int(os.getenv("GROQ_MAX_TOKEN")),
)
groq_llm_mixtral_larger = ChatGroq(
  temperature=float(os.getenv("GROQ_TEMPERATURE")),
  groq_api_key=os.getenv("GROQ_API_KEY"),
  model_name=os.getenv("MODEL_MIXTRAL_LARGER"),
  max_tokens=int(os.getenv("GROQ_MAX_TOKEN")),
)
groq_llm_llama3_8b = ChatGroq(
  temperature=float(os.getenv("GROQ_TEMPERATURE")),
  groq_api_key=os.getenv("GROQ_API_KEY"),
  model_name=os.getenv("MODEL_LLAMA3_8B"),
  max_tokens=int(os.getenv("GROQ_MAX_TOKEN")),
)

groq_llm_llama3_70b = ChatGroq(
  temperature=float(os.getenv("GROQ_TEMPERATURE")),
  groq_api_key=os.getenv("GROQ_API_KEY"),
  model_name=os.getenv("MODEL_LLAMA3_70B"),
  max_tokens=int(os.getenv("GROQ_MAX_TOKEN")),
)
groq_llm_llama3_70b_versatile = ChatGroq(
  temperature=float(os.getenv("GROQ_TEMPERATURE")),
  groq_api_key=os.getenv("GROQ_API_KEY"),
  model_name=os.getenv("MODEL_LLAMA3_3_70B_VERSATILE"),
  max_tokens=int(os.getenv("GROQ_MAX_TOKEN")),
)
groq_llm_llama3_vision_large = ChatGroq(
  temperature=float(os.getenv("GROQ_TEMPERATURE")),
  groq_api_key=os.getenv("GROQ_API_KEY"),
  model_name=os.getenv("MODEL_LLAMA3_VISION_LARGE"),
  max_tokens=int(os.getenv("GROQ_MAX_TOKEN")),
)
groq_llm_gemma_7b = ChatGroq(
  temperature=float(os.getenv("GROQ_TEMPERATURE")),
  groq_api_key=os.getenv("GROQ_API_KEY"),
  model_name=os.getenv("MODEL_GEMMA_7B"),
  max_tokens=int(os.getenv("GROQ_MAX_TOKEN")),
)
