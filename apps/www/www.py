# web api工具集合，先写这里
# TODO merge all web api here
from flask import Flask, redirect


app = Flask(__name__)


@app.route('/utils/link_redir', methods=['GET'])
def link_redir():
    return redirect('https://web.kipaskipas.com', code=307)


def www():
    app.run(host='0.0.0.0', port=80)