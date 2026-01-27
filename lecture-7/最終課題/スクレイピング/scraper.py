"""
観光データスクレイピングツール（月情報対応版）
使い方: python scraper.py
"""

import requests
import sqlite3
from datetime import datetime

# 設定
API_URL = 'http://127.0.0.1:8080/api/data'
DB_PATH = 'tourism_data.db'

def init_database():
    """データベース初期化"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # ★ month カラムを追加
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tourism_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prefecture TEXT NOT NULL,
            nationality TEXT NOT NULL,
            value INTEGER NOT NULL,
            month INTEGER,
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(prefecture, nationality, month)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scraping_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            records_added INTEGER,
            status TEXT,
            message TEXT,
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ データベース初期化完了")

def scrape_data():
    """APIからデータ取得してDBに保存"""
    print("\n" + "="*60)
    print("🕷️  スクレイピング開始")
    print("="*60)
    
    try:
        # API呼び出し
        print(f"📡 接続中: {API_URL}")
        response = requests.get(API_URL, timeout=10)
        
        if response.status_code != 200:
            raise Exception(f"HTTPエラー: {response.status_code}")
        
        data = response.json()
        
        if data.get('status') != 'success':
            raise Exception(f"APIエラー: {data.get('message')}")
        
        records = data['data']
        print(f"✅ {len(records)} 件のデータを取得")
        
        # データベースに保存
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        inserted = 0
        updated = 0
        
        for item in records:
            try:
                # ★ month を追加
                month = item.get('month')
                
                cursor.execute('''
                    INSERT INTO tourism_data (prefecture, nationality, value, month)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(prefecture, nationality, month) 
                    DO UPDATE SET value=excluded.value, scraped_at=CURRENT_TIMESTAMP
                ''', (item['prefecture'], item['nationality'], item['value'], month))
                
                if cursor.rowcount > 0:
                    if cursor.lastrowid:
                        inserted += 1
                    else:
                        updated += 1
            except Exception as e:
                print(f"⚠️ データ挿入エラー: {e}")
        
        # ログ保存
        cursor.execute('''
            INSERT INTO scraping_log (records_added, status, message)
            VALUES (?, ?, ?)
        ''', (inserted, 'success', f'新規:{inserted}, 更新:{updated}'))
        
        conn.commit()
        conn.close()
        
        print(f"✅ 保存完了: 新規 {inserted} 件 / 更新 {updated} 件")
        print("="*60)
        
        return True
        
    except requests.exceptions.ConnectionError:
        error_msg = "接続エラー: Flaskサーバーが起動していません"
        print(f"❌ {error_msg}")
        print("   先に別ターミナルで `python app.py` を実行してください")
        
        # エラーログ保存
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO scraping_log (records_added, status, message)
            VALUES (?, ?, ?)
        ''', (0, 'error', error_msg))
        conn.commit()
        conn.close()
        
        return False
        
    except Exception as e:
        error_msg = f"エラー: {str(e)}"
        print(f"❌ {error_msg}")
        
        # エラーログ保存
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO scraping_log (records_added, status, message)
            VALUES (?, ?, ?)
        ''', (0, 'error', error_msg))
        conn.commit()
        conn.close()
        
        return False

def show_stats():
    """データベース統計表示"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM tourism_data')
    total = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(DISTINCT prefecture) FROM tourism_data')
    pref_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(DISTINCT nationality) FROM tourism_data')
    nat_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT SUM(value) FROM tourism_data')
    total_visitors = cursor.fetchone()[0] or 0
    
    # ★ 月別データ数を表示
    cursor.execute('SELECT COUNT(DISTINCT month) FROM tourism_data WHERE month IS NOT NULL')
    month_count = cursor.fetchone()[0]
    
    print(f"\n📊 データベース統計:")
    print(f"  総レコード数: {total:,}")
    print(f"  都道府県数: {pref_count}")
    print(f"  国籍種類数: {nat_count}")
    print(f"  月別データ数: {month_count} ヶ月分")
    print(f"  総宿泊者数: {total_visitors:,} 人泊")
    
    # ★ 月別集計を表示
    cursor.execute('''
        SELECT month, COUNT(*), SUM(value) 
        FROM tourism_data 
        WHERE month IS NOT NULL
        GROUP BY month 
        ORDER BY month
    ''')
    
    monthly = cursor.fetchall()
    if monthly:
        print(f"\n📅 月別データ:")
        for m in monthly:
            month_label = f"{m[0]}月" if m[0] > 0 else "年計"
            print(f"  {month_label}: {m[1]:,} 件 / {m[2]:,} 人泊")
    
    # 最新のスクレイピングログ
    cursor.execute('''
        SELECT scraped_at, records_added, status, message 
        FROM scraping_log 
        ORDER BY id DESC 
        LIMIT 5
    ''')
    
    logs = cursor.fetchall()
    if logs:
        print(f"\n📋 最近のスクレイピング履歴:")
        for log in logs:
            status_icon = "✅" if log[2] == 'success' else "❌"
            print(f"  {status_icon} {log[0]} - {log[3]}")
    
    conn.close()

if __name__ == '__main__':
    print("\n🚀 観光データ スクレイピングツール")
    print("\n事前準備:")
    print("  1. 別ターミナルで `python app.py` を実行")
    print("  2. http://127.0.0.1:8080 が起動していることを確認")
    
    input("\n準備ができたら Enter を押してください...")
    
    # DB初期化
    init_database()
    
    # スクレイピング実行
    success = scrape_data()
    
    # 統計表示
    show_stats()
    
    if success:
        print("\n✅ スクレイピング完了！")
    else:
        print("\n❌ スクレイピング失敗")