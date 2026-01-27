"""
データベース管理ツール
使い方: python db_manager.py
"""

import sqlite3
import os

DB_PATH = 'tourism_data.db'

def show_stats():
    """データベース統計表示"""
    if not os.path.exists(DB_PATH):
        print("❌ データベースが見つかりません")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("\n" + "="*60)
    print("📊 データベース統計")
    print("="*60)
    
    cursor.execute('SELECT COUNT(*) FROM tourism_data')
    total = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(DISTINCT prefecture) FROM tourism_data')
    pref_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(DISTINCT nationality) FROM tourism_data')
    nat_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT SUM(value) FROM tourism_data')
    total_visitors = cursor.fetchone()[0] or 0
    
    print(f"\n【tourism_data テーブル】")
    print(f"  総レコード数: {total:,}")
    print(f"  都道府県数: {pref_count}")
    print(f"  国籍種類数: {nat_count}")
    print(f"  総宿泊者数: {total_visitors:,} 人泊")
    
    cursor.execute('SELECT COUNT(*) FROM scraping_log')
    log_count = cursor.fetchone()[0]
    print(f"\n【scraping_log テーブル】")
    print(f"  ログ件数: {log_count}")
    
    conn.close()

def show_recent_data(n=10):
    """最新データ表示"""
    if not os.path.exists(DB_PATH):
        print("❌ データベースが見つかりません")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute(f'''
        SELECT prefecture, nationality, value, scraped_at 
        FROM tourism_data 
        ORDER BY id DESC 
        LIMIT {n}
    ''')
    
    rows = cursor.fetchall()
    
    print(f"\n最新{n}件のデータ:")
    print("-" * 60)
    for row in rows:
        print(f"{row[0]:10s} {row[1]:15s} {row[2]:>12,} 人泊 ({row[3]})")
    
    conn.close()

def show_scraping_history(n=10):
    """スクレイピング履歴表示"""
    if not os.path.exists(DB_PATH):
        print("❌ データベースが見つかりません")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute(f'''
        SELECT scraped_at, records_added, status, message 
        FROM scraping_log 
        ORDER BY id DESC 
        LIMIT {n}
    ''')
    
    rows = cursor.fetchall()
    
    print(f"\n📋 スクレイピング履歴（最新{n}件）:")
    print("-" * 60)
    for row in rows:
        status_icon = "✅" if row[2] == 'success' else "❌"
        print(f"{status_icon} {row[0]} - {row[3]}")
    
    conn.close()

def clear_data():
    """データ削除"""
    if not os.path.exists(DB_PATH):
        print("❌ データベースが見つかりません")
        return
    
    print("\n⚠️  警告: 全データが削除されます")
    confirm = input("本当に削除しますか？ (yes/no): ").strip().lower()
    
    if confirm != 'yes':
        print("キャンセルしました")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM tourism_data')
    data_deleted = cursor.rowcount
    
    cursor.execute('DELETE FROM scraping_log')
    log_deleted = cursor.rowcount
    
    conn.commit()
    conn.close()
    
    print(f"✅ {data_deleted} 件のデータを削除しました")
    print(f"✅ {log_deleted} 件のログを削除しました")

def export_to_csv():
    """CSVエクスポート"""
    if not os.path.exists(DB_PATH):
        print("❌ データベースが見つかりません")
        return
    
    import pandas as pd
    from datetime import datetime
    
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query('SELECT * FROM tourism_data', conn)
    conn.close()
    
    if df.empty:
        print("⚠️ データがありません")
        return
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filepath = f'tourism_export_{timestamp}.csv'
    df.to_csv(filepath, index=False, encoding='utf-8-sig')
    
    print(f"✅ CSVエクスポート: {filepath}")
    print(f"   {len(df)} 件のレコードを出力しました")

def interactive_menu():
    """対話型メニュー"""
    while True:
        print("\n" + "="*60)
        print("🗄️  データベース管理ツール")
        print("="*60)
        print("1. データベース統計表示")
        print("2. 最新データ表示")
        print("3. スクレイピング履歴表示")
        print("4. CSVエクスポート")
        print("5. 全データ削除（危険）")
        print("0. 終了")
        print("="*60)
        
        choice = input("\n選択 (0-5): ").strip()
        
        if choice == '0':
            print("\n👋 終了します")
            break
        
        elif choice == '1':
            show_stats()
        
        elif choice == '2':
            n = input("表示件数 (デフォルト10): ").strip()
            n = int(n) if n.isdigit() else 10
            show_recent_data(n)
        
        elif choice == '3':
            n = input("表示件数 (デフォルト10): ").strip()
            n = int(n) if n.isdigit() else 10
            show_scraping_history(n)
        
        elif choice == '4':
            export_to_csv()
        
        elif choice == '5':
            clear_data()
        
        else:
            print("⚠️ 無効な選択です")

if __name__ == '__main__':
    interactive_menu()