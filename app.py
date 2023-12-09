from flask import Flask, render_template, request, jsonify
import openai
import os
import time

app = Flask(__name__)

# Set the OpenAI API key
openai.api_key = os.environ.get('OPENAI_API_KEY')

# Global variable to store the thread ID
global_thread_id = None

def create_thread(ass_id, prompt):
    global global_thread_id

    # Check if a thread already exists, create one if not
    if not global_thread_id:
        thread = openai.beta.threads.create()
        global_thread_id = thread.id

    my_thread_id = global_thread_id

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

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json['message']
    print("Received request:", request.json) # Logs the received message

    try:
        assistant_id = "asst_JZnFQkifZLY3r1C5uaL1cgpg"
        my_run_id, my_thread_id = create_thread(assistant_id, user_input)
        time.sleep(10)
        # Assuming immediate response, get the latest response
        response = openai.beta.threads.messages.list(thread_id=my_thread_id)
        #if response.data:
        #    chat_response = response.data[-1].content[0].text.value
        print("Sending response with Thread ID:", response)
        return jsonify({'response': f"{response}\n\nThread ID: {my_thread_id}"})
    except Exception as e:
        print("Error:", str(e))
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True)
