"""
気象庁API専用のモジュール
地域リストと天気予報データの取得機能を提供
"""

from src.api.api_client import APIClient


class WeatherAPI:
    """
    気象庁APIとの通信を管理するクラス
    """
    
    # 気象庁APIのエンドポイント
    AREA_LIST_URL = "http://www.jma.go.jp/bosai/common/const/area.json"
    FORECAST_URL_TEMPLATE = "https://www.jma.go.jp/bosai/forecast/data/forecast/{area_code}.json"
    
    
    def __init__(self):
        """
        WeatherAPIの初期化
        APIClientインスタンスを作成
        """
        self.client = APIClient(timeout=15)
        print("WeatherAPI初期化完了")
    
    
    def get_area_list(self):
        """
        全国の地域リストを取得する
        
        Returns:
            dict 地域情報の辞書
                  {
                      "centers": {...},  # 地方区分
                      "offices": {...},  # 気象台
                      "class10s": {...}, # 都道府県レベル
                      "class15s": {...}, # 市町村レベル
                      "class20s": {...}  # 細分区域
                  }
            None エラーが発生した場合
        """
        print("\n🗺️  地域リストを取得中...")
        data = self.client.get_json(self.AREA_LIST_URL, log_detail=False)
        
        if data:
            # データの構造を確認
            print(f"取得したデータのキー：{list(data.keys())}")
            if 'offices' in data:
                print(f"地域数：{len(data['offices'])}件")
        
        return data
    
    
    def get_weather_forecast(self, area_code):
        """
        指定された地域の天気予報を取得する
        
        Args:
            area_code 地域コード（例：130000は東京都）
            
        Returns:
            list: 天気予報データのリスト
                  [
                      {
                          "publishingOffice": "気象庁",
                          "reportDatetime": "2024-01-01T1100:00+09:00",
                          "timeSeries": [...]
                      }
                  ]
            None: エラーが発生した場合
        """
        print(f"\n☁️  天気予報を取得中（地域コード：{area_code}）...")
        
        # URLを生成
        url = self.FORECAST_URL_TEMPLATE.format(area_code=area_code)
        
        # データを取得
        data = self.client.get_json(url, log_detail=False)
        
        if data:
            print(f"✅ 天気予報データ取得成功")
        
        return data
    
    
    def parse_weather_data(self, forecast_data):
        """
        天気予報データから必要な情報を抽出する
        
        Args
            forecast_data: get_weather_forecastで取得したデータ
            
        Returns:
            dict: 整形された天気情報
                  {
                      "publishing_office": "発表機関",
                      "report_datetime": "発表日時",
                      "area_name": "地域名",
                      "forecasts": [
                          {
                              "date": "日付",
                              "weather": "天気",
                              "wind": "風",
                              "wave": "波"
                          }
                      ]
                  }
            None: データ解析に失敗した場合
        """
        try:
            if not forecast_data or len(forecast_data) == 0:
                print("⚠️  天気予報データが空です")
                return None
            
            # 最初の予報データを取得
            first_forecast = forecast_data[0]
            
            # 基本情報を取得
            result = {
                "publishing_office": first_forecast.get("publishingOffice", "不明"),
                "report_datetime": first_forecast.get("reportDatetime", "不明"),
                "forecasts": []
            }
            
            # 時系列データから天気情報を抽出
            time_series = first_forecast.get("timeSeries", [])
            if len(time_series) > 0:
                # 天気、風、波の情報
                weather_series = time_series[0]
                areas = weather_series.get("areas", [])
                
                if len(areas) > 0:
                    area = areas[0]
                    result["area_name"] = area.get("area", {}).get("name", "不明")
                    
                    # 日付と天気のデータを結合
                    time_defines = weather_series.get("timeDefines", [])
                    weathers = area.get("weathers", [])
                    winds = area.get("winds", [])
                    waves = area.get("waves", [])
                    
                    for i in range(len(time_defines)):
                        forecast_item = {
                            "date": time_defines[i] if i < len(time_defines) else "不明",
                            "weather": weathers[i] if i < len(weathers) else "不明",
                            "wind": winds[i] if i < len(winds) else "不明",
                            "wave": waves[i] if i < len(waves) else "不明"
                        }
                        result["forecasts"].append(forecast_item)
            
            print(f"✅ データ解析成功（{len(result['forecasts'])}日分の予報）")
            return result
            
        except Exception as e:
            from utils.logger import log_error
            log_error("天気予報データの解析に失敗しました", e)
            return None
if __name__ == "__main__":
    # テスト実行用のコード
    api = WeatherAPI()
    print("Weather API initialized successfully")