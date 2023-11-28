from flask import Flask, render_template, request, jsonify
#from flask_cors import CORS
from openai import OpenAI
import os

app = Flask(__name__)
#CORS(app)

# Initialize the OpenAI client with the API key
client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json['message']
    print("Received request:", request.json) # Logs the received message
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": user_input}]
        )
        # Accessing the response directly
        chat_response = response.choices[0].message.content
        print("Sending response:", chat_response)  # Logs the response being sent back
        return jsonify({'response': chat_response})
    except Exception as e:
        print("Error:", str(e))  # Logs the error if occurred
        return jsonify({'error': str(e)})
        
if __name__ == '__main__':
    app.run(debug=True)
