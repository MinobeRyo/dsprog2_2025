"""
天気予報アプリケーションのエントリポイント
"""

import flet as ft
from api.weather_api import WeatherAPI
from ui.weather_view import WeatherView


def main(page: ft.Page):
    """
    アプリケーションのメイン関数
    
    Args:
        page: Fletのページオブジェクト
    """
    # ヘッダー出力
    print("="*60)
    print("🚀 天気予報アプリケーション起動")
    print("="*60)

    # APIクラスの初期化
    weather_api = WeatherAPI()
    
    # UIの初期化と構築
    weather_view = WeatherView(page)
    weather_view.build()


# アプリケーション起動
ft.app(target=main)