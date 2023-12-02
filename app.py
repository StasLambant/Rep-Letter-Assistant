from flask import Flask, render_template, request, jsonify
import openai
import os
import time

app = Flask(__name__)

# Set the OpenAI API key
openai.api_key = os.environ.get('OPENAI_API_KEY')

def create_thread(ass_id, prompt):
    # Create a thread
    thread = openai.beta.threads.create()
    my_thread_id = thread.id

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

    return run.id, thread.id

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
    print("Received request:", request.json) # Logs the received message

    try:
        assistant_id = "asst_JZnFQkifZLY3r1C5uaL1cgpg"  # Replace with your assistant ID
        my_run_id, my_thread_id = create_thread(assistant_id, user_input)

        status = check_status(my_run_id, my_thread_id)

        while status != "completed":
            status = check_status(my_run_id, my_thread_id)
            time.sleep(2)

        response = openai.beta.threads.messages.list(
            thread_id=my_thread_id
        )

        if response.data:
            chat_response = response.data[0].content[0].text.value
            print("Sending response:", chat_response)  # Logs the response being sent back
            return jsonify({'response': chat_response})
    except Exception as e:
        print("Error:", str(e))  # Logs the error if occurred
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True)
