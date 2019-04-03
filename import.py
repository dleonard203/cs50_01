from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import csv

database_url = "postgres://ioovleludzhxle:a966a7d36f9e61edd437415d538afd38b89ab723d71177647d3766c32e0b2106@ec2-54-221-243-211.compute-1.amazonaws.com:5432/d3a4ekarkutr2s"
engine = create_engine(database_url)
db = scoped_session(sessionmaker(bind=engine))

def import_books():
    csv_file = open('books.csv', 'r')
    rows = csv.reader(csv_file, delimiter=',')
    cur_row = 0
    db.execute("""CREATE TABLE books (
        id SERIAL PRIMARY KEY,
        isbn varchar NOT NULL,
        title varchar NOT NULL,
        author varchar NOT NULL,
        year INTEGER NOT NULL)""")
    for row in rows:
        if cur_row != 0:
            db.execute("INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)",
            {"isbn": row[0], "title": row[1], "author": row[2], "year": int(row[3])})
        cur_row += 1
    db.commit()
        





if __name__ == '__main__':
    import_books()