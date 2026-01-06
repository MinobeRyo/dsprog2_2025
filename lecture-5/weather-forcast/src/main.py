"""
天気予報アプリケーションのメインエントリーポイント
Fletアプリケーションを起動する
"""

import flet as ft
from ui.weather_view import WeatherView


def main(page: ft.Page):
    """
    Fletアプリケーションのメイン関数
    
    Args
        page: Fletのページオブジェクト
    """
    print("="*60)
    print("🚀 天気予報アプリケーション起動")
    print("="*60)
    
    # WeatherViewを作成してUIを構築
    weather_view = WeatherView(page)
    weather_view.build()
    
    print("\n✅ アプリケーション起動完了")
    print("="*60 + "\n")


# アプリケーションを起動
if __name__ == "__main__":
    ft.app(target=main)