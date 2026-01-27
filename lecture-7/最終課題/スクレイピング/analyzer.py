"""
観光データ月別分析ツール
"""

import sqlite3
import matplotlib
matplotlib.use('Agg')  # ★ バックエンドモード（画像表示しない）
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import japanize_matplotlib
from pathlib import Path
import os



# 除外する集計カテゴリ
EXCLUDE_CATEGORIES = ['実宿泊者', '総数', '外国人']

def connect_db():
    """データベース接続"""
    script_dir = Path(__file__).parent
    db_path = script_dir / 'tourism_data.db'
    
    print(f"📂 DB ファイルパス: {db_path}")
    
    if not db_path.exists():
        print(f"❌ エラー: {db_path} が見つかりません")
        exit(1)
    
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    
    # 月別データ確認
    cur.execute("SELECT COUNT(DISTINCT month) FROM tourism_data WHERE month IS NOT NULL")
    month_count = cur.fetchone()[0]
    print(f"✅ データベース接続成功: {month_count} 月分のデータ\n")
    
    return conn

def get_available_months(conn):
    """利用可能な月リストを取得"""
    cur = conn.cursor()
    cur.execute('''
        SELECT DISTINCT month 
        FROM tourism_data 
        WHERE month IS NOT NULL AND month > 0
        ORDER BY month
    ''')
    months = [row[0] for row in cur.fetchall()]
    return months

def print_monthly_summary(conn):
    """月別サマリー表示"""
    print("\n" + "="*60)
    print("📅 月別データサマリー")
    print("="*60)
    
    cur = conn.cursor()
    placeholders = ','.join('?' * len(EXCLUDE_CATEGORIES))
    
    cur.execute(f'''
        SELECT 
            month,
            COUNT(*) as records,
            COUNT(DISTINCT prefecture) as prefectures,
            COUNT(DISTINCT nationality) as nationalities,
            SUM(value) as total_guests
        FROM tourism_data
        WHERE nationality NOT IN ({placeholders}) AND month IS NOT NULL
        GROUP BY month
        ORDER BY month
    ''', EXCLUDE_CATEGORIES)
    
    data = cur.fetchall()
    
    print(f"\n{'月':>4} {'レコード数':>12} {'都道府県':>8} {'国籍数':>8} {'総宿泊者数':>15}")
    print("-" * 60)
    
    for row in data:
        month = row[0]
        month_label = f"{month}月" if month > 0 else "年計"
        print(f"{month_label:>4} {row[1]:>12,} {row[2]:>8,} {row[3]:>8,} {row[4]:>15,}")

def plot_monthly_trend(conn):
    """月別推移グラフ"""
    print("\n" + "="*60)
    print("📊 月別推移分析")
    print("="*60)
    
    cur = conn.cursor()
    placeholders = ','.join('?' * len(EXCLUDE_CATEGORIES))
    
    cur.execute(f'''
        SELECT month, SUM(value) as total
        FROM tourism_data
        WHERE nationality NOT IN ({placeholders}) 
              AND month IS NOT NULL 
              AND month > 0
        GROUP BY month
        ORDER BY month
    ''', EXCLUDE_CATEGORIES)
    
    data = cur.fetchall()
    months = [f"{row[0]}月" for row in data]
    guests = [row[1] for row in data]
    
    # データ表示
    print(f"\n【月別外国人宿泊者数推移】")
    for month, guest in zip(months, guests):
        print(f"  {month:>4}: {guest:15,} 人泊")
    
    # グラフ作成
    fig, ax = plt.subplots(figsize=(14, 6))
    ax.plot(months, guests, marker='o', linewidth=2, markersize=8, color='steelblue')
    ax.fill_between(range(len(months)), guests, alpha=0.3, color='steelblue')
    
    ax.set_xlabel('月', fontsize=12)
    ax.set_ylabel('宿泊者数（人泊）', fontsize=12)
    ax.set_title('月別外国人宿泊者数推移', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    
    # 数値ラベル追加
    for i, (x, y) in enumerate(zip(months, guests)):
        ax.text(i, y, f'{y:,.0f}', ha='center', va='bottom', fontsize=9)
    
    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.savefig('output_monthly_trend.png', dpi=150, bbox_inches='tight')
    plt.close()  # ★ 画像を閉じる
    print("\n💾 保存: output_monthly_trend.png")

def analyze_monthly_prefecture_ranking(conn, target_month=None):
    """特定月の都道府県別ランキング"""
    
    if target_month is None:
        # 最新月を取得
        cur = conn.cursor()
        cur.execute('SELECT MAX(month) FROM tourism_data WHERE month > 0')
        target_month = cur.fetchone()[0]
    
    print("\n" + "="*60)
    print(f"📊 {target_month}月の都道府県別ランキング")
    print("="*60)
    
    cur = conn.cursor()
    placeholders = ','.join('?' * len(EXCLUDE_CATEGORIES))
    
    params = EXCLUDE_CATEGORIES + [target_month]
    cur.execute(f'''
        SELECT prefecture, SUM(value) as total
        FROM tourism_data
        WHERE nationality NOT IN ({placeholders})
              AND month = ?
        GROUP BY prefecture
        ORDER BY total DESC
        LIMIT 20
    ''', params)
    
    data = cur.fetchall()
    
    prefectures = [row[0] for row in data]
    guests = [row[1] for row in data]
    
    # データ表示
    print(f"\n【{target_month}月 都道府県別トップ20】")
    total_all = sum(guests)
    for i, (pref, guest) in enumerate(data, 1):
        percentage = (guest / total_all) * 100
        print(f"  {i:2d}. {pref:10s} {guest:15,} 人泊 ({percentage:5.2f}%)")
    
    # グラフ作成（トップ10）
    fig, ax = plt.subplots(figsize=(12, 6))
    bars = ax.barh(prefectures[:10], guests[:10], color='coral')
    ax.set_xlabel('宿泊者数（人泊）', fontsize=12)
    ax.set_title(f'{target_month}月 都道府県別外国人宿泊者数 トップ10', fontsize=14, fontweight='bold')
    ax.invert_yaxis()
    
    # 数値ラベル追加
    for i, (bar, value) in enumerate(zip(bars, guests[:10])):
        ax.text(value, i, f' {value:,.0f}', va='center', fontsize=10)
    
    plt.tight_layout()
    plt.savefig(f'output_month{target_month}_prefectures.png', dpi=150, bbox_inches='tight')
    plt.close()  # ★ 画像を閉じる
    print(f"\n💾 保存: output_month{target_month}_prefectures.png")

def analyze_all_months_prefecture_ranking(conn):
    """全月の都道府県別ランキング比較"""
    print("\n" + "="*60)
    print("📊 月別都道府県ランキング推移")
    print("="*60)
    
    months = get_available_months(conn)
    
    cur = conn.cursor()
    placeholders = ','.join('?' * len(EXCLUDE_CATEGORIES))
    
    # 各月トップ5を取得
    print(f"\n【各月のトップ5都道府県】")
    
    all_month_data = {}
    
    for month in months:
        params = EXCLUDE_CATEGORIES + [month]
        cur.execute(f'''
            SELECT prefecture, SUM(value) as total
            FROM tourism_data
            WHERE nationality NOT IN ({placeholders})
                  AND month = ?
            GROUP BY prefecture
            ORDER BY total DESC
            LIMIT 5
        ''', params)
        
        data = cur.fetchall()
        all_month_data[month] = data
        
        print(f"\n  {month}月:")
        for i, (pref, guest) in enumerate(data, 1):
            print(f"    {i}. {pref:10s} {guest:12,} 人泊")
    
    # ヒートマップ用データ作成（トップ10都道府県 × 全月）
    print(f"\n【月別×都道府県 ヒートマップ作成中...】")
    
    df_list = []
    for month in months:
        params = EXCLUDE_CATEGORIES + [month]
        query = f'''
            SELECT prefecture, SUM(value) as total
            FROM tourism_data
            WHERE nationality NOT IN ({placeholders})
                  AND month = ?
            GROUP BY prefecture
        '''
        df_month = pd.read_sql_query(query, conn, params=params)
        df_month['month'] = month
        df_list.append(df_month)
    
    df = pd.concat(df_list, ignore_index=True)
    pivot = df.pivot(index='prefecture', columns='month', values='total').fillna(0)
    
    # トップ15都道府県に絞る
    top_prefectures = pivot.sum(axis=1).nlargest(15).index
    pivot_filtered = pivot.loc[top_prefectures]
    
    # ヒートマップ作成
    fig, ax = plt.subplots(figsize=(14, 10))
    sns.heatmap(
        pivot_filtered,
        annot=True,
        fmt='.0f',
        cmap='YlOrRd',
        cbar_kws={'label': '宿泊者数（人泊）'},
        linewidths=0.5,
        ax=ax
    )
    
    ax.set_title('月別×都道府県 外国人宿泊者数ヒートマップ（トップ15）', fontsize=14, fontweight='bold', pad=20)
    ax.set_xlabel('月', fontsize=12)
    ax.set_ylabel('都道府県', fontsize=12)
    
    # x軸ラベルを「1月」形式に
    ax.set_xticklabels([f'{int(m)}月' for m in pivot_filtered.columns])
    
    plt.tight_layout()
    plt.savefig('output_monthly_prefecture_heatmap.png', dpi=150, bbox_inches='tight')
    plt.close()  # ★ 画像を閉じる
    print("\n💾 保存: output_monthly_prefecture_heatmap.png")

def analyze_monthly_nationality_ranking(conn, target_month=None):
    """特定月の国籍別ランキング"""
    
    if target_month is None:
        # 最新月を取得
        cur = conn.cursor()
        cur.execute('SELECT MAX(month) FROM tourism_data WHERE month > 0')
        target_month = cur.fetchone()[0]
    
    print("\n" + "="*60)
    print(f"📊 {target_month}月の国籍別ランキング")
    print("="*60)
    
    cur = conn.cursor()
    placeholders = ','.join('?' * len(EXCLUDE_CATEGORIES))
    
    params = EXCLUDE_CATEGORIES + [target_month]
    cur.execute(f'''
        SELECT nationality, SUM(value) as total
        FROM tourism_data
        WHERE nationality NOT IN ({placeholders})
              AND month = ?
        GROUP BY nationality
        ORDER BY total DESC
        LIMIT 15
    ''', params)
    
    data = cur.fetchall()
    
    nationalities = [row[0] for row in data]
    guests = [row[1] for row in data]
    
    # データ表示
    print(f"\n【{target_month}月 国籍別トップ15】")
    total_all = sum(guests)
    for i, (nat, guest) in enumerate(data, 1):
        percentage = (guest / total_all) * 100
        print(f"  {i:2d}. {nat:15s} {guest:15,} 人泊 ({percentage:5.2f}%)")
    
    # グラフ作成（トップ10）
    fig, ax = plt.subplots(figsize=(12, 6))
    bars = ax.barh(nationalities[:10], guests[:10], color='seagreen')
    ax.set_xlabel('宿泊者数（人泊）', fontsize=12)
    ax.set_title(f'{target_month}月 国籍別外国人宿泊者数 トップ10', fontsize=14, fontweight='bold')
    ax.invert_yaxis()
    
    # 数値ラベル追加
    for i, (bar, value) in enumerate(zip(bars, guests[:10])):
        ax.text(value, i, f' {value:,.0f}', va='center', fontsize=10)
    
    plt.tight_layout()
    plt.savefig(f'output_month{target_month}_nationalities.png', dpi=150, bbox_inches='tight')
    plt.close()  # ★ 画像を閉じる
    print(f"\n💾 保存: output_month{target_month}_nationalities.png")

def compare_months_prefecture(conn, pref_name):
    """特定都道府県の月別推移"""
    print("\n" + "="*60)
    print(f"📊 {pref_name}の月別推移")
    print("="*60)
    
    cur = conn.cursor()
    placeholders = ','.join('?' * len(EXCLUDE_CATEGORIES))
    
    params = EXCLUDE_CATEGORIES + [pref_name]
    cur.execute(f'''
        SELECT month, SUM(value) as total
        FROM tourism_data
        WHERE nationality NOT IN ({placeholders})
              AND prefecture = ?
              AND month > 0
        GROUP BY month
        ORDER BY month
    ''', params)
    
    data = cur.fetchall()
    
    if not data:
        print(f"⚠️ {pref_name}のデータが見つかりません")
        return
    
    months = [f"{row[0]}月" for row in data]
    guests = [row[1] for row in data]
    
    # データ表示
    print(f"\n【{pref_name} 月別外国人宿泊者数】")
    for month, guest in zip(months, guests):
        print(f"  {month:>4}: {guest:15,} 人泊")
    
    # グラフ作成
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(months, guests, marker='o', linewidth=2, markersize=8, color='purple')
    ax.fill_between(range(len(months)), guests, alpha=0.3, color='purple')
    
    ax.set_xlabel('月', fontsize=12)
    ax.set_ylabel('宿泊者数（人泊）', fontsize=12)
    ax.set_title(f'{pref_name} 月別外国人宿泊者数推移', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    
    # 数値ラベル追加
    for i, (x, y) in enumerate(zip(months, guests)):
        ax.text(i, y, f'{y:,.0f}', ha='center', va='bottom', fontsize=9)
    
    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.savefig(f'output_{pref_name}_monthly_trend.png', dpi=150, bbox_inches='tight')
    plt.close()  # ★ 画像を閉じる
    print(f"\n💾 保存: output_{pref_name}_monthly_trend.png")

def main():
    print("\n" + "="*60)
    print("🔍 観光データ月別分析開始")
    print("="*60)
    
    conn = connect_db()
    
    # 1. 月別サマリー
    print_monthly_summary(conn)
    
    # 2. 月別推移グラフ
    plot_monthly_trend(conn)
    
    # 3. 全月の都道府県ランキング比較
    analyze_all_months_prefecture_ranking(conn)
    
    # 4. 最新月の都道府県ランキング
    analyze_monthly_prefecture_ranking(conn)
    
    # 5. 最新月の国籍別ランキング
    analyze_monthly_nationality_ranking(conn)
    
    # 6. 特定都道府県の月別推移（例: 東京都）
    compare_months_prefecture(conn, '東京都')
    compare_months_prefecture(conn, '北海道')
    compare_months_prefecture(conn, '沖縄県')
    
    conn.close()
    
    print("\n" + "="*60)
    print("✅ 分析完了")
    print("="*60)
    print("\n📊 生成されたファイル:")
    print("  - output_monthly_trend.png")
    print("  - output_monthly_prefecture_heatmap.png")
    print("  - output_month{N}_prefectures.png")
    print("  - output_month{N}_nationalities.png")
    print("  - output_{都道府県名}_monthly_trend.png")

if __name__ == '__main__':
    main()