from flask import Flask
from utils import run_auction_check
app = Flask(__name__)

@app.route('/')
def index():
    return '<h1>Essence Hub Discord Bot Server</h1>'

@app.route('/check_auctions')
def check_auctions():
    return run_auction_check()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)