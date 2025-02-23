import sys
import json


def safe_json_dumps(obj):
  """
  Safely dumps an object to JSON. Converts non-serializable objects to strings.
  """
  try:
    return json.dumps(obj, indent=4)
  except TypeError as e:
    # Log the serialization error
    print(f"Serialization error: {e}", file=sys.stderr)
    # Fallback to a string representation for non-serializable objects
    return str(obj)
