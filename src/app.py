from flask import Flask, render_template, jsonify, request, redirect, url_for, session
from helper import TableListClass     
import os
from logger import logging
import time
import json
from reltiocom import APICallClass

os.chdir("src/")
app = Flask(__name__)

# Secret key for session management
app.secret_key = "sample"

obj = TableListClass()

@app.route("/")
def welcome():
    # Set a session variable to indicate the user has visited the welcome page
    session['visited_welcome'] = True
    return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Welcome</title>
            <style>
                body {
                    background-color: #f0f8ff; /* Light blue background */
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                    font-family: Arial, sans-serif;
                    color: #333; /* Dark text for contrast */
                }
                .container {
                    text-align: center;
                }
                button {
                    background-color: #4CAF50; /* Green button */
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    font-size: 16px;
                    cursor: pointer;
                    border-radius: 5px;
                }
                button:hover {
                    background-color: #45a049; /* Darker green on hover */
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Welcome to Reltio SQL Chatbot!</h1>
                <p>Press here to chat.</p>
                <form action="/index">
                    <button type="submit">Submit</button>
                </form>
            </div>
        </body>
        </html>
    '''

@app.route("/index")
def index():
    # Redirect to welcome page if user hasn't visited it yet
    if not session.get('visited_welcome'):
        return redirect(url_for('welcome'))
    return render_template('index.html')

@app.route("/get", methods=["GET", "POST"])
def chat():
    msg = request.form["msg"]
    input = msg
    print(input)
    response = obj.full_chain_call(input)
    logging.info(f"Response value is : {response}")
    print("Response : ", response)
    return jsonify(response)

def generate_stream():
    def generate():
        for row in chat():
            yield f"{','.join(row)}\n"
            time.sleep(0.01)  # Simulate some delay in processing
    return jsonify(app.response_class(generate(), mimetype='json'))

@app.route('/get_toggled_status') 
def toggled_status():
  current_status = request.args.get('status')
  apicallclass = APICallClass()
  print("API Call Started")
  if current_status == 'Refreshing':
    apicallclass.execute_workflow()
  else:
      print("Toggle is off")  
  print(f"Toggle status changed is : {current_status}")
  print("API Call Completed")
  return '' if current_status == 'Refreshing' else 'Refreshing'

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080, debug=True)
