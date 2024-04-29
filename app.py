from flask import Flask, render_template, request, jsonify, session
import logging
import openai
import os
import time
import markdown
import bleach
import json
from utils.token_counter import count_thread_tokens
from api.google_civic_api import get_representatives


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

#list run steps. steps used to identify function and function arguments being ran by the bot.
def get_run_steps(thread_id, run_id):
    run_steps= client.beta.threads.runs.steps.list(
    thread_id=thread_id,
    run_id=run_id,
    )
    return run_steps




@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json['message']

    # Define the maximum allowed characters
    MAX_CHARS = 300  # Set your desired limit

    if len(user_input) > MAX_CHARS:
        return jsonify({'error': 'Input exceeds the maximum allowed character limit.'}), 300

    allowed_tags = ['b', 'i', 'hr', 'p', 'br ', 'n'] #Tags allowed by bleach. everything else is sanitised
    sanitised_input = bleach.clean(user_input, tags = allowed_tags) #Sanitize user input to prevent malicious html insert

    app.logger.info(f"Received request: {sanitised_input}")  # Log the received message
    print("Received request:", request.json) # Prints the received message in dev mode only.

    try:
        assistant_id = "asst_QYgQz5e5ru1kQFn6JeRXiTnS"  # Replace with environment variable in prod
        my_run_id, my_thread_id = create_thread(assistant_id, sanitised_input)

        response = client.beta.threads.messages.list(
            thread_id=my_thread_id
        )

        run_status = check_status(my_run_id, my_thread_id)

        while run_status in ['queued', 'in_progress']:
            run_status = check_status(my_run_id, my_thread_id)
            time.sleep(1)

        if run_status == 'requires_action':
            steps_output = get_run_steps(my_thread_id, my_run_id) #Call function to fetch steps.
            
            # Extract function name and arguments
            step_details = steps_output.data[0].step_details.tool_calls[0]
            gpt_function_name = step_details.function.name
            gpt_tool_call_id = step_details.id
            gpt_function_arguments = json.loads(step_details.function.arguments)
        
            #fixed ressponse for testing purposes. replace with API call to google.
            if gpt_function_name == "get_rep_details" and (gpt_function_arguments.get('country') == 'US' or gpt_function_arguments.get('country') == 'USA'):
                client.beta.threads.runs.submit_tool_outputs(
                thread_id=my_thread_id,
                run_id=my_run_id,
                tool_outputs=[
                    {
                        "tool_call_id": gpt_tool_call_id,
                        "output": "1 high street, California"
                    }
                ]
                )
            else:
                client.beta.threads.runs.submit_tool_outputs(
                thread_id=my_thread_id,
                run_id=my_run_id,
                tool_outputs=[
                    {
                        "tool_call_id": gpt_tool_call_id,
                        "output": "Could not find requested details. This feature is only available for US postcodes at the moment."
                    }
                ]
                )
            run_status = check_status(my_run_id, my_thread_id)
            while run_status in ['queued', 'in_progress']:
                run_status = check_status(my_run_id, my_thread_id)
                time.sleep(1)

            response = client.beta.threads.messages.list(
                thread_id=my_thread_id
            )

        else:
            #For debugging. Remove after function calling is implemented.
            #app.logger.info(f"Function name: {gpt_function_name}")
            #app.logger.info(f"Function arguments: {gpt_function_arguments}")
            #app.logger.info(f"Function tool call id: {gpt_tool_call_id}")

            #Run message status check againfollowing 
            run_status = check_status(my_run_id, my_thread_id)
            while run_status in ['queued', 'in_progress']:
                run_status = check_status(my_run_id, my_thread_id)
                time.sleep(1)

            response = client.beta.threads.messages.list(
                thread_id=my_thread_id
            )

        app.logger.info(f"updated message content: {response}")
        print(response)

        if response.data:
            chat_response = response.data[0].content[0].text.value
            chat_response_html = markdown.markdown(chat_response, extensions=['nl2br']) #Convert markdown to HTML with nl2br extension to handle conversion of single new lines (\n) into breaks and double new lines (\n\n) into paragraph breaks.

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
