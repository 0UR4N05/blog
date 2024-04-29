from flask import Flask, render_template
from src.getfiles import return_files
from src.init import app

@app.route("/")
def main():
    dirs = return_files()
    return (render_template('index.html', dirs=dirs))

if (__name__ == "__main__"):
    app.run()
