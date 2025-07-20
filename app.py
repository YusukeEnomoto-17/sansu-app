import datetime
from flask import Flask, render_template, request, jsonify

# --- Flaskアプリケーションの初期化 ---
app = Flask(__name__)

# --- 簡易的なインメモリデータベース ---
# このリストは、アプリが再起動するたびに空になります。
high_scores = []

# --- ルート（URLと処理の紐付け） ---

@app.route('/')
def index():
    """トップページを表示する"""
    return render_template('index.html')

@app.route('/api/scores', methods=['GET'])
def get_high_scores():
    """ハイスコアのリストを取得するAPI"""
    try:
        # high_scoresリストをスコア（降順）、タイム（昇順）で並び替え
        # scoreをマイナスにすることで降順ソートを実現
        sorted_scores = sorted(high_scores, key=lambda x: (-x['score'], x['time']))
        
        # 上位5件を返す
        return jsonify(sorted_scores[:5])
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
        # 新しいスコアデータを作成
        new_score = {
            'score': data['score'],
            'time': data['time'],
            'timestamp': datetime.datetime.now().isoformat()
        }
        
        # high_scoresリストに追加
        high_scores.append(new_score)
        
        return jsonify({"status": "success"})
    except Exception as e:
        print(f"スコアの保存中にエラーが発生しました: {e}")
        return jsonify({"error": "Failed to save score"}), 500

# --- ローカル開発用の設定 ---
if __name__ == '__main__':
    app.run(debug=True)
