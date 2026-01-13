"""
天気予報API連携モジュール
気象庁の天気予報APIからデータを取得
"""

import json
from api.api_client import APIClient
from db.weather_database import WeatherDatabase


class WeatherAPI:
    """
    天気予報APIからデータを取得するクラス
    DBキャッシュも管理
    """
    
    def __init__(self):
        """
        WeatherAPIクラスの初期化
        """
        # APIクライアントとDBの初期化
        self.api_client = APIClient()
        self.db = WeatherDatabase()
        
        # APIエンドポイント
        self.area_url = "https://www.jma.go.jp/bosai/common/const/area.json"
        self.forecast_url = "https://www.jma.go.jp/bosai/forecast/data/forecast/{office}.json"
        
        print("WeatherAPI初期化完了")
    
    
    def get_area_list(self):
        """
        地域リストを取得する
        まずDBから取得を試み、なければAPIから取得してDBに保存
        
        Returns:
            地域情報を含む辞書 {'offices': {...}}
        """
        # まずDBから取得を試みる
        area_list = self.db.get_area_list()
        
        # DBに地域リストがない場合、APIから取得
        if not area_list or not area_list.get('offices'):
            print("DBに地域リストがないか空なので、APIから取得します")
            
            # APIから地域リストを取得
            response = self.api_client.get(self.area_url)
            
            if response.status_code == 200:
                try:
                    area_data = response.json()
                    
                    # 必要な情報だけを抽出（offices部分）
                    if 'offices' in area_data:
                        area_list = {'offices': area_data['offices']}
                        
                        # DBに保存
                        self.db.save_area_list(area_list)
                    else:
                        print("APIレスポンスにofficesキーがありません")
                        return None
                except Exception as e:
                    print(f"地域リストのJSONパースエラー: {e}")
                    return None
            else:
                print(f"地域リスト取得に失敗: ステータスコード {response.status_code}")
                return None
        
        return area_list
        
    def get_weather_forecast(self, area_code):
        """
        指定されたエリアの天気予報を取得する
        まずDBから取得を試み、なければAPIから取得してDBに保存
        
        Args:
            area_code: 地域コード
            
        Returns:
            天気予報データ（JSON文字列）
        """
        try:
            if not area_code:
                return None
                
            # まずDBから最新の天気予報を取得
            db_forecast = self.db.get_weather_forecast(area_code)
            
            if db_forecast:
                print(f"DBから{area_code}の天気予報を取得しました")
                # 日付ごとに重複を排除
                if 'forecasts' in db_forecast:
                    unique_forecasts = {}
                    for forecast in db_forecast['forecasts']:
                        date_key = forecast['date'][:10]  # YYYY-MM-DDの部分だけを使用
                        if date_key not in unique_forecasts:
                            unique_forecasts[date_key] = forecast
                    
                    # 辞書から値のリストを作成し、日付でソート
                    db_forecast['forecasts'] = sorted(unique_forecasts.values(), key=lambda x: x["date"])
                    print(f"重複排除後の予報件数: {len(db_forecast['forecasts'])}")
                
                return db_forecast
            
            # DBにデータがない場合、APIから取得
            print(f"DBに{area_code}の天気予報がないので、APIから取得します")
            
            # URLの整形（地域コードを挿入）
            url = self.forecast_url.format(office=area_code)
            
            # APIリクエスト
            response = self.api_client.get(url)
            
            if response.status_code == 200:
                forecast_data = response.json()
                
                # DBに保存
                if forecast_data and len(forecast_data) > 0:
                    saved = self.db.save_weather_forecast(area_code, forecast_data[0])
                    
                    if saved:
                        # 保存後にDBから整形済みデータを取得
                        db_data = self.db.get_weather_forecast(area_code)
                        
                        # 重複を排除して返す
                        if db_data and 'forecasts' in db_data:
                            unique_forecasts = {}
                            for forecast in db_data['forecasts']:
                                date_key = forecast['date'][:10]
                                if date_key not in unique_forecasts:
                                    unique_forecasts[date_key] = forecast
                            
                            db_data['forecasts'] = sorted(unique_forecasts.values(), key=lambda x: x["date"])
                            print(f"重複排除後の予報件数: {len(db_data['forecasts'])}")
                        
                        return db_data
                    else:
                        print("天気予報データの保存に失敗しました")
                else:
                    print("APIから有効な天気予報データが取得できませんでした")
            else:
                print(f"天気予報取得に失敗: ステータスコード {response.status_code}")
            
            return None
            
        except Exception as e:
            print(f"天気予報取得エラー: {e}")
            import traceback
            traceback.print_exc()
            return None


    def parse_weather_data(self, weather_data):
        """
        天気予報データを解析して必要な情報を抽出する
        DBからのデータはすでに解析済みなので、そのまま返す
        
        Args:
            weather_data: 天気予報データ
            
        Returns:
            解析済みの天気予報情報を含む辞書
        """
        # DBからのデータは既に解析済み
        if isinstance(weather_data, dict) and 'area_name' in weather_data:
            # 重複を排除
            if 'forecasts' in weather_data:
                unique_forecasts = {}
                for forecast in weather_data['forecasts']:
                    date_key = forecast['date'][:10]
                    if date_key not in unique_forecasts:
                        unique_forecasts[date_key] = forecast
                
                weather_data['forecasts'] = sorted(unique_forecasts.values(), key=lambda x: x["date"])
                print(f"parse_weather_data: 重複排除後の予報件数 {len(weather_data['forecasts'])}")
            
            return weather_data
            
        # APIレスポンスのJSONデータの場合は解析が必要（互換性のため残す）
        try:
            if isinstance(weather_data, str):
                weather_data = json.loads(weather_data)
                
            result = {}
            
            # 発表元・発表日時
            result['publishing_office'] = weather_data.get('publishingOffice', '不明')
            result['report_datetime'] = weather_data.get('reportDatetime', '不明')
            
            # 予報データ取得（最初のtimeSeriesのみ使用）
            if 'timeSeries' in weather_data and len(weather_data['timeSeries']) > 0:
                time_series = weather_data['timeSeries'][0]
                
                if 'timeDefines' in time_series and 'areas' in time_series:
                    # 日付のリスト
                    time_defines = time_series['timeDefines']
                    
                    # 地域データ（最初の地域のみ使用）
                    if len(time_series['areas']) > 0:
                        area = time_series['areas'][0]
                        
                        # 地域名
                        if 'area' in area and 'name' in area['area']:
                            result['area_name'] = area['area']['name']
                        else:
                            result['area_name'] = '不明'
                        
                        # 各日の天気 - 重複を排除
                        if 'weathers' in area and 'weatherCodes' in area:
                            weathers = area['weathers']
                            weather_codes = area['weatherCodes']
                            unique_forecasts = {}
                            
                            for i, weather in enumerate(weathers):
                                if i < len(time_defines):
                                    weather_code = weather_codes[i] if i < len(weather_codes) else ""
                                    date_key = time_defines[i][:10]  # YYYY-MM-DDの部分だけ
                                    
                                    # 同じ日付の予報がまだなければ追加
                                    if date_key not in unique_forecasts:
                                        unique_forecasts[date_key] = {
                                            'date': date_key,
                                            'weather': weather,
                                            'weather_code': weather_code
                                        }
                            
                            # 辞書から値のリストを作成し、日付でソート
                            result['forecasts'] = sorted(unique_forecasts.values(), key=lambda x: x["date"])
            
            return result
        except Exception as e:
            print(f"天気データ解析エラー: {e}")
            import traceback
            traceback.print_exc()
            return None