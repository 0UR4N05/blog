from src.init import app
from flask import render_template
from src.serve import *

@app.route("/")
def main():
    return (render_template('index.html'))

if __name__ == "__main__":
    app.run(debug=True)
