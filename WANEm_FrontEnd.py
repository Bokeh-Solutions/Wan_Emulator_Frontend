from flask import Flask
from flask import render_template

app = Flask(__name__)


@app.route('/config')
def config():
    active = {"status": "", "config": "bg-success"}
    return render_template('config.html', active=active)


@app.route('/')
def status():
    active = {"status": "bg-success", "config": ""}
    return render_template('status.html', active=active)


if __name__ == '__main__':
    app.run()
