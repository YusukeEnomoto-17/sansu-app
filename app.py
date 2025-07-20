import sqlite3
import datetime
import os
from flask import Flask, render_template, request, jsonify, g

# --- Flaskアプリケーションの初期化 ---
app = Flask(__name__)
# データベースファイル名を指定
DATABASE = 'highscore.db'
app.config['DATABASE'] = DATABASE


# --- データベース関連の関数 ---

def get_db():
    """
    現在のリクエストでデータベース接続がなければ作成し、あれば既存のものを返す。
    Flaskのgオブジェクトを使い、リクエスト内で接続を再利用する。
    """
    if 'db' not in g:
        g.db = sqlite3.connect(
            app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        # カラム名でアクセスできるようにする
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
    # 外部ファイルに頼らず、直接スキーマを記述する
    schema = """
    CREATE TABLE IF NOT EXISTS scores (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      timestamp TEXT NOT NULL,
      score INTEGER NOT NULL,
      time INTEGER NOT NULL
    );
    """
    db.executescript(schema)
    print("データベースを初期化しました。")

# Flaskのコマンドラインから `flask init-db` でDBを初期化できるようにする
@app.cli.command('init-db')
def init_db_command():
    """データベーステーブルをクリアして作成します。"""
    with app.app_context():
        init_db()
    print('データベースを初期化しました。')


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
        # スコアの降順、タイムの昇順で上位5件を取得するように変更
        scores_cursor = db.execute(
            'SELECT score, time FROM scores ORDER BY score DESC, time ASC LIMIT 5'
        )
        scores = scores_cursor.fetchall()
        # 取得したデータをJSON形式で返す
        return jsonify([dict(row) for row in scores])
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
        db.execute(
            'INSERT INTO scores (timestamp, score, time) VALUES (?, ?, ?)',
            (timestamp, score, time)
        )
        db.commit() # 変更を確定
        return jsonify({"status": "success"})
    except Exception as e:
        print(f"スコアの保存中にエラーが発生しました: {e}")
        return jsonify({"error": "Failed to save score"}), 500

# --- アプリケーションの実行 ---
if __name__ == '__main__':
    # アプリケーションコンテキスト内でデータベースの存在を確認し、なければ初期化
    with app.app_context():
        if not os.path.exists(DATABASE):
            print(f"'{DATABASE}'が見つからないため、新規に作成します。")
            init_db()
    
    # Flaskの開発サーバーを起動
    app.run(debug=True)
