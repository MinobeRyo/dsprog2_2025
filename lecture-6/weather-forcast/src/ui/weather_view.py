"""
天気予報アプリのUI構築モジュール
Fletを使用した画面表示とユーザー操作の処理
iPhoneの天気アプリ風デザイン
"""

import flet as ft
from api.weather_api import WeatherAPI
# weather_view.py の先頭に追加
import threading
import time

class WeatherView:
    """
    天気予報アプリのUI管理クラス
    """
    
    def __init__(self, page: ft.Page):
        """
        WeatherViewの初期化
        制御: ページ設定とAPI初期化
        """
        self.page = page
        self.weather_api = WeatherAPI()
        self.area_list = None
        self.selected_area_name = None
        
        # ページ設定
        self.page.title = "天気予報アプリ"
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.padding = 0  # パディングをなくして画面いっぱいに表示
        self.page.window_width = 800
        self.page.window_height = 800
        self.page.bgcolor = ft.Colors.BLUE_ACCENT
        
        print("WeatherView初期化完了")
    
    
    def build(self):
        """
        UIを構築してページに追加する
        制御: 全UIコンポーネントの生成と配置
        """
        print("\n🎨 UI構築開始")
        
        # ローディング表示
        self.loading = ft.ProgressRing(visible=False, color=ft.Colors.WHITE)
        
        # エラーメッセージ表示エリア
        self.error_text = ft.Text(
            "",
            color=ft.Colors.RED_400,
            visible=False,
            text_align=ft.TextAlign.CENTER,
            size=16
        )
        
        # 地域選択用ドロップダウン
        self.area_dropdown = ft.PopupMenuButton(
            content=ft.Row([
                ft.Icon(ft.Icons.LOCATION_ON, color=ft.Colors.WHITE),
                ft.Text("地域を選択", color=ft.Colors.WHITE, size=18),
                ft.Icon(ft.Icons.ARROW_DROP_DOWN, color=ft.Colors.WHITE),
            ]),
            items=[]
        )
        
        # 天気予報表示エリア（スクロール可能な大きなコンテナ）
        self.weather_info = ft.Column(
            spacing=0,
            visible=False,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )
        
        # 地域未選択時のメッセージ
        self.welcome_message = ft.Container(
            content=ft.Column([
                ft.Icon(
                    name=ft.Icons.CLOUD_OUTLINED,
                    size=100,
                    color=ft.Colors.WHITE,
                ),
                ft.Text(
                    "地域を選択してください",
                    size=24,
                    color=ft.Colors.WHITE,
                    text_align=ft.TextAlign.CENTER,
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Text(
                    "右上のメニューから地域を選択すると\n天気予報が表示されます",
                    size=16,
                    color=ft.Colors.WHITE,
                    text_align=ft.TextAlign.CENTER,
                )
            ], 
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            alignment=ft.alignment.center,
            expand=True,
            bgcolor=ft.Colors.BLUE_ACCENT,
            padding=30
        )
        
        # カスタムアプリバー
        app_bar = ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.CLOUD, color=ft.Colors.WHITE, size=24),
                    ft.Container(width=10),
                    ft.Text("天気予報", color=ft.Colors.WHITE, size=20, weight=ft.FontWeight.BOLD),
                    ft.Container(expand=True),
                    self.area_dropdown,
                    ft.IconButton(
                        icon=ft.Icons.REFRESH,
                        icon_color=ft.Colors.WHITE,
                        tooltip="地域リストを再読み込み",
                        on_click=self.load_area_list,
                    ),
                ],
                alignment=ft.MainAxisAlignment.START,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.padding.symmetric(horizontal=15, vertical=10),
            bgcolor=ft.Colors.BLUE,
            height=60,
        )
        
        # メインコンテナ
        main_container = ft.Container(
            content=ft.Stack([
                self.welcome_message,
                self.weather_info,
            ]),
            expand=True,
        )
        
        # ローディングとエラーメッセージを表示するオーバーレイ
        self.status_overlay = ft.Container(
            content=ft.Column([
                self.loading,
                self.error_text,
            ], 
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
            ),
            expand=True,
            bgcolor=ft.Colors.with_opacity(0.7, ft.Colors.BLACK),
            visible=False,
        )
        
        # 全体レイアウト
        self.page.add(
            ft.Column([
                app_bar,
                ft.Stack([
                    main_container,
                    self.status_overlay,
                ],
                expand=True),
            ],
            spacing=0,
            expand=True)
        )
        
        print("✅ UI構築完了")
        
        # UIを構築した直後に地域リストを自動読み込み
        self.page.update()
        self.load_area_list_auto()
    
    
    def load_area_list_auto(self):
        """
        地域リストを自動的に読み込む
        制御: 初期ロード時にAPI呼び出し→ドロップダウン設定
        """
        print("\n📥 地域リスト自動読み込み開始")
        
        # ローディング表示ON
        self.status_overlay.visible = True
        self.loading.visible = True
        self.error_text.visible = False
        self.page.update()
        
        # APIから地域リストを取得
        self.area_list = self.weather_api.get_area_list()
        
        if self.area_list and 'offices' in self.area_list:
            # ドロップダウンのオプションを作成
            offices = self.area_list['offices']
            
            self.area_dropdown.items = [
                ft.PopupMenuItem(
                    text=info['name'],
                    on_click=lambda _, code=code: self.on_area_selected(code)
                )
                for code, info in offices.items()
            ]
            
            print(f"✅ {len(offices)}件の地域を自動読み込みしました")
        else:
            # エラー表示
            error_msg = "地域リストの読み込みに失敗しました"
            print(f"❌ {error_msg}")
            self.show_error_message(error_msg)
        
        # ローディング表示OFF
        self.loading.visible = False
        self.status_overlay.visible = False
        self.page.update()
    
    
    def load_area_list(self, _):
        """
        地域リストを読み込んでドロップダウンに設定する
        制御: リフレッシュボタンクリック時のAPI再呼び出し
        """
        print("\n📥 地域リスト読み込み開始")
        
        # ローディング表示ON
        self.status_overlay.visible = True
        self.loading.visible = True
        self.error_text.visible = False
        self.page.update()
        
        # APIから地域リストを取得
        self.area_list = self.weather_api.get_area_list()
        
        if self.area_list and 'offices' in self.area_list:
            # ドロップダウンのオプションを作成
            offices = self.area_list['offices']
            
            self.area_dropdown.items = [
                ft.PopupMenuItem(
                    text=info['name'],
                    on_click=lambda _, code=code: self.on_area_selected(code)
                )
                for code, info in offices.items()
            ]
            
            print(f"✅ {len(offices)}件の地域を読み込みました")
            self.show_success_message(f"{len(offices)}件の地域を読み込みました")
        else:
            # エラー表示
            error_msg = "地域リストの読み込みに失敗しました"
            print(f"❌ {error_msg}")
            self.show_error_message(error_msg)
        
        # ローディング表示OFF
        self.loading.visible = False
        self.status_overlay.visible = False
        self.page.update()
    
    
    def on_area_selected(self, area_code):
        """
        地域が選択されたときの処理
        制御: 選択地域の確認→天気データAPI呼び出し→画面表示
        """
        if not area_code:
            return
        
        print(f"\n📍 地域選択：{area_code}")
        
        # 選択された地域名をセット
        if self.area_list and 'offices' in self.area_list:
            self.selected_area_name = self.area_list['offices'].get(area_code, {}).get('name', '不明な地域')
            
            # ドロップダウンの表示テキストを更新
            self.area_dropdown.content = ft.Row([
                ft.Icon(ft.Icons.LOCATION_ON, color=ft.Colors.WHITE),
                ft.Text(self.selected_area_name, color=ft.Colors.WHITE, size=18),
                ft.Icon(ft.Icons.ARROW_DROP_DOWN, color=ft.Colors.WHITE),
            ])
        
        # ローディング表示ON、ウェルカムメッセージOFF
        self.status_overlay.visible = True
        self.loading.visible = True
        self.error_text.visible = False
        self.welcome_message.visible = False
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
                self.welcome_message.visible = True
        else:
            self.show_error_message("天気予報の取得に失敗しました")
            self.welcome_message.visible = True
        
        # ローディング表示OFF
        self.loading.visible = False
        self.status_overlay.visible = False
        self.page.update()
    
    
    def display_weather(self, weather_data):
        """
        天気予報情報を画面に表示する
        制御: データ解析→レイアウト生成→UI更新（背景色も動的に変更）
        """
        print("\n🌤️  天気予報表示開始")
        
        # 既存の表示をクリア
        self.weather_info.controls.clear()
        
        # 天気に基づいて背景色を設定
        bg_color = ft.Colors.BLUE_ACCENT
        main_weather = weather_data.get('forecasts', [{}])[0].get('weather', '')
        if "雨" in main_weather:
            bg_color = ft.Colors.BLUE_GREY_700
        elif "曇" in main_weather:
            bg_color = ft.Colors.BLUE_GREY_400
        elif "晴" in main_weather:
            bg_color = ft.Colors.BLUE_ACCENT
        
        # 大きな天気アイコンと気温
        weather_icon = "☀️"
        first_forecast = weather_data.get('forecasts', [{}])[0]
        weather_text = first_forecast.get('weather', '不明')
        if "雨" in weather_text:
            weather_icon = "🌧️"
        elif "曇" in weather_text or "くもり" in weather_text:
            weather_icon = "☁️"
        elif "雪" in weather_text:
            weather_icon = "❄️"
        
        # ヘッダー情報（地域名、現在の天気など）
        header = ft.Container(
            content=ft.Column([
                ft.Container(height=20),
                ft.Text(
                    weather_data.get('area_name', '不明'),
                    size=36,
                    color=ft.Colors.WHITE,
                    weight=ft.FontWeight.BOLD,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Container(height=10),
                ft.Text(
                    weather_icon,
                    size=100,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Text(
                    self._get_simple_weather(weather_text),
                    size=24,
                    color=ft.Colors.WHITE,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Container(height=10),
                ft.Text(
                    f"発表: {weather_data.get('report_datetime', '不明')[:16]}",
                    size=14,
                    color=ft.Colors.WHITE70,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Container(height=30),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.padding.symmetric(horizontal=20),
            bgcolor=bg_color,
        )
        
        self.weather_info.controls.append(header)
        
        # 時間ごとの天気予報（横スクロール）
        forecasts = weather_data.get('forecasts', [])
        
        # 日別予報カード
        forecast_card = ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.Text(
                        "天気予報",
                        size=18,
                        color=ft.Colors.WHITE,
                        weight=ft.FontWeight.BOLD,
                    ),
                    padding=ft.padding.only(left=15, top=15, bottom=5),
                ),
                
                ft.Container(
                    content=ft.Column([
                        self._create_forecast_row(forecast, i)
                        for i, forecast in enumerate(forecasts)
                    ],
                    spacing=0),
                    padding=ft.padding.only(bottom=15),
                )
            ]),
            margin=ft.margin.symmetric(horizontal=15, vertical=10),
            border_radius=15,
            bgcolor=ft.Colors.with_opacity(0.2, ft.Colors.WHITE),
        )
        
        self.weather_info.controls.append(forecast_card)
        
        # 追加情報カード
        info_card = ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.Text(
                        "その他の情報",
                        size=18,
                        color=ft.Colors.WHITE,
                        weight=ft.FontWeight.BOLD,
                    ),
                    padding=ft.padding.only(left=15, top=15, bottom=5),
                ),
                
                ft.Container(
                    content=ft.Column([
                        ft.ListTile(
                            leading=ft.Icon(ft.Icons.INFO_OUTLINE, color=ft.Colors.WHITE),
                            title=ft.Text("発表元", color=ft.Colors.WHITE),
                            subtitle=ft.Text(
                                weather_data.get('publishing_office', '不明'),
                                color=ft.Colors.WHITE70
                            ),
                        ),
                        ft.ListTile(
                            leading=ft.Icon(ft.Icons.CLOUD_OUTLINED, color=ft.Colors.WHITE),
                            title=ft.Text("天気概況", color=ft.Colors.WHITE),
                            subtitle=ft.Text(
                                "詳細は気象庁ウェブサイトをご覧ください",
                                color=ft.Colors.WHITE70
                            ),
                        ),
                    ]),
                )
            ]),
            margin=ft.margin.symmetric(horizontal=15, vertical=10),
            border_radius=15,
            bgcolor=ft.Colors.with_opacity(0.2, ft.Colors.WHITE),
        )
        
        self.weather_info.controls.append(info_card)
        self.weather_info.controls.append(ft.Container(height=30))
        
        self.weather_info.visible = True
        self.page.bgcolor = bg_color
        print(f"✅ {len(forecasts)}日分の天気予報を表示しました")
    
    
    def _get_simple_weather(self, weather_text):
        """
        天気テキストを簡略化する
        制御: 文字列解析→最初の単語を抽出
        """
        if not weather_text:
            return "不明"
            
        weather_parts = weather_text.split()
        main_weather = weather_parts[0] if weather_parts else "不明"
        
        return main_weather
    
    
    def _create_forecast_row(self, forecast, index):
        """
        各予報日の行を作成する
        制御: 天気データ→アイコン判定→チップ生成→行レイアウト構築
        """
        weather_text = forecast.get('weather', '不明')
        weather_parts = weather_text.split()
        
        # 主要な天気を判断
        main_weather = weather_parts[0] if weather_parts else "不明"
        
        # 天気に応じたアイコン選択
        weather_icon = "☀️"
        if "雨" in main_weather:
            weather_icon = "🌧️"
        elif "曇" in main_weather or "くもり" in main_weather:
            weather_icon = "☁️"
        elif "雪" in main_weather:
            weather_icon = "❄️"
        elif "晴" in main_weather:
            weather_icon = "☀️"
        
        # 日付表示のフォーマット
        date_str = forecast.get('date', '')
        if date_str:
            try:
                month = int(date_str[5:7])
                day = int(date_str[8:10])
                date_display = f"{month}月{day}日"
            except:
                date_display = date_str[:10]
        else:
            date_display = "不明"
        
        # インデックスで今日/明日の判定
        if index == 0:
            date_display = f"今日 ({date_display})"
        elif index == 1:
            date_display = f"明日 ({date_display})"
        
        # 天気情報を視覚的に構造化
        weather_chips = []
        time_periods = []
        
        # 時間帯と天気の組み合わせを抽出
        current_weather = None
        current_time = None
        
        for part in weather_parts:
            if part in ["晴れ", "曇り", "雨", "雪", "くもり", "ふぶく"]:
                current_weather = part
                if current_time:
                    time_periods.append((current_time, current_weather))
                    current_time = None
            elif part in ["朝", "昼", "夕方", "夜", "夜遅く", "明け方", "夜のはじめ頃", "一時", "後", "のち"]:
                current_time = part
            elif part in ["所により"]:
                pass
        
        # 残りの天気と時間の組み合わせを追加
        if current_weather and not current_time:
            time_periods.append(("終日", current_weather))
        elif current_time and current_weather:
            time_periods.append((current_time, current_weather))
        
        # チップの作成（時間帯ごとの天気）
        for time, weather in time_periods:
            icon = "☀️"
            chip_color = ft.Colors.with_opacity(0.7, ft.Colors.WHITE)
            
            if "雨" in weather:
                icon = "🌧️"
                chip_color = ft.Colors.with_opacity(0.7, ft.Colors.BLUE)
            elif "曇" in weather or "くもり" in weather:
                icon = "☁️"
                chip_color = ft.Colors.with_opacity(0.7, ft.Colors.GREY)
            elif "雪" in weather:
                icon = "❄️"
                chip_color = ft.Colors.with_opacity(0.7, ft.Colors.LIGHT_BLUE)
            elif "晴" in weather:
                icon = "☀️"
                chip_color = ft.Colors.with_opacity(0.7, ft.Colors.ORANGE)
            
            weather_chips.append(
                ft.Container(
                    content=ft.Row([
                        ft.Text(icon, size=16),
                        ft.Text(f"{time}: {weather}", color=ft.Colors.BLACK, size=12),
                    ],
                    spacing=4,
                    alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    padding=ft.padding.symmetric(horizontal=8, vertical=4),
                    border_radius=15,
                    bgcolor=chip_color,
                )
            )
        
        return ft.Container(
            content=ft.Column([
                # 日付と主要天気
                ft.Row([
                    ft.Container(
                        content=ft.Text(
                            date_display,
                            color=ft.Colors.WHITE,
                            size=16,
                            weight=ft.FontWeight.BOLD,
                        ),
                        width=130,
                    ),
                    
                    ft.Container(
                        content=ft.Text(
                            weather_icon,
                            size=24,
                        ),
                        width=40,
                    ),
                    
                    ft.Container(
                        content=ft.Text(
                            main_weather,
                            color=ft.Colors.WHITE,
                            size=16,
                            weight=ft.FontWeight.BOLD,
                        ),
                        expand=True,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                
                # 時間帯ごとの天気チップ（横スクロール）
                ft.Container(
                    content=ft.Row(
                        weather_chips,
                        scroll=ft.ScrollMode.AUTO,
                        spacing=8,
                    ),
                    margin=ft.margin.only(top=8, left=8),
                    height=35,
                ) if weather_chips else ft.Container(),
            ]),
            padding=ft.padding.symmetric(horizontal=15, vertical=12),
            border_radius=10,
            ink=True,
            on_hover=lambda e: self._on_forecast_hover(e),
        )
    
    
    def _on_forecast_hover(self, e):
        """
        予報行のホバーエフェクト処理
        制御: ホバー状態判定→背景色ON/OFF
        """
        if e.data == "true":
            e.control.bgcolor = ft.Colors.with_opacity(0.1, ft.Colors.WHITE)
        else:
            e.control.bgcolor = None
        
        e.control.update()
    
        
    def show_error_message(self, message):
        """
        エラーメッセージを表示する
        制御: メッセージ表示→3秒後に自動消去
        """
        self.error_text.value = f"❌ {message}"
        self.error_text.visible = True
        self.status_overlay.visible = True
        self.page.update()
        
        # 3秒後に非表示 (スレッドを使用)
        def delayed_hide():
            time.sleep(3)  # 3秒待機
            self.error_text.visible = False
            self.status_overlay.visible = False
            self.page.update()
        
        # 別スレッドで実行
        threading.Thread(target=delayed_hide, daemon=True).start()


    def show_success_message(self, message):
        """
        成功メッセージを表示する
        制御: 成功メッセージ表示→色変更→2秒後に自動消去・色戻す
        """
        self.error_text.value = f"✅ {message}"
        self.error_text.color = ft.Colors.GREEN_400
        self.error_text.visible = True
        self.status_overlay.visible = True
        self.page.update()
        
        # 2秒後に非表示 (スレッドを使用)
        def delayed_hide():
            time.sleep(2)  # 2秒待機
            self.error_text.visible = False
            self.status_overlay.visible = False
            self.error_text.color = ft.Colors.RED_400  # 元の色に戻す
            self.page.update()
        
        # 別スレッドで実行
        threading.Thread(target=delayed_hide, daemon=True).start()