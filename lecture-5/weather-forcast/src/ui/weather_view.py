"""
天気予報アプリのUI構築モジュール
Fletを使用した画面表示とユーザー操作の処理
"""

import flet as ft
from api.weather_api import WeatherAPI


class WeatherView:
    """
    天気予報アプリのUI管理クラス
    """
    
    def __init__(self, page: ft.Page):
        """
        WeatherViewの初期化
        
        Args
            page: Fletのページオブジェクト
        """
        self.page = page
        self.weather_api = WeatherAPI()
        self.area_list = None
        
        # ページ設定
        self.page.title = "天気予報アプリ"
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.padding = 20
        self.page.window_width = 800
        self.page.window_height = 600
        
        print("WeatherView初期化完了")
    
    
    def build(self):
        """
        UIを構築してページに追加する
        """
        print("\n🎨 UI構築開始")
        
        # タイトル
        title = ft.Text(
            "☀️ 天気予報アプリ",
            size=30,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.BLUE_700
        )
        
        # ローディング表示
        self.loading = ft.ProgressRing(visible=False)
        
        # エラーメッセージ表示エリア
        self.error_text = ft.Text(
            "",
            color=ft.Colors.RED_700,
            visible=False
        )
        
        # 地域選択ドロップダウン
        self.area_dropdown = ft.Dropdown(
            label="地域を選択してください",
            width=400,
            on_change=self.on_area_selected
        )
        
        # 天気予報表示エリア
        self.weather_info = ft.Column(
            spacing=10,
            visible=False
        )
        
        # 地域リストを読み込むボタン
        load_button = ft.ElevatedButton(
            "地域リストを読み込む",
            icon=ft.Icons.DOWNLOAD,
            on_click=self.load_area_list
        )
        
        # レイアウト構築
        self.page.add(
            ft.Container(
                content=ft.Column([
                    title,
                    ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
                    load_button,
                    self.loading,
                    self.error_text,
                    ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
                    self.area_dropdown,
                    ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
                    self.weather_info
                ],
                scroll=ft.ScrollMode.AUTO,  # ← この行を追加
                ),
                padding=20,
                expand=True  # ← この行を追加
            )
        )
        
        print("✅ UI構築完了")
    
    
    def load_area_list(self, e):
        """
        地域リストを読み込んでドロップダウンに設定する
        
        Args:
            e: イベントオブジェクト
        """
        print("\n📥 地域リスト読み込み開始")
        
        # ローディング表示
        self.loading.visible = True
        self.error_text.visible = False
        self.page.update()
        
        # APIから地域リストを取得
        self.area_list = self.weather_api.get_area_list()
        
        if self.area_list and 'offices' in self.area_list:
            # ドロップダウンのオプションを作成
            offices = self.area_list['offices']
            self.area_dropdown.options = [
                ft.dropdown.Option(key=code, text=info['name'])
                for code, info in offices.items()
            ]
            
            print(f"✅ {len(offices)}件の地域を読み込みました")
            self.show_success_message(f"{len(offices)}件の地域を読み込みました")
        else:
            # エラー表示
            error_msg = "地域リストの読み込みに失敗しました"
            print(f"❌ {error_msg}")
            self.show_error_message(error_msg)
        
        # ローディング非表示
        self.loading.visible = False
        self.page.update()
    
    
    def on_area_selected(self, e):
        """
        地域が選択されたときの処理
        
        Args:
            e: イベントオブジェクト
        """
        area_code = self.area_dropdown.value
        
        if not area_code:
            return
        
        print(f"\n📍 地域選択：{area_code}")
        
        # ローディング表示
        self.loading.visible = True
        self.error_text.visible = False
        self.weather_info.visible = False
        self.page.update()
        
        # 天気予報を取得
        forecast_data = self.weather_api.get_weather_forecast(area_code)
        
        if forecast_data:
            # データを解析
            parsed_data = self.weather_api.parse_weather_data(forecast_data)
            
            if parsed_data:
                # 天気予報を表示
                self.display_weather(parsed_data)
            else:
                self.show_error_message("天気予報データの解析に失敗しました")
        else:
            self.show_error_message("天気予報の取得に失敗しました")
        
        # ローディング非表示
        self.loading.visible = False
        self.page.update()
    
    
    def display_weather(self, weather_data):
        """
        天気予報情報を画面に表示する
        
        Args:
            weather_data 解析済みの天気予報データ
        """
        print("\n🌤️  天気予報表示開始")
        
        # 既存の表示をクリア
        self.weather_info.controls.clear()
        
        # ヘッダー情報
        header = ft.Container(
            content=ft.Column([
                ft.Text(
                    weather_data.get('area_name', '不明'),
                    size=24,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.BLUE_900
                ),
                ft.Text(
                    f"発表: {weather_data.get('publishing_office', '不明')}",
                    size=14,
                    color=ft.Colors.GREY_700
                ),
                ft.Text(
                    f"発表日時: {weather_data.get('report_datetime', '不明')[:16]}",
                    size=14,
                    color=ft.Colors.GREY_700
                ),
            ]),
            bgcolor=ft.Colors.BLUE_50,
            padding=15,
            border_radius=10
        )
        
        self.weather_info.controls.append(header)
        
        # 各日の予報を表示
        forecasts = weather_data.get('forecasts', [])
        for i, forecast in enumerate(forecasts):
            forecast_card = ft.Container(
                content=ft.Column([
                    ft.Text(
                        f"📅 {forecast.get('date', '不明')[:10]}",
                        size=18,
                        weight=ft.FontWeight.BOLD
                    ),
                    ft.Divider(height=10, color=ft.Colors.GREY_300),
                    ft.Text(f"☁️ 天気: {forecast.get('weather', '不明')}"),
                    ft.Text(f"💨 風: {forecast.get('wind', '不明')}"),
                    ft.Text(f"🌊 波: {forecast.get('wave', '不明')}"),
                ]),
                bgcolor=ft.Colors.WHITE,
                padding=15,
                border_radius=10,
                border=ft.border.all(1,ft.Colors.GREY_300)
            )
            self.weather_info.controls.append(forecast_card)
        
        self.weather_info.visible = True
        print(f"✅ {len(forecasts)}日分の天気予報を表示しました")
    
    
    def show_error_message(self, message):
        """
        エラーメッセージを表示する
        
        Args:
            message: 表示するエラーメッセージ
        """
        self.error_text.value = f"❌ {message}"
        self.error_text.visible = True
        self.page.update()
    
    
    def show_success_message(self, message):
        """
        成功メッセージを表示する
        
        Args:
            message: 表示する成功メッセージ
        """
        # 一時的にエラーテキストを成功メッセージに使用
        self.error_text.value = f"✅ {message}"
        self.error_text.color =ft.Colors.GREEN_700
        self.error_text.visible = True
        self.page.update()
        
        # 元の色に戻す
        self.error_text.color =ft.Colors.RED_700