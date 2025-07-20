import os
import datetime
import gspread
from google.oauth2.service_account import Credentials
from flask import Flask, render_template, request, jsonify
import json

# --- Flaskアプリケーションの初期化 ---
app = Flask(__name__)

# --- Google Sheets APIとの連携設定 ---

def get_spreadsheet_client():
    """Google Sheetsに接続するためのクライアントを取得する"""
    # Renderの環境変数から認証情報を読み込む
    creds_json_str = os.environ.get('GOOGLE_CREDENTIALS_JSON')
    
    if creds_json_str:
        # Render環境の場合：環境変数から認証情報を読み込む
        creds_dict = json.loads(creds_json_str)
        creds = Credentials.from_service_account_info(
            creds_dict,
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
    else:
        # ローカル環境の場合：ファイルから認証情報を読み込む
        # このファイルは .gitignore されている必要があります
        creds = Credentials.from_service_account_file(
            'credentials.json',
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
    
    client = gspread.authorize(creds)
    return client

# スプレッドシートとワークシートの名前
SPREADSHEET_NAME = 'ハイスコア'
WORKSHEET_NAME = 'Sheet1' # 通常はデフォルトのシート名

def ensure_sheet_header(sheet):
    """シートのヘッダーを確認し、なければ作成する"""
    header = sheet.row_values(1)
    if header != ['タイムスタンプ', '合計点', 'タイム(秒)']:
        # ヘッダーが正しくない、または空の場合
        sheet.update('A1:C1', [['タイムスタンプ', '合計点', 'タイム(秒)']])
        print("スプレッドシートのヘッダーを作成/修正しました。")


# --- ルート（URLと処理の紐付け） ---

@app.route('/')
def index():
    """トップページを表示する"""
    return render_template('index.html')

@app.route('/api/scores', methods=['GET'])
def get_high_scores():
    """ハイスコアのリストを取得するAPI"""
    try:
        client = get_spreadsheet_client()
        sheet = client.open(SPREADSHEET_NAME).worksheet(WORKSHEET_NAME)
        ensure_sheet_header(sheet)
        
        records = sheet.get_all_records()
        
        # scoreとtimeを数値に変換
        for record in records:
            record['合計点'] = int(record['合計点'])
            record['タイム(秒)'] = int(record['タイム(秒)'])

        sorted_scores = sorted(records, key=lambda x: (-x['合計点'], x['タイム(秒)']))
        
        response_data = [{'score': r['合計点'], 'time': r['タイム(秒)']} for r in sorted_scores]

        return jsonify(response_data[:5])
    except gspread.exceptions.SpreadsheetNotFound:
        print(f"スプレッドシート '{SPREADSHEET_NAME}' が見つかりません。")
        return jsonify({"error": "Spreadsheet not found"}), 500
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
        client = get_spreadsheet_client()
        sheet = client.open(SPREADSHEET_NAME).worksheet(WORKSHEET_NAME)
        ensure_sheet_header(sheet) # 保存時にもヘッダーを確認
        
        new_row = [
            datetime.datetime.now().isoformat(),
            data['score'],
            data['time']
        ]
        
        sheet.append_row(new_row)
        
        return jsonify({"status": "success"})
    except Exception as e:
        print(f"スコアの保存中にエラーが発生しました: {e}")
        return jsonify({"error": "Failed to save score"}), 500

# --- ローカル開発用の設定 ---
if __name__ == '__main__':
    # credentials.jsonの存在チェック
    if not os.path.exists('credentials.json'):
        print("警告: credentials.json が見つかりません。ローカルでの実行にはこのファイルが必要です。")
    app.run(debug=True)
