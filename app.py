from flask import Flask, request, render_template, jsonify
from V2CHAT import Session

app = Flask(__name__)
session = Session()
@app.route('/', methods=['POST'])
def handle_request():
    data = request.get_json()
    user_input = data['input']
    response = session.reply(user_input)
    return {'response': response}
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_input = data['message']
    response = session.reply(user_input)
    return jsonify({'message': response})
def printMsg():
    app.logger.warning('testing warning log')
    app.logger.error('testing error log')
    app.logger.info('testing info log')
    return "Check your console"
if __name__ == '__main__':
    app.run(debug=True)