from flask import Flask
from flask import render_template

app = Flask(__name__)


@app.route('/config')
def config():
    active = {"status": "", "config": "active"}
    return render_template('config.html', active=active)


@app.route('/')
def status():
    active = {"status": "active", "config": ""}
    return render_template('status.html', active=active)


if __name__ == '__main__':
    app.run()
