from flask import Flask, render_template, jsonify
import pandas as pd
import glob
import os
import re

app = Flask(__name__)

def clean_prefecture_name(name):
    """都道府県名をクリーニング"""
    if not isinstance(name, str):
        return None
    
    # 不要な文字列を削除
    name = name.strip()
    name = re.sub(r'^[0-9]+', '', name)  # 先頭の数字を削除
    name = re.sub(r'施設所在地.*', '', name)
    name = re.sub(r'及び運輸局等.*', '', name)
    name = name.replace('（47区分', '')
    name = name.strip()
    
    # 除外すべきパターン
    exclude_patterns = [
        r'令和\d+年',
        r'平成\d+年',
        r'運輸局',
        r'総数',
        r'全国',
        r'合計',
        r'注）',
        r'資料',
        r'（',
        r'月',
        r'年計'
    ]
    
    for pattern in exclude_patterns:
        if re.search(pattern, name):
            return None
    
    # 空文字や短すぎる名前を除外
    if len(name) < 2:
        return None
    
    # 正しい都道府県リスト
    valid_prefectures = [
        '北海道', '青森県', '岩手県', '宮城県', '秋田県', '山形県', '福島県',
        '茨城県', '栃木県', '群馬県', '埼玉県', '千葉県', '東京都', '神奈川県',
        '新潟県', '富山県', '石川県', '福井県', '山梨県', '長野県', '岐阜県',
        '静岡県', '愛知県', '三重県', '滋賀県', '京都府', '大阪府', '兵庫県',
        '奈良県', '和歌山県', '鳥取県', '島根県', '岡山県', '広島県', '山口県',
        '徳島県', '香川県', '愛媛県', '高知県', '福岡県', '佐賀県', '長崎県',
        '熊本県', '大分県', '宮崎県', '鹿児島県', '沖縄県'
    ]
    
    # 正しい都道府県名のみ許可
    if name in valid_prefectures:
        return name
    
    return None

def load_data():
    """CSVファイルを読み込む（クリーニング強化版）"""
    csv_dir = "csv_output"
    
    if not os.path.exists(csv_dir):
        os.makedirs(csv_dir)
        print(f"⚠️ ディレクトリが作成されました: {csv_dir}")
        return []
    
    files = glob.glob(f"{csv_dir}/*.csv")
    
    if not files:
        print(f"⚠️ {csv_dir} にCSVファイルがありません")
        return []
    
    print(f"📁 {len(files)} 個のCSVファイルを検出しました")
    
    all_data = []
    
    for file in files:
        try:
            # データ行の開始位置を探す
            df_raw = pd.read_csv(file, nrows=15)
            
            data_start_row = None
            prefectures = ['北海道', '青森', '岩手', '宮城', '秋田']
            
            for i in range(len(df_raw)):
                first_col = str(df_raw.iloc[i, 0])
                if any(pref in first_col for pref in prefectures):
                    data_start_row = i
                    break
            
            if data_start_row is None:
                continue
            
            # データ行から読み込み
            df = pd.read_csv(file, skiprows=data_start_row, header=None)
            
            filename = os.path.basename(file)
            print(f"  📄 処理中: {filename}")
            
            # 第2表（延べ宿泊者数）
            if '第2表' in filename or '第２表' in filename:
                if df.shape[1] >= 17:
                    for _, row in df.iterrows():
                        prefecture_raw = str(row[0]).strip()
                        prefecture = clean_prefecture_name(prefecture_raw)
                        
                        if not prefecture:
                            continue
                        
                        # 総数
                        try:
                            total_value = int(float(str(row[1]).replace(',', '')))
                            if total_value > 0:
                                all_data.append({
                                    'prefecture': prefecture,
                                    'value': total_value,
                                    'nationality': '総数'
                                })
                        except:
                            pass
                        
                        # 外国人
                        try:
                            foreign_value = int(float(str(row[16]).replace(',', '')))
                            if foreign_value > 0:
                                all_data.append({
                                    'prefecture': prefecture,
                                    'value': foreign_value,
                                    'nationality': '外国人'
                                })
                        except:
                            pass
            
            # 参考第1表（外国人国籍別）
            elif '参考第1表' in filename or '参考第１表' in filename:
                nationalities = ['韓国', '中国', '香港', '台湾', '米国', 'カナダ', 
                               '英国', 'ドイツ', 'フランス', 'ロシア', 'シンガポール',
                               'タイ', 'マレーシア', 'インド', 'オーストラリア']
                
                for _, row in df.iterrows():
                    prefecture_raw = str(row[0]).strip()
                    prefecture = clean_prefecture_name(prefecture_raw)
                    
                    if not prefecture:
                        continue
                    
                    for i, nationality in enumerate(nationalities):
                        if i + 2 < len(row):
                            try:
                                value = int(float(str(row[i + 2]).replace(',', '')))
                                if value > 0:
                                    all_data.append({
                                        'prefecture': prefecture,
                                        'value': value,
                                        'nationality': nationality
                                    })
                            except:
                                continue
            
            # 第4表（実宿泊者数）
            elif '第4表' in filename or '第４表' in filename:
                if df.shape[1] >= 2:
                    for _, row in df.iterrows():
                        prefecture_raw = str(row[0]).strip()
                        prefecture = clean_prefecture_name(prefecture_raw)
                        
                        if not prefecture:
                            continue
                        
                        try:
                            value = int(float(str(row[1]).replace(',', '')))
                            if value > 0:
                                all_data.append({
                                    'prefecture': prefecture,
                                    'value': value,
                                    'nationality': '実宿泊者'
                                })
                        except:
                            continue
        
        except Exception as e:
            print(f"❌ エラー {os.path.basename(file)}: {e}")
    
    # 無効なデータを除外
    all_data = [d for d in all_data if d['prefecture'] and d['value'] > 0]
    
    print(f"\n📊 合計 {len(all_data)} 件の有効なデータを読み込みました\n")
    return all_data


@app.route('/')
def index():
    """トップページ（ダッシュボード）"""
    data = load_data()
    
    if not data:
        message = "⚠️ データがありません。csv_output ディレクトリにCSVファイルを配置してください。"
        return render_template('index.html', data=[], message=message, total=0)
    
    # 全データをJavaScriptに渡す
    return render_template('index.html', data=data, message=None, total=len(data))


@app.route('/data')
def data_page():
    """全データ表示ページ"""
    data = load_data()
    
    if not data:
        message = "⚠️ データがありません"
        return render_template('data.html', data=[], message=message)
    
    return render_template('data.html', data=data, message=None)


@app.route('/api/data')
def api_data():
    """JSON API"""
    data = load_data()
    
    if not data:
        return jsonify({
            'status': 'error',
            'message': 'データが見つかりません',
            'count': 0,
            'data': []
        }), 404
    
    return jsonify({
        'status': 'success',
        'count': len(data),
        'data': data
    })


@app.route('/status')
def status():
    """ステータス確認"""
    csv_dir = "csv_output"
    files = glob.glob(f"{csv_dir}/*.csv")
    data = load_data()
    
    return jsonify({
        'csv_directory': csv_dir,
        'csv_files': [os.path.basename(f) for f in files],
        'file_count': len(files),
        'data_count': len(data),
        'port': 8080
    })


if __name__ == '__main__':
    print("=" * 70)
    print("🚀 Flask Application Starting on PORT 8080")
    print("=" * 70)
    
    # 起動時にデータ読み込み
    data = load_data()
    
    print("\n🌐 アクセス方法:")
    print("   http://127.0.0.1:8080          - トップページ")
    print("   http://127.0.0.1:8080/data     - 全データ")
    print("   http://127.0.0.1:8080/api/data - JSON API")
    print("   http://127.0.0.1:8080/status   - ステータス確認")
    print("")
    print("=" * 70)
    print("")
    
    app.run(debug=True, port=8080, host='0.0.0.0')