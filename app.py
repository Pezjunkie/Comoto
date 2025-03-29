import os
from slack_bolt import App

# Initialize the Slack app with your bot token and signing secret
app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
)

from datetime import datetime, timedelta
import google.generativeai as genai

# Configure Gemini API (replace with actual configuration)
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")  # Assuming API key is in environment variable
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY environment variable not set.")
genai.configure(api_key=GOOGLE_API_KEY)

# Process messages and send to Gemini
def process_message(message_text, channel_id, ts):
    time_period = "message"  # Default to current message
    if message_text.lower().startswith("day:"):
        time_period = "day"
        message_text = message_text[4:].strip()
    elif message_text.lower().startswith("week:"):
        time_period = "week"
        message_text = message_text[5:].strip()
    elif message_text.lower().startswith("month:"):
        time_period = "month"
        message_text = message_text[6:].strip()

    analysis_prompt = f"Analyze the following Slack message: '{message_text}'"

    if time_period != "message":
        # Placeholder for retrieving messages for the specified time period
        # In a real app, this would involve querying a database or Slack API
        if time_period == "day":
            start_date = datetime.now() - timedelta(days=1)
        elif time_period == "week":
            start_date = datetime.now() - timedelta(weeks=1)
        elif time_period == "month":
            start_date = datetime.now() - timedelta(days=30)  # Approximate

        # Format start_date for display
        start_date_str = start_date.strftime("%Y-%m-%d")

        # Placeholder for retrieving messages - replace with actual logic
        analysis_prompt = f"Analyze Slack messages from channel {channel_id} since {start_date_str}. The current message is: '{message_text}'"

    try:
        model = genai.GenerativeModel('gemini-pro')  # Use appropriate model
        response = model.generate_content(analysis_prompt)
        analysis_result = response.text
    except Exception as e:
        analysis_result = f"Error during Gemini analysis: {e}"

    if time_period != "message":
        analysis_result = f"Analysis for the past {time_period} (including your message):\n{analysis_result}"

    return analysis_result

# Listen for messages in private channels (im or mpim)
@app.event("app_mention")  # Use app_mention for private channels and direct messages
def handle_app_mention_events(body, say, logger):
    logger.info(body)
    event = body.get("event", {})
    message_text = event.get("text")
    channel_id = event.get("channel")
    ts = event.get("ts")
    if message_text:
        # Remove the app mention prefix if present
        app_id = body["authorizations"][0]["user_id"]
        message_text = message_text.replace(f"<@{app_id}>", "").strip()
        analysis_result = process_message(message_text, channel_id, ts)
        say(f"{analysis_result}")
    else:
        say("Received an empty message (via app mention).")

# Listen for messages in public channels
@app.event("message")
def handle_message_events(body, say, logger):
    logger.info(body)
    event = body.get("event", {})
    subtype = event.get("subtype")
    if subtype != "bot_message":  # Ignore bot messages to prevent loops
        message_text = event.get("text")
        channel_id = event.get("channel")
        ts = event.get("ts")
        if message_text:
            # Remove the app mention prefix if present
            app_id = body["authorizations"][0]["user_id"]
            message_text = message_text.replace(f"<@{app_id}>", "").strip()
            analysis_result = process_message(message_text, channel_id, ts)
            say(f"{analysis_result}")
        else:
            say("Received an empty message.")
    else:
        logger.info("Ignoring bot message")

# Start the app
if __name__ == "__main__":
    app.start(port=int(os.environ.get("PORT", 3000)))
