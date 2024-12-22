from src.init import app
from flask import render_template
from src.serve import *

@app.route('/content/<path:filename>')
def serve_file(filename):
    return send_from_directory('../content', filename)

@app.route("/")
def main():
    return (render_template('index.html'))

@app.route("/<path:filename>")
def servex(filename):
    return (render_template('index.html'))

if __name__ == "__main__":
    app.run()
