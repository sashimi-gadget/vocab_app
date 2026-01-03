from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask import request, redirect, url_for
from flask import request
import random
from flask import session
import csv
import io
from flask import Response
from datetime import date
_database_initialized = False

app = Flask(__name__)

app.secret_key = 'secret-key-for-vocab-app'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///vocab.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Word(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    english = db.Column(db.String(100), nullable=False)
    meaning = db.Column(db.String(200), nullable=False)
    part_of_speech = db.Column(db.String(50))
    example = db.Column(db.String(300))
    correct_count = db.Column(db.Integer, default=0)
    wrong_count = db.Column(db.Integer, default=0)
    is_done = db.Column(db.Boolean, default=False)

@app.before_request
def setup_db():
    global _database_initialized
    if not _database_initialized:
        # ここに最初の1回だけやりたい処理を書く
        # db.create_all() など
        _database_initialized = True

@app.route('/') #一覧
def index():
    words = Word.query.all()
    return render_template('index.html', title='単語一覧', words=words)

@app.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        word = Word(
            english=request.form['english'],
            meaning=request.form['meaning'],
            part_of_speech=request.form['part_of_speech'],
            example=request.form['example']
        )
        db.session.add(word)
        db.session.commit()
        return redirect(url_for('index'))

    return render_template('add.html', title='単語追加')


@app.route('/delete/<int:id>') #削除
def delete(id):
    word = Word.query.get_or_404(id)
    db.session.delete(word)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/edit/<int:id>', methods=['GET', 'POST']) #編集
def edit(id):
    word = Word.query.get_or_404(id)

    if request.method == 'POST':
        word.english = request.form['english']
        word.meaning = request.form['meaning']
        word.part_of_speech = request.form['part_of_speech']
        word.example = request.form['example']
        db.session.commit()
    return redirect(url_for('index'))

    return render_template('edit.html', title='単語編集', word=word)

@app.route('/study/<int:id>', methods=['GET', 'POST'])
def study(id):
    word = Word.query.get_or_404(id)
    result = None

    if request.method == 'POST':
        user_answer = request.form['answer'].strip()

        if user_answer == word.meaning:
            word.correct_count += 1
            result = '正解'
        else:
            word.wrong_count += 1
            result = '不正解'

        db.session.commit()

    return render_template(
        'study.html',
        title='学習',
        word=word,
        result=result
    )

@app.route('/toggle_done/<int:id>')
def toggle_done(id):
    word = Word.query.get_or_404(id)
    word.is_done = not word.is_done
    db.session.commit()
    return redirect(url_for('index'))


@app.route('/study/random', methods=['GET', 'POST'])
def study_random():
    # POST時：同じ単語で判定する
    if request.method == 'POST':
        word_id = session.get('current_word_id')
        if not word_id:
            return redirect(url_for('study_random'))

        word = Word.query.get_or_404(word_id)

        user_answer = request.form['answer'].strip()

        if user_answer == word.meaning:
            word.correct_count += 1
            word.is_done = True
            result = '正解（完了！）'
        else:
            word.wrong_count += 1
            result = '不正解'

        db.session.commit()

        return render_template(
            'study_random.html',
            title='ランダム学習',
            word=word,
            result=result
        )

    # GET時：ランダムに単語を選ぶ
    words = Word.query.filter_by(is_done=False).all()

    if not words:
        session.pop('last_word_id', None)
        session.pop('current_word_id', None)
        return render_template('random_done.html', title='学習完了')

    last_word_id = session.get('last_word_id')

    candidates = [w for w in words if w.id != last_word_id]
    if not candidates:
        candidates = words

    word = random.choice(candidates)

    # ★ 今回表示する単語IDを保存
    session['current_word_id'] = word.id
    session['last_word_id'] = word.id

    return render_template(
        'study_random.html',
        title='ランダム学習',
        word=word,
        result=None
    )

@app.route('/import', methods=['GET', 'POST'])
def import_csv():
    if request.method == 'POST':
        file = request.files.get('csv_file')
        if not file:
            return redirect(url_for('index'))

        # ★ TextIOWrapperを使わない
        content = file.stream.read().decode('utf-8-sig')
        reader = csv.DictReader(io.StringIO(content))

        for row in reader:
            english = row.get('english', '').strip()
            if not english:
                continue

            existing = Word.query.filter_by(english=english).first()
            if existing:
                continue

            word = Word(
                english=english,
                meaning=row.get('meaning', '').strip(),
                part_of_speech=row.get('part_of_speech'),
                example=row.get('example')
            )
            db.session.add(word)

        db.session.commit()
        return redirect(url_for('index'))

    return render_template('import_csv.html')

@app.route('/export')
def export_csv():
    filename = f"vocab_{date.today()}.csv"
    output = io.StringIO()
    writer = csv.writer(output)

    # ヘッダー
    writer.writerow([
        'english',
        'meaning',
        'part_of_speech',
        'example',
        'correct_count',
        'wrong_count',
        'is_done'
    ])

    # データ
    words = Word.query.all()
    for word in words:
        writer.writerow([
            word.english,
            word.meaning,
            word.part_of_speech,
            word.example,
            word.correct_count,
            word.wrong_count,
            word.is_done
        ])

    # Excel用 UTF-8 BOM付き
    csv_data = '\ufeff' + output.getvalue()
    output.close()

    return Response(
        csv_data,
        mimetype='text/csv',
        headers={
            'Content-Disposition': f'attachment; filename={filename}'
        }
    )

if __name__ == '__main__':
    app.run(debug=True)

