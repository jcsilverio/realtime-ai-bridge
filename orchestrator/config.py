"""Model settings for the selection agent."""

MODEL_NAME = "gpt-5.4-mini"
# GPT-5 models reject a custom temperature, so tune reasoning effort instead.
REASONING_EFFORT = "low"
MAX_RETRIES = 1
