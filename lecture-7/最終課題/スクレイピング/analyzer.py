"""
月別観光データ分析ツール + 仮説検証
"""

import sqlite3
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
import japanize_matplotlib
from pathlib import Path
import warnings

warnings.filterwarnings('ignore')

# 除外する集計カテゴリ
EXCLUDE_CATEGORIES = ['実宿泊者', '総数', '外国人']

def connect_db():
    """データベース接続"""
    script_dir = Path(__file__).parent
    db_path = script_dir / 'tourism_data.db'
    
    if not db_path.exists():
        print(f"❌ エラー: {db_path} が見つかりません")
        exit(1)
    
    conn = sqlite3.connect(str(db_path))
    
    # データ数確認
    placeholders = ','.join('?' * len(EXCLUDE_CATEGORIES))
    cursor = conn.execute(
        f'SELECT COUNT(DISTINCT month) FROM tourism_data WHERE nationality NOT IN ({placeholders})', 
        EXCLUDE_CATEGORIES
    )
    month_count = cursor.fetchone()[0]
    
    print(f"📂 DB ファイルパス: {db_path}")
    print(f"✅ データベース接続成功: {month_count} 月分のデータ\n")
    
    return conn

def analyze_monthly_summary(conn):
    """月別データサマリー"""
    print("="*60)
    print("📅 月別データサマリー")
    print("="*60 + "\n")
    
    placeholders = ','.join('?' * len(EXCLUDE_CATEGORIES))
    query = f'''
        SELECT 
            CASE 
                WHEN month = 0 THEN '年計'
                ELSE printf('%2d月', month)
            END as month_label,
            COUNT(DISTINCT prefecture) as pref_count,
            COUNT(DISTINCT nationality) as nat_count,
            SUM(value) as total_stays
        FROM tourism_data
        WHERE nationality NOT IN ({placeholders})
        GROUP BY month
        ORDER BY month
    '''
    
    df = pd.read_sql(query, conn, params=EXCLUDE_CATEGORIES)
    
    print(f"{'月':^8} {'レコード数':>10} {'都道府県':>8} {'国籍数':>8} {'総宿泊者数':>18}")
    print("-" * 60)
    
    for _, row in df.iterrows():
        print(f"{row['month_label']:^8} {row['pref_count']*row['nat_count']:>10} "
              f"{row['pref_count']:>8} {row['nat_count']:>8} {row['total_stays']:>18,}")

def analyze_monthly_trend(conn):
    """月別推移分析"""
    print("\n" + "="*60)
    print("📊 月別推移分析")
    print("="*60 + "\n")
    
    placeholders = ','.join('?' * len(EXCLUDE_CATEGORIES))
    query = f'''
        SELECT month, SUM(value) as total
        FROM tourism_data
        WHERE nationality NOT IN ({placeholders}) AND month > 0
        GROUP BY month
        ORDER BY month
    '''
    
    df = pd.read_sql(query, conn, params=EXCLUDE_CATEGORIES)
    
    print("【月別外国人宿泊者数推移】")
    for _, row in df.iterrows():
        print(f"  {int(row['month']):>3}月: {row['total']:>14,} 人泊")
    
    # グラフ作成
    fig, ax = plt.subplots(figsize=(12, 6))
    
    months = [f"{int(m)}月" for m in df['month']]
    values = df['total'].values
    
    colors = ['#FF6B6B' if v == max(values) else '#4ECDC4' if v == min(values) else '#95E1D3' 
              for v in values]
    
    bars = ax.bar(months, values, color=colors, edgecolor='black', linewidth=0.7)
    
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height/10000)}万',
                ha='center', va='bottom', fontsize=9)
    
    ax.set_xlabel('月', fontsize=12)
    ax.set_ylabel('宿泊者数（人泊）', fontsize=12)
    ax.set_title('月別外国人宿泊者数推移', fontsize=14, fontweight='bold', pad=20)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{int(x/1000000)}M'))
    ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('output_monthly_trend.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    print("\n💾 保存: output_monthly_trend.png")

def analyze_monthly_prefecture_ranking(conn):
    """月別都道府県ランキング推移"""
    print("\n" + "="*60)
    print("📊 月別都道府県ランキング推移")
    print("="*60 + "\n")
    
    print("【各月のトップ5都道府県】\n")
    
    placeholders = ','.join('?' * len(EXCLUDE_CATEGORIES))
    
    # 月ごとのトップ5
    for month in range(1, 13):
        params = EXCLUDE_CATEGORIES + [month]
        query = f'''
            SELECT prefecture, SUM(value) as total
            FROM tourism_data
            WHERE nationality NOT IN ({placeholders}) AND month = ?
            GROUP BY prefecture
            ORDER BY total DESC
            LIMIT 5
        '''
        df = pd.read_sql(query, conn, params=params)
        
        print(f"  {month}月:")
        for i, row in enumerate(df.itertuples(), 1):
            print(f"    {i}. {row.prefecture:<10} {row.total:>14,} 人泊")
        print()
    
    # ヒートマップ作成
    print("【月別×都道府県 ヒートマップ作成中...】\n")
    
    query = f'''
        SELECT month, prefecture, SUM(value) as total
        FROM tourism_data
        WHERE nationality NOT IN ({placeholders}) AND month > 0
        GROUP BY month, prefecture
    '''
    df = pd.read_sql(query, conn, params=EXCLUDE_CATEGORIES)
    
    # トップ15都道府県を抽出
    top_prefs = df.groupby('prefecture')['total'].sum().nlargest(15).index
    df_filtered = df[df['prefecture'].isin(top_prefs)]
    
    # ピボットテーブル作成
    pivot = df_filtered.pivot(index='prefecture', columns='month', values='total')
    pivot = pivot.div(1000000)  # 百万人泊単位
    
    # ヒートマップ
    fig, ax = plt.subplots(figsize=(14, 8))
    sns.heatmap(pivot, annot=True, fmt='.1f', cmap='YlOrRd', 
                linewidths=0.5, cbar_kws={'label': '宿泊者数（百万人泊）'})
    
    ax.set_xlabel('月', fontsize=12)
    ax.set_ylabel('都道府県', fontsize=12)
    ax.set_title('月別×都道府県 宿泊者数ヒートマップ (トップ15)', 
                 fontsize=13, fontweight='bold', pad=15)
    
    plt.tight_layout()
    plt.savefig('output_monthly_prefecture_heatmap.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    print("💾 保存: output_monthly_prefecture_heatmap.png")

def analyze_specific_month(conn, target_month=12):
    """特定月の詳細分析"""
    print("\n" + "="*60)
    print(f"📊 {target_month}月の都道府県別ランキング")
    print("="*60 + "\n")
    
    placeholders = ','.join('?' * len(EXCLUDE_CATEGORIES))
    params = EXCLUDE_CATEGORIES + [target_month]
    
    query = f'''
        SELECT prefecture, SUM(value) as total
        FROM tourism_data
        WHERE nationality NOT IN ({placeholders}) AND month = ?
        GROUP BY prefecture
        ORDER BY total DESC
        LIMIT 20
    '''
    
    df = pd.read_sql(query, conn, params=params)
    total_sum = df['total'].sum()
    df['share'] = df['total'] / total_sum * 100
    
    print(f"【{target_month}月 都道府県別トップ20】")
    for i, row in enumerate(df.itertuples(), 1):
        print(f"  {i:>2}. {row.prefecture:<10} {row.total:>18,} 人泊 ({row.share:>5.2f}%)")
    
    # グラフ作成
    fig, ax = plt.subplots(figsize=(12, 8))
    
    colors = plt.cm.RdYlGn_r(np.linspace(0.2, 0.8, len(df)))
    bars = ax.barh(df['prefecture'][::-1], df['total'][::-1], color=colors[::-1], 
                   edgecolor='black', linewidth=0.5)
    
    for i, bar in enumerate(bars):
        width = bar.get_width()
        ax.text(width, bar.get_y() + bar.get_height()/2,
                f'{int(width/10000)}万 ({df["share"].iloc[::-1].iloc[i]:.1f}%)',
                ha='left', va='center', fontsize=9, fontweight='bold')
    
    ax.set_xlabel('宿泊者数（人泊）', fontsize=12)
    ax.set_ylabel('都道府県', fontsize=12)
    ax.set_title(f'{target_month}月 都道府県別外国人宿泊者数ランキング', 
                 fontsize=13, fontweight='bold', pad=15)
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{int(x/1000000)}M'))
    
    plt.tight_layout()
    plt.savefig(f'output_month{target_month}_prefectures.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"\n💾 保存: output_month{target_month}_prefectures.png")
    
    # 国籍別ランキング
    print("\n" + "="*60)
    print(f"📊 {target_month}月の国籍別ランキング")
    print("="*60 + "\n")
    
    query = f'''
        SELECT nationality, SUM(value) as total
        FROM tourism_data
        WHERE nationality NOT IN ({placeholders}) AND month = ?
        GROUP BY nationality
        ORDER BY total DESC
    '''
    
    df_nat = pd.read_sql(query, conn, params=params)
    total_sum_nat = df_nat['total'].sum()
    df_nat['share'] = df_nat['total'] / total_sum_nat * 100
    
    print(f"【{target_month}月 国籍別トップ15】")
    for i, row in enumerate(df_nat.itertuples(), 1):
        print(f"  {i:>2}. {row.nationality:<15} {row.total:>18,} 人泊 ({row.share:>5.2f}%)")
    
    # グラフ作成
    fig, ax = plt.subplots(figsize=(10, 8))
    
    colors_nat = plt.cm.Spectral(np.linspace(0, 1, len(df_nat)))
    bars = ax.barh(df_nat['nationality'][::-1], df_nat['total'][::-1], 
                   color=colors_nat[::-1], edgecolor='black', linewidth=0.5)
    
    for i, bar in enumerate(bars):
        width = bar.get_width()
        ax.text(width, bar.get_y() + bar.get_height()/2,
                f'{int(width/10000)}万 ({df_nat["share"].iloc[::-1].iloc[i]:.1f}%)',
                ha='left', va='center', fontsize=9, fontweight='bold')
    
    ax.set_xlabel('宿泊者数（人泊）', fontsize=12)
    ax.set_ylabel('国籍', fontsize=12)
    ax.set_title(f'{target_month}月 国籍別外国人宿泊者数ランキング', 
                 fontsize=13, fontweight='bold', pad=15)
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{int(x/1000000)}M'))
    
    plt.tight_layout()
    plt.savefig(f'output_month{target_month}_nationalities.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"\n💾 保存: output_month{target_month}_nationalities.png")

def analyze_prefecture_trend(conn, prefecture):
    """都道府県別の月別推移"""
    print("\n" + "="*60)
    print(f"📊 {prefecture}の月別推移")
    print("="*60 + "\n")
    
    placeholders = ','.join('?' * len(EXCLUDE_CATEGORIES))
    params = EXCLUDE_CATEGORIES + [prefecture]
    
    query = f'''
        SELECT month, SUM(value) as total
        FROM tourism_data
        WHERE nationality NOT IN ({placeholders}) AND prefecture = ? AND month > 0
        GROUP BY month
        ORDER BY month
    '''
    
    df = pd.read_sql(query, conn, params=params)
    
    print(f"【{prefecture} 月別外国人宿泊者数】")
    for _, row in df.iterrows():
        print(f"  {int(row['month']):>3}月: {row['total']:>14,} 人泊")
    
    # グラフ作成
    fig, ax = plt.subplots(figsize=(12, 6))
    
    months = [f"{int(m)}月" for m in df['month']]
    values = df['total'].values
    
    ax.plot(months, values, marker='o', linewidth=2.5, markersize=8, 
            color='#3498db', markerfacecolor='#e74c3c')
    ax.fill_between(range(len(months)), values, alpha=0.3, color='#3498db')
    
    for i, v in enumerate(values):
        ax.text(i, v, f'{int(v/10000)}万', ha='center', va='bottom', fontsize=9)
    
    ax.set_xlabel('月', fontsize=12)
    ax.set_ylabel('宿泊者数（人泊）', fontsize=12)
    ax.set_title(f'{prefecture} 月別外国人宿泊者数推移', fontsize=14, fontweight='bold', pad=20)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{int(x/1000000)}M'))
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f'output_{prefecture}_monthly_trend.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"\n💾 保存: output_{prefecture}_monthly_trend.png")


# ==========================================
# 仮説1: 季節変動と地域特性の相関分析
# ==========================================

def hypothesis1_seasonal_correlation(conn):
    """仮説1: 北海道と沖縄の季節相関分析"""
    
    print("\n" + "="*70)
    print("🔬 仮説1: 季節変動と地域特性の相関分析")
    print("="*70)
    
    # データ取得
    placeholders = ','.join('?' * len(EXCLUDE_CATEGORIES))
    query = f'''
        SELECT month, 
               SUM(CASE WHEN prefecture='北海道' THEN value ELSE 0 END) as hokkaido,
               SUM(CASE WHEN prefecture='沖縄県' THEN value ELSE 0 END) as okinawa,
               SUM(CASE WHEN prefecture='東京都' THEN value ELSE 0 END) as tokyo
        FROM tourism_data
        WHERE nationality NOT IN ({placeholders}) AND month > 0
        GROUP BY month
        ORDER BY month
    '''
    df = pd.read_sql(query, conn, params=EXCLUDE_CATEGORIES)
    
    # 相関係数計算
    corr_hokkaido_okinawa = df['hokkaido'].corr(df['okinawa'])
    corr_tokyo_hokkaido = df['tokyo'].corr(df['hokkaido'])
    corr_tokyo_okinawa = df['tokyo'].corr(df['okinawa'])
    
    print(f"\n【地域間の季節相関係数】")
    print(f"  北海道 ⇔ 沖縄県: {corr_hokkaido_okinawa:6.3f} {'(逆相関)' if corr_hokkaido_okinawa < 0 else '(正相関)'}")
    print(f"  東京都 ⇔ 北海道: {corr_tokyo_hokkaido:6.3f}")
    print(f"  東京都 ⇔ 沖縄県: {corr_tokyo_okinawa:6.3f}")
    
    # 変動係数(CV)計算
    cv_hokkaido = df['hokkaido'].std() / df['hokkaido'].mean()
    cv_okinawa = df['okinawa'].std() / df['okinawa'].mean()
    cv_tokyo = df['tokyo'].std() / df['tokyo'].mean()
    
    print(f"\n【季節変動リスク (変動係数)】")
    print(f"  北海道: {cv_hokkaido:.3f} (最大/最小比: {df['hokkaido'].max()/df['hokkaido'].min():.2f}倍)")
    print(f"  沖縄県: {cv_okinawa:.3f} (最大/最小比: {df['okinawa'].max()/df['okinawa'].min():.2f}倍)")
    print(f"  東京都: {cv_tokyo:.3f} (最大/最小比: {df['tokyo'].max()/df['tokyo'].min():.2f}倍)")
    
    # 統計的検定
    from scipy.stats import pearsonr
    r, p_value = pearsonr(df['hokkaido'], df['okinawa'])
    print(f"\n【統計的有意性】")
    print(f"  p値: {p_value:.4f} {'(有意)' if p_value < 0.05 else '(非有意)'}")
    
    # グラフ1: 散布図
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    # 北海道 vs 沖縄
    axes[0].scatter(df['hokkaido'], df['okinawa'], s=100, alpha=0.6, c=df['month'], cmap='coolwarm')
    axes[0].plot(df['hokkaido'], np.poly1d(np.polyfit(df['hokkaido'], df['okinawa'], 1))(df['hokkaido']), 
                 'r--', linewidth=2, label=f'r={corr_hokkaido_okinawa:.3f}')
    axes[0].set_xlabel('北海道 宿泊数（人泊）', fontsize=11)
    axes[0].set_ylabel('沖縄県 宿泊数（人泊）', fontsize=11)
    axes[0].set_title('仮説1: 北海道と沖縄の季節相関', fontsize=12, fontweight='bold')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)
    
    # 月別ラベル追加
    for i, row in df.iterrows():
        axes[0].annotate(f"{int(row['month'])}月", (row['hokkaido'], row['okinawa']), 
                        fontsize=8, alpha=0.7)
    
    # 東京 vs 北海道
    axes[1].scatter(df['tokyo'], df['hokkaido'], s=100, alpha=0.6, c=df['month'], cmap='viridis')
    axes[1].plot(df['tokyo'], np.poly1d(np.polyfit(df['tokyo'], df['hokkaido'], 1))(df['tokyo']), 
                 'b--', linewidth=2, label=f'r={corr_tokyo_hokkaido:.3f}')
    axes[1].set_xlabel('東京都 宿泊数（人泊）', fontsize=11)
    axes[1].set_ylabel('北海道 宿泊数（人泊）', fontsize=11)
    axes[1].set_title('東京都と北海道の季節相関', fontsize=12, fontweight='bold')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('hypothesis1_seasonal_correlation.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("\n💾 保存: hypothesis1_seasonal_correlation.png")
    
    # グラフ2: 月別推移比較（標準化）
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # 標準化（平均0、標準偏差1）
    df['hokkaido_std'] = (df['hokkaido'] - df['hokkaido'].mean()) / df['hokkaido'].std()
    df['okinawa_std'] = (df['okinawa'] - df['okinawa'].mean()) / df['okinawa'].std()
    df['tokyo_std'] = (df['tokyo'] - df['tokyo'].mean()) / df['tokyo'].std()
    
    months_label = [f"{int(m)}月" for m in df['month']]
    
    ax.plot(months_label, df['hokkaido_std'], marker='o', linewidth=2, label='北海道', color='blue')
    ax.plot(months_label, df['okinawa_std'], marker='s', linewidth=2, label='沖縄県', color='coral')
    ax.plot(months_label, df['tokyo_std'], marker='^', linewidth=2, label='東京都', color='green')
    
    ax.axhline(0, color='gray', linestyle='--', linewidth=1, alpha=0.5)
    ax.set_xlabel('月', fontsize=12)
    ax.set_ylabel('標準化宿泊数（平均0, SD=1）', fontsize=12)
    ax.set_title('標準化した月別宿泊数推移 - 季節パターンの比較', fontsize=13, fontweight='bold')
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('hypothesis1_standardized_trend.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("💾 保存: hypothesis1_standardized_trend.png")
    
    # 結論
    print("\n【仮説1の検証結果】")
    if corr_hokkaido_okinawa < -0.3:
        print("✅ 仮説支持: 北海道と沖縄は明確な逆相関（補完関係）を示す")
        print("   → 「冬の北海道、夏の沖縄」という季節補完型観光戦略が有効")
    elif corr_hokkaido_okinawa < 0:
        print("⚠️ 弱い逆相関: 一部の月で補完関係が見られる")
    else:
        print("❌ 仮説不支持: 逆相関は確認できず")
    
    print(f"\n   北海道の変動リスクは東京都の{cv_hokkaido/cv_tokyo:.2f}倍")
    print(f"   → 北海道は気候変動・雪不足リスクに特に脆弱")


# ==========================================
# 仮説2: 国籍別の地域選好パターン分析
# ==========================================

def hypothesis2_nationality_preference(conn):
    """仮説2: 国籍別の地域分散度分析"""
    
    print("\n" + "="*70)
    print("🔬 仮説2: 国籍別の地域選好パターン分析")
    print("="*70)
    
    placeholders = ','.join('?' * len(EXCLUDE_CATEGORIES))
    
    # 分析対象国籍
    target_nationalities = ['中国', '韓国', '台湾', '米国', 'オーストラリア', '英国']
    
    results = []
    
    for nationality in target_nationalities:
        params = EXCLUDE_CATEGORIES + [nationality]
        query = f'''
            SELECT prefecture, SUM(value) as total
            FROM tourism_data
            WHERE nationality NOT IN ({placeholders})
                  AND nationality = ?
                  AND month > 0
            GROUP BY prefecture
            ORDER BY total DESC
        '''
        df = pd.read_sql(query, conn, params=params)
        
        # シェア計算
        df['share'] = df['total'] / df['total'].sum()
        
        # ハーフィンダール指数 (HHI): 0に近い=分散、1に近い=集中
        hhi = (df['share'] ** 2).sum()
        
        # ゴールデンルート(東京・大阪・京都)依存度
        golden_route_share = df[df['prefecture'].isin(['東京都', '大阪府', '京都府'])]['share'].sum()
        
        # トップ5のシェア
        top5_share = df.head(5)['share'].sum()
        
        results.append({
            'nationality': nationality,
            'hhi': hhi,
            'golden_route_share': golden_route_share,
            'top5_share': top5_share,
            'top1': df.iloc[0]['prefecture'],
            'top1_share': df.iloc[0]['share']
        })
    
    results_df = pd.DataFrame(results)
    
    # 結果表示
    print(f"\n【国籍別の地域集中度】")
    print(f"{'国籍':<15} {'HHI':>8} {'GR依存度':>10} {'Top5依存度':>12} {'最多訪問地':<10} {'シェア':>8}")
    print("-" * 70)
    
    for _, row in results_df.iterrows():
        print(f"{row['nationality']:<15} {row['hhi']:>8.3f} {row['golden_route_share']:>9.1%} "
              f"{row['top5_share']:>11.1%} {row['top1']:<10} {row['top1_share']:>7.1%}")
    
    print("\n【指標の解釈】")
    print("  HHI (ハーフィンダール指数): 地域集中度 (低い=分散的, 高い=集中的)")
    print("  GR依存度: ゴールデンルート(東京・大阪・京都)への依存度")
    print("  Top5依存度: 上位5都道府県への依存度")
    
    # グラフ1: HHI比較
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # HHI
    axes[0, 0].barh(results_df['nationality'], results_df['hhi'], 
                    color=['#E74C3C' if x > 0.15 else '#3498DB' for x in results_df['hhi']])
    axes[0, 0].set_xlabel('HHI (地域集中度)', fontsize=11)
    axes[0, 0].set_title('国籍別 地域集中度 (HHI)', fontsize=12, fontweight='bold')
    axes[0, 0].axvline(0.15, color='red', linestyle='--', linewidth=1, alpha=0.5, label='高集中の閾値')
    axes[0, 0].legend()
    axes[0, 0].grid(axis='x', alpha=0.3)
    
    # ゴールデンルート依存度
    axes[0, 1].barh(results_df['nationality'], results_df['golden_route_share'], 
                    color='#F39C12')
    axes[0, 1].set_xlabel('シェア', fontsize=11)
    axes[0, 1].set_title('ゴールデンルート依存度', fontsize=12, fontweight='bold')
    axes[0, 1].xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.0%}'))
    axes[0, 1].grid(axis='x', alpha=0.3)
    
    # Top5依存度
    axes[1, 0].barh(results_df['nationality'], results_df['top5_share'], 
                    color='#9B59B6')
    axes[1, 0].set_xlabel('シェア', fontsize=11)
    axes[1, 0].set_title('上位5都道府県依存度', fontsize=12, fontweight='bold')
    axes[1, 0].xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.0%}'))
    axes[1, 0].grid(axis='x', alpha=0.3)
    
    # 散布図: HHI vs ゴールデンルート依存度
    axes[1, 1].scatter(results_df['hhi'], results_df['golden_route_share'], 
                       s=200, alpha=0.6, c=range(len(results_df)), cmap='Set2')
    
    for _, row in results_df.iterrows():
        axes[1, 1].annotate(row['nationality'], 
                           (row['hhi'], row['golden_route_share']),
                           fontsize=9, ha='center', va='bottom')
    
    axes[1, 1].set_xlabel('HHI (地域集中度)', fontsize=11)
    axes[1, 1].set_ylabel('ゴールデンルート依存度', fontsize=11)
    axes[1, 1].set_title('集中度 vs GR依存度の関係', fontsize=12, fontweight='bold')
    axes[1, 1].yaxis.set_major_formatter(plt.FuncFormatter(lambda y, p: f'{y:.0%}'))
    axes[1, 1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('hypothesis2_nationality_concentration.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("\n💾 保存: hypothesis2_nationality_concentration.png")
    
    # グラフ2: 国籍別トップ10都道府県ヒートマップ
    fig, ax = plt.subplots(figsize=(14, 8))
    
    heatmap_data = []
    for nationality in target_nationalities:
        params = EXCLUDE_CATEGORIES + [nationality]
        query = f'''
            SELECT prefecture, SUM(value) as total
            FROM tourism_data
            WHERE nationality NOT IN ({placeholders})
                  AND nationality = ?
                  AND month > 0
            GROUP BY prefecture
            ORDER BY total DESC
            LIMIT 10
        '''
        df = pd.read_sql(query, conn, params=params)
        df['share'] = df['total'] / df['total'].sum() * 100
        
        # 国籍ごとのトップ10を辞書化
        pref_dict = dict(zip(df['prefecture'], df['share']))
        heatmap_data.append(pref_dict)
    
    # 全国籍のトップ10都道府県リストを作成
    all_prefs = set()
    for data in heatmap_data:
        all_prefs.update(data.keys())
    all_prefs = sorted(all_prefs, key=lambda x: sum(d.get(x, 0) for d in heatmap_data), reverse=True)[:15]
    
    # マトリックス作成
    matrix = []
    for data in heatmap_data:
        matrix.append([data.get(pref, 0) for pref in all_prefs])
    
    sns.heatmap(matrix, annot=True, fmt='.1f', cmap='YlOrRd',
                xticklabels=all_prefs, yticklabels=target_nationalities,
                linewidths=0.5, cbar_kws={'label': 'シェア (%)'})
    
    ax.set_title('国籍別 都道府県選好パターン（上位15地域）', fontsize=13, fontweight='bold', pad=15)
    ax.set_xlabel('都道府県', fontsize=11)
    ax.set_ylabel('国籍', fontsize=11)
    
    plt.tight_layout()
    plt.savefig('hypothesis2_nationality_preference_heatmap.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("💾 保存: hypothesis2_nationality_preference_heatmap.png")
    
    # 結論
    print("\n【仮説2の検証結果】")
    
    asia_hhi = results_df[results_df['nationality'].isin(['中国', '韓国', '台湾'])]['hhi'].mean()
    western_hhi = results_df[results_df['nationality'].isin(['米国', 'オーストラリア', '英国'])]['hhi'].mean()
    
    print(f"\n  アジア圏平均HHI: {asia_hhi:.3f}")
    print(f"  欧米圏平均HHI: {western_hhi:.3f}")
    print(f"  差: {(western_hhi - asia_hhi):.3f}")
    
    if western_hhi < asia_hhi:
        print("\n✅ 仮説支持: 欧米圏は地方分散度が高い")
        print("   → 地方創生には欧米客誘致が効果的")
    else:
        print("\n❌ 仮説不支持: アジア圏の方が分散的")
    
    # 追加分析: 韓国の特徴
    korea_gr = results_df[results_df['nationality'] == '韓国']['golden_route_share'].values[0]
    print(f"\n【特記事項】")
    print(f"  韓国のGR依存度: {korea_gr:.1%}")
    print(f"  → {'地方分散型' if korea_gr < 0.5 else 'GR集中型'}")


def main():
    """メイン処理"""
    conn = connect_db()
    
    try:
        # 既存分析
        analyze_monthly_summary(conn)
        analyze_monthly_trend(conn)
        analyze_monthly_prefecture_ranking(conn)
        analyze_specific_month(conn, 12)
        
        # 個別都道府県
        analyze_prefecture_trend(conn, '東京都')
        analyze_prefecture_trend(conn, '北海道')
        analyze_prefecture_trend(conn, '沖縄県')
        
        # 仮説検証
        hypothesis1_seasonal_correlation(conn)
        hypothesis2_nationality_preference(conn)
        
        print("\n" + "="*60)
        print("✅ 全分析完了")
        print("="*60)
        
    finally:
        conn.close()

if __name__ == '__main__':
    main()