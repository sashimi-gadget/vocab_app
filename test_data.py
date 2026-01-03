from app import app, db, Word

with app.app_context():
    words = [
        Word(
            english="apple",
            meaning="りんご",
            part_of_speech="noun",
            example="I eat an apple every morning."
        ),
        Word(
            english="run",
            meaning="走る",
            part_of_speech="verb",
            example="She runs in the park every day."
        ),
        Word(
            english="beautiful",
            meaning="美しい",
            part_of_speech="adjective",
            example="The city is beautiful at night."
        ),
        Word(
            english="quickly",
            meaning="素早く",
            part_of_speech="adverb",
            example="He finished his homework quickly."
        ),
        Word(
            english="study",
            meaning="勉強する",
            part_of_speech="verb",
            example="I study English every day."
        ),
        Word(
            english="book",
            meaning="本",
            part_of_speech="noun",
            example="This book is very interesting."
        ),
        Word(
            english="important",
            meaning="重要な",
            part_of_speech="adjective",
            example="It is important to practice every day."
        ),
        Word(
            english="slowly",
            meaning="ゆっくりと",
            part_of_speech="adverb",
            example="Please speak slowly."
        )
    ]

    db.session.add_all(words)
    db.session.commit()