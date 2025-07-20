import os
import sqlite3
import datetime
import psycopg2 # PostgreSQLに接続するためのライブラリ
from flask import Flask, render_template, request, jsonify, g

# --- Flaskアプリケーションの初期化 ---
app = Flask(__name__)

# --- データベース関連の関数 ---

def get_db():
    """
    リクエストごとにデータベース接続を管理する。
    Render環境ではPostgreSQLに、ローカル環境ではSQLiteに接続する。
    """
    if 'db' not in g:
        # Renderが提供するデータベースURL（環境変数）を取得
        db_url = os.environ.get('DATABASE_URL')
        if db_url:
            # Render環境の場合: PostgreSQLに接続
            g.db = psycopg2.connect(db_url)
        else:
            # ローカル環境の場合: SQLiteに接続
            app.config['DATABASE'] = 'highscore.db'
            g.db = sqlite3.connect(
                app.config['DATABASE'],
                detect_types=sqlite3.PARSE_DECLTYPES
            )
            g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(e=None):
    """リクエストの終了時にデータベース接続を閉じる"""
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    """データベースのテーブルを初期化（作成）する"""
    db = get_db()
    cursor = db.cursor()
    # PostgreSQLとSQLiteの両方で動作するスキーマ
    # id SERIAL PRIMARY KEY はPostgreSQLの自動インクリメント
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS scores (
      id SERIAL PRIMARY KEY,
      timestamp TEXT NOT NULL,
      score INTEGER NOT NULL,
      time INTEGER NOT NULL
    );
    """)
    db.commit()
    cursor.close()
    print("データベースのテーブルをチェック・初期化しました。")

# --- ルート（URLと処理の紐付け） ---

@app.route('/')
def index():
    """トップページを表示する"""
    return render_template('index.html')

@app.route('/api/scores', methods=['GET'])
def get_high_scores():
    """ハイスコアのリストを取得するAPI"""
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            'SELECT score, time FROM scores ORDER BY score DESC, time ASC LIMIT 5'
        )
        # fetchall()の結果を辞書に変換
        scores = [dict(zip([column[0] for column in cursor.description], row)) for row in cursor.fetchall()]
        cursor.close()
        return jsonify(scores)
    except Exception as e:
        print(f"スコアの取得中にエラーが発生しました: {e}")
        return jsonify({"error": "Failed to retrieve scores"}), 500


@app.route('/api/score', methods=['POST'])
def save_score():
    """スコアを保存するAPI"""
    data = request.get_json()
    if not data or 'score' not in data or 'time' not in data:
        return jsonify({"error": "無効なデータです"}), 400

    try:
        score = data['score']
        time = data['time']
        timestamp = datetime.datetime.now().isoformat()

        db = get_db()
        cursor = db.cursor()
        # PostgreSQLではプレースホルダが %s
        cursor.execute(
            'INSERT INTO scores (timestamp, score, time) VALUES (%s, %s, %s)',
            (timestamp, score, time)
        )
        db.commit()
        cursor.close()
        return jsonify({"status": "success"})
    except Exception as e:
        print(f"スコアの保存中にエラーが発生しました: {e}")
        return jsonify({"error": "Failed to save score"}), 500

# --- アプリケーションの初期化処理 ---
# このコードはGunicornでアプリが起動した時に一度だけ実行される
with app.app_context():
    init_db()

# --- ローカル開発用の設定 ---
if __name__ == '__main__':
    app.run(debug=True)
