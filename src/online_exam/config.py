class Config:
    DB_NAME = "examdb"
    DB_USER = "examuser"
    DB_PASSWORD = "Exam123%40"
    DB_HOST = "localhost"
    DB_PORT = "3306"

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = "dev-secret-key"