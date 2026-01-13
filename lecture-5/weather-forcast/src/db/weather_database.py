"""
天気予報データベース管理モジュール
SQLiteを使用してデータの永続化を実現
"""

import os
import sqlite3
import json
from datetime import datetime


class WeatherDatabase:
    """
    天気予報データの保存と取得を担当するクラス
    """
    
    def __init__(self, db_path='weather.db'):
        """
        データベース接続の初期化
        
        Args:
            db_path: データベースファイルのパス
        """
        # データベースファイルのパスを設定
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.db_path = os.path.join(base_dir, 'data', db_path)
        
        # データディレクトリがなければ作成
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # データベース接続と初期化
        self.conn = None
        self.cursor = None
        self.connect()
        
        # テーブルを毎回削除して作り直す
        self.drop_tables()
        self.create_tables()
        
        print(f"WeatherDatabase初期化完了（パス: {self.db_path}）")
    
    
    def connect(self):
        """データベースに接続する"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
        except sqlite3.Error as e:
            print(f"データベース接続エラー: {e}")
    
    
    def close(self):
        """データベース接続を閉じる"""
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None
    
    
    def drop_tables(self):
        """既存のテーブルを全て削除する"""
        try:
            # 外部キー制約を一時的に無効化
            self.cursor.execute("PRAGMA foreign_keys = OFF")
            
            # 既存のテーブルを削除
            tables = ["forecasts", "report_info", "areas"]
            for table in tables:
                self.cursor.execute(f"DROP TABLE IF EXISTS {table}")
            
            # 外部キー制約を再度有効化
            self.cursor.execute("PRAGMA foreign_keys = ON")
            self.conn.commit()
            print("既存のテーブルを全て削除しました")
            
        except sqlite3.Error as e:
            print(f"テーブル削除エラー: {e}")
    
    
    def create_tables(self):
        """必要なテーブルを作成する"""
        try:
            # 地域マスターテーブル
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS areas (
                area_code TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                office_name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # 天気予報データテーブル - weather_codeカラムを含める
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS forecasts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                area_code TEXT NOT NULL,
                report_datetime TEXT NOT NULL,
                forecast_date TEXT NOT NULL,
                weather_code TEXT NOT NULL,
                weather TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (area_code) REFERENCES areas(area_code)
            )
            ''')
            
            # 予報公開情報テーブル
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS report_info (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                area_code TEXT NOT NULL,
                report_datetime TEXT NOT NULL,
                publishing_office TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (area_code) REFERENCES areas(area_code)
            )
            ''')
            
            self.conn.commit()
            print("データベーステーブルを作成しました")
            
        except sqlite3.Error as e:
            print(f"テーブル作成エラー: {e}")
    
    
    def save_area_list(self, area_list):
        """
        地域リストをデータベースに保存
        
        Args:
            area_list: 地域情報を含む辞書
        
        Returns:
            保存された地域の数
        """
        try:
            if not area_list or 'offices' not in area_list:
                return 0
                
            offices = area_list['offices']
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            count = 0
            
            for code, info in offices.items():
                name = info.get('name', '')
                office_name = info.get('name', '')  # 同じ値を使用（APIの構造上）
                
                self.cursor.execute('''
                INSERT OR REPLACE INTO areas 
                (area_code, name, office_name, updated_at)
                VALUES (?, ?, ?, ?)
                ''', (code, name, office_name, now))
                count += 1
                
            self.conn.commit()
            print(f"✅ {count}件の地域情報をDBに保存しました")
            return count
        except sqlite3.Error as e:
            print(f"地域データ保存エラー: {e}")
            return 0
    
    
    def get_area_list(self):
        """
        データベースから地域リストを取得
        
        Returns:
            APIと同じ形式の地域リスト辞書
        """
        try:
            self.cursor.execute('SELECT area_code, name, office_name FROM areas ORDER BY name')
            rows = self.cursor.fetchall()
            
            result = {'offices': {}}
            for row in rows:
                # タプルからインデックスでデータを取得
                area_code = row[0]
                name = row[1]
                office_name = row[2]
                
                result['offices'][area_code] = {
                    'name': name,
                    'office_name': office_name
                }
            
            return result
        except sqlite3.Error as e:
            print(f"地域データ取得エラー: {e}")
            return {'offices': {}}  # エラー時は空の辞書を返す
    
    
    def save_weather_forecast(self, area_code, forecast_data):
        """
        天気予報データをデータベースに保存する
        
        Args:
            area_code: 地域コード
            forecast_data: 天気予報データ（API応答）
            
        Returns:
            bool: 保存が成功したかどうか
        """
        try:
            # デバッグ出力
            print(f"保存するデータの構造: {type(forecast_data)}")
            
            # レポート情報を取得
            report_datetime = forecast_data.get("reportDatetime")
            publishing_office = forecast_data.get("publishingOffice")
            
            if not report_datetime or not publishing_office:
                print("Error: レポート情報が見つかりません")
                return False
                
            print(f"レポート情報: {report_datetime}, {publishing_office}")
            
            # トランザクション開始
            self.conn.execute("BEGIN TRANSACTION")
            
            # レポート情報を保存
            self.cursor.execute('''
            INSERT OR REPLACE INTO report_info 
            (area_code, report_datetime, publishing_office)
            VALUES (?, ?, ?)
            ''', (area_code, report_datetime, publishing_office))
            
            # timeSeries配列（気象庁APIの形式に合わせる）
            time_series_list = forecast_data.get("timeSeries", [])
            
            if not time_series_list or len(time_series_list) == 0:
                print("Error: timeSeries 情報が見つかりません")
                return False
            
            # 0番目のtimeSeriesが天気予報のメインデータ
            time_series = time_series_list[0]
            time_defines = time_series.get("timeDefines", [])
            
            if not time_defines:
                print("Error: timeDefines 情報が見つかりません")
                return False
                
            print(f"予報日数: {len(time_defines)}")
            
            # 各地域の予報を処理
            for area_info in time_series.get("areas", []):
                area_name = area_info.get("area", {}).get("name")
                office_code = area_info.get("area", {}).get("code")
                
                if not area_name:
                    print(f"Warning: 地域名が見つかりません: {area_info}")
                    continue
                    
                # 地域情報を保存
                self.cursor.execute('''
                INSERT OR REPLACE INTO areas
                (area_code, name, office_name)
                VALUES (?, ?, ?)
                ''', (area_code, area_name, office_code or "不明"))
                
                print(f"地域情報を保存: area_code={area_code}, name={area_name}, office_code={office_code}")
                
                # 天気予報データを処理
                weather_codes = area_info.get("weatherCodes", [])
                weathers = area_info.get("weathers", [])
                
                if not weather_codes or not weathers:
                    print(f"Warning: 天気データが見つかりません: weatherCodes={weather_codes}, weathers={weathers}")
                    continue
                    
                print(f"天気コード数: {len(weather_codes)}, 天気テキスト数: {len(weathers)}")
                
                # 各日の予報を保存
                for i in range(min(len(time_defines), len(weather_codes), len(weathers))):
                    forecast_date = time_defines[i]
                    weather_code = weather_codes[i]
                    weather = weathers[i]
                    
                    print(f"予報データ: date={forecast_date}, code={weather_code}, weather={weather}")
                    
                    # 予報データを保存
                    self.cursor.execute('''
                    INSERT OR REPLACE INTO forecasts
                    (area_code, report_datetime, forecast_date, weather_code, weather)
                    VALUES (?, ?, ?, ?, ?)
                    ''', (area_code, report_datetime, forecast_date, weather_code, weather))
                    
                    print(f"保存完了: area_code={area_code}, date={forecast_date}, weather={weather}")
            
            # コミット
            self.conn.commit()
            print(f"✅ {area_code}の天気予報をDBに保存しました（{report_datetime}）")
            
            # 保存後に検証
            self.cursor.execute('''
            SELECT COUNT(*) FROM forecasts WHERE area_code = ? AND report_datetime = ?
            ''', (area_code, report_datetime))
            count = self.cursor.fetchone()[0]
            print(f"保存された予報データ数: {count}")
            
            return True
            
        except Exception as e:
            # エラー時はロールバック
            self.conn.rollback()
            print(f"天気予報保存エラー: {e}")
            import traceback
            traceback.print_exc()
            return False
        
    def get_weather_forecast(self, area_code):
        """
        指定された地域の最新の天気予報を取得
        
        Args:
            area_code: 地域コード
            
        Returns:
            dict: 整形された天気予報情報
        """
        try:
            print(f"天気予報をDBから取得しています: {area_code}")
            
            # 最新のレポート情報を取得
            self.cursor.execute('''
            SELECT report_datetime, publishing_office FROM report_info
            WHERE area_code = ?
            ORDER BY report_datetime DESC LIMIT 1
            ''', (area_code,))
            
            report_info = self.cursor.fetchone()
            
            if not report_info:
                print(f"レポート情報が見つかりません (area_code={area_code})")
                return None
                
            report_datetime, publishing_office = report_info
            print(f"レポート情報を取得しました - report_datetime={report_datetime}, publishing_office={publishing_office}")
            
            # 予報データを取得
            self.cursor.execute('''
            SELECT forecast_date, weather_code, weather FROM forecasts
            WHERE area_code = ? AND report_datetime = ?
            ORDER BY forecast_date
            ''', (area_code, report_datetime))
            
            forecasts = self.cursor.fetchall()
            
            if not forecasts:
                print(f"予報データが見つかりません (area_code={area_code}, report_datetime={report_datetime})")
                return None
                
            # 地域名を取得
            self.cursor.execute('''
            SELECT name FROM areas
            WHERE area_code = ?
            LIMIT 1
            ''', (area_code,))
            
            area_result = self.cursor.fetchone()
            area_name = area_result[0] if area_result else "不明"
            
            # 結果を整形
            result = {
                "area_code": area_code,
                "area_name": area_name,
                "report_datetime": report_datetime,
                "publishing_office": publishing_office,
                "forecasts": []
            }
            
            for forecast in forecasts:
                forecast_date, weather_code, weather = forecast
                result["forecasts"].append({
                    "date": forecast_date[:10],  # YYYY-MM-DDの部分だけ取得
                    "weather_code": weather_code,
                    "weather": weather
                })
                
            print(f"DB検索結果: {len(result['forecasts'])}件の予報データを取得")
            return result
            
        except Exception as e:
            print(f"天気予報取得エラー(DB): {e}")
            import traceback
            traceback.print_exc()
            return None