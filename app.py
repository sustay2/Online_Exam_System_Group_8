from src.online_exam import create_app


def create():
    return create_app()


# For running directly (python app.py)
if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
