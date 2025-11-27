from src.online_exam import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
