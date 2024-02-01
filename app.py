from flask import Flask, render_template, request, jsonify, session
import logging
import openai
import os
import time
import markdown
import bleach
from utils.token_counter import count_thread_tokens

app = Flask(__name__)

client = openai

# Configure logging
logging.basicConfig(level=logging.INFO)
app.logger.setLevel(logging.INFO)

# Set the OpenAI API key
client.api_key = os.environ.get('OPENAI_API_KEY')

# Set the app secret key for thread management
app.secret_key = os.environ.get('SECRET_KEY')

def create_thread(ass_id, prompt):
 
    # Check if a thread already exists, create one if not
    if 'thread_id' not in session:
        thread = client.beta.threads.create()
        session['thread_id'] = thread.id

    my_thread_id = session['thread_id']

    # Create a message
    message = client.beta.threads.messages.create(
        thread_id=my_thread_id,
        role="user",
        content=prompt  
    )

    # Run
    run = client.beta.threads.runs.create(
        thread_id=my_thread_id,
        assistant_id=ass_id,
    ) 

    return run.id, my_thread_id

#check run status
def check_status(run_id, thread_id):
    run = client.beta.threads.runs.retrieve(
        thread_id=thread_id,
        run_id=run_id,
    )
    return run.status

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json['message']

    # Define the maximum allowed characters
    MAX_CHARS = 300  # Set your desired limit

    if len(user_input) > MAX_CHARS:
        return jsonify({'error': 'Input exceeds the maximum allowed character limit.'}), 400


    allowed_tags = ['b', 'i', 'hr', 'p', 'br '] #Tags allowed by bleach. everything else is sanitised
    sanitised_input = bleach.clean(user_input, tags = allowed_tags) #Sanitize user input to prevent malicious html insert

    app.logger.info(f"Received request: {sanitised_input}")  # Log the received message
    print("Received request:", request.json) # Prints the received message in dev mode only.

    try:
        assistant_id = "asst_JZnFQkifZLY3r1C5uaL1cgpg"  # Replace with environment variable
        my_run_id, my_thread_id = create_thread(assistant_id, sanitised_input)

        status = check_status(my_run_id, my_thread_id)

        while status in ['queued', 'in_progress']:
            status = check_status(my_run_id, my_thread_id)
            time.sleep(1)

        response = client.beta.threads.messages.list(
            thread_id=my_thread_id
        
        )
        
        if response.data:
            chat_response = response.data[0].content[0].text.value
            chat_response_html = markdown.markdown(chat_response, extensions=['nl2br']) #Convert markdown to HTML with nl2br extension to handle conversion of single new lines (\n) into breaks and double new lines (\n\n) into paragraph breaks.
            #chat_response_html = bleach.clean(chat_response_markdown, tags=allowed_tags)#Sanitize user input to prevent malicious html insert

            #count total tokens in a thread
            encoding_name = 'cl100k_base'
            total_tokens = count_thread_tokens(my_thread_id, client, encoding_name)
            app.logger.info(f"Total tokens in the thread: {total_tokens}")

            app.logger.info(f"Sending response: {chat_response_html}")  #Log the response being sent back
            print("Sending response:", response)  # Prints the response being sent back in dev mode only
            return jsonify({'response': chat_response_html, 'thread_id': my_thread_id})

    except Exception as e:
        app.logger.error(f"Error in chat endpoint: {e}")  # Log the error if occurred
        print("Error:", str(e))  # Prints the error if occurred in dev mode only
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=False)
