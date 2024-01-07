from flask import Flask, render_template, request, jsonify, session
import logging
import openai
import os
import time
import markdown

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
app.logger.setLevel(logging.INFO)

# Set the OpenAI API key
openai.api_key = os.environ.get('OPENAI_API_KEY')

# Set the app secret key for thread management
app.secret_key = os.environ.get('SECRET_KEY')

def create_thread(ass_id, prompt):
 
    # Check if a thread already exists, create one if not
    if 'thread_id' not in session:
        thread = openai.beta.threads.create()
        session['thread_id'] = thread.id

    my_thread_id = session['thread_id']

    # Create a message
    message = openai.beta.threads.messages.create(
        thread_id=my_thread_id,
        role="user",
        content=prompt  
    )

    # Run
    run = openai.beta.threads.runs.create(
        thread_id=my_thread_id,
        assistant_id=ass_id,
    ) 

    return run.id, my_thread_id

#check run status
def check_status(run_id, thread_id):
    run = openai.beta.threads.runs.retrieve(
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
    app.logger.info(f"Received request: {user_input}")  # Log the received message
    print("Received request:", request.json) # Prints the received message in dev mode only.

    try:
        assistant_id = "asst_JZnFQkifZLY3r1C5uaL1cgpg"  # Replace with environment variable
        my_run_id, my_thread_id = create_thread(assistant_id, user_input)

        status = check_status(my_run_id, my_thread_id)

        while status in ['queued', 'in_progress']:
            status = check_status(my_run_id, my_thread_id)
            time.sleep(1)

        response = openai.beta.threads.messages.list(
            thread_id=my_thread_id
        )

        if response.data:
            chat_response = response.data[0].content[0].text.value
            chat_response_html = markdown.markdown(chat_response) #Convert markdown to HTML
            app.logger.info(f"Sending response: {chat_response_html}")  # Log the response being sent back
            print("Sending response:", response)  # Prints the response being sent back in dev mode only
            return jsonify({'response': chat_response_html, 'thread_id': my_thread_id})

    except Exception as e:
        app.logger.error(f"Error in chat endpoint: {e}")  # Log the error if occurred
        print("Error:", str(e))  # Prints the error if occurred in dev mode only
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=False)
