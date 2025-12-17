import flet as ft  
import math  


# ボタンの基本クラス - すべての電卓ボタンの親
class CalcButton(ft.ElevatedButton):
    def __init__(self, text, button_clicked, expand=1):
        super().__init__()  # 親クラス(ElevatedButton)の初期化
        self.text = text  # ボタンに表示するテキスト
        self.expand = expand  # ボタンの横幅（相対値）
        self.on_click = button_clicked  # クリックされた時に実行する関数
        self.data = text  # ボタンのデータ属性（クリック時に識別するため）


# 数字ボタン用のクラス - 0-9と小数点のボタン
class DigitButton(CalcButton):
    def __init__(self, text, button_clicked, expand=1):
        CalcButton.__init__(self, text, button_clicked, expand)  # 親クラスの初期化
        self.bgcolor =ft.Colors.WHITE24  # 背景色: 薄い白
        self.color =ft.Colors.WHITE  # 文字色: 白


# 演算子ボタン用のクラス - +, -, *, /, = のボタン
class ActionButton(CalcButton):
    def __init__(self, text, button_clicked):
        CalcButton.__init__(self, text, button_clicked)  # 親クラスの初期化
        self.bgcolor =ft.Colors.ORANGE  # 背景色: オレンジ
        self.color =ft.Colors.WHITE  # 文字色: 白


# 特殊機能ボタン用のクラス - AC, +/-, %, 数学機能など
class ExtraActionButton(CalcButton):
    def __init__(self, text, button_clicked):
        CalcButton.__init__(self, text, button_clicked)  # 親クラスの初期化
        self.bgcolor =ft.Colors.BLUE_GREY_100  # 背景色: 青みがかったグレー
        self.color =ft.Colors.BLACK  # 文字色: 黒


# 電卓アプリのメインクラス - UIとロジックをまとめています
class CalculatorApp(ft.Container):
    def __init__(self):
        super().__init__()  # 親クラス(Container)の初期化
        self.reset()  # 計算状態をリセット

        # 計算結果を表示するテキストフィールド
        self.result = ft.Text(value="0", color=ft.Colors.WHITE, size=20)
        
        # 電卓のサイズとデザイン設定
        self.width = 350  # 幅:350ピクセル
        self.bgcolor =ft.Colors.BLACK  # 背景色: 黒
        self.border_radius = ft.border_radius.all(20)  # 角を丸くする: 半径20
        self.padding = 20  # 内側の余白: 20ピクセル
        
        # 電卓の画面レイアウト - 縦に並べる
        self.content = ft.Column(
            controls=[
                # 計算結果表示行 - 右寄せで表示
                ft.Row(controls=[self.result], alignment="end"),
        
                ft.Row(
                    controls=[
                        ExtraActionButton(text="sqrt", button_clicked=self.button_clicked),  #平方根計算
                        ExtraActionButton(text="^2", button_clicked=self.button_clicked),    #2乗計算
                        ExtraActionButton(text="1/x", button_clicked=self.button_clicked),   #逆数計算
                        ExtraActionButton(text="exp", button_clicked=self.button_clicked),   #指数関数計算
                        ExtraActionButton(text="π", button_clicked=self.button_clicked),     #円周率
                    ]
                ),
                
                # 基本機能ボタンの行 - クリア、符号反転、パーセント、割り算
                ft.Row(
                    controls=[
                        ExtraActionButton(text="AC", button_clicked=self.button_clicked),    #オールクリア
                        ExtraActionButton(text="+/-", button_clicked=self.button_clicked),   #符号反転
                        ExtraActionButton(text="%", button_clicked=self.button_clicked),     #パーセント
                        ActionButton(text="/", button_clicked=self.button_clicked),          #割り算
                    ]
                ),
                
                # 数字7,8,9と掛け算の行
                ft.Row(
                    controls=[
                        DigitButton(text="7", button_clicked=self.button_clicked),  #数字7
                        DigitButton(text="8", button_clicked=self.button_clicked),  #数字8
                        DigitButton(text="9", button_clicked=self.button_clicked),  #数字9
                        ActionButton(text="*", button_clicked=self.button_clicked), #掛け算
                    ]
                ),
                
                # 数字4,5,6と引き算の行
                ft.Row(
                    controls=[
                        DigitButton(text="4", button_clicked=self.button_clicked),  #数字4
                        DigitButton(text="5", button_clicked=self.button_clicked),  #数字5
                        DigitButton(text="6", button_clicked=self.button_clicked),  #数字6
                        ActionButton(text="-", button_clicked=self.button_clicked), #引き算
                    ]
                ),
                
                # 数字1,2,3と足し算の行
                ft.Row(
                    controls=[
                        DigitButton(text="1", button_clicked=self.button_clicked),  #数字1
                        DigitButton(text="2", button_clicked=self.button_clicked),  #数字2
                        DigitButton(text="3", button_clicked=self.button_clicked),  #数字3
                        ActionButton(text="+", button_clicked=self.button_clicked), #足し算
                    ]
                ),
                
                # 数字0、小数点、イコールの行
                ft.Row(
                    controls=[
                        DigitButton(text="0", expand=2, button_clicked=self.button_clicked),  #数字0（幅2倍）
                        DigitButton(text=".", button_clicked=self.button_clicked),            #小数点
                        ActionButton(text="=", button_clicked=self.button_clicked),           #イコール
                    ]
                ),
            ]
        )

    # ボタンがクリックされた時に呼ばれるメソッド
    def button_clicked(self, e):
        data = e.control.data  # クリックされたボタンのデータを取得
        print(f"Button clicked with data = {data}")  # デバッグ出力でどのボタンが押されたか表す！
        
        # エラー表示中またはACボタン押下時の処理
        if self.result.value == "Error" or data == "AC":
            self.result.value = "0"  # 表示を0にリセット
            self.reset()  # 計算状態をリセット

        # 数字または小数点ボタンの処理
        elif data in ("1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "."):
            if self.result.value == "0" or self.new_operand == True:
                # 表示が0または新しい数値入力の場合は置き換え
                self.result.value = data
                self.new_operand = False  # 数値入力中フラグをオフに
            else:
                # 既に数値がある場合は追加
                self.result.value = self.result.value + data

# 演算子ボタン(+, -, *, /)の処理
        elif data in ("+", "-", "*", "/"):
            # 現在の数値と前に入力された数値で計算実行
            self.result.value = self.calculate(self.operand1, float(self.result.value), self.operator)
            self.operator = data  # 新しい演算子を保存
            
            if self.result.value == "Error":
                # エラー時の処理
                # ゼロ除算（10÷0）などでエラーが発生した場合、次の計算のために最初のオペランド（左側の数値）を0にリセット
                # これにより、エラー後も電卓を使い続けられる
                self.operand1 = "0"  
            else:
                # 正常計算時：計算結果を次の計算の最初のオペランドに設定、例えば「5+3=8」の後に「+」を押すと、次は「8+」から始まる
                self.operand1 = float(self.result.value)
                
            # 次の入力を新しいオペランド（右側の数値）として扱うフラグをONに
            self.new_operand = True
        # イコールボタンの処理
        elif data in ("="):
            # 最終計算を実行
            self.result.value = self.calculate(self.operand1, float(self.result.value), self.operator)
            self.reset()  # 計算状態をリセット

        # パーセントボタンの処理
        elif data in ("%"):
            # 現在の値を100で割る（パーセント化）
            self.result.value = float(self.result.value) / 100
            self.reset()  # 計算状態をリセット

        # 符号反転ボタンの処理
        elif data in ("+/-"):
            if float(self.result.value) > 0:
                # 正の数なら負の数にする
                self.result.value = "-" + str(self.result.value)
            elif float(self.result.value) < 0:
                # 負の数なら正の数にする
                self.result.value = str(self.format_number(abs(float(self.result.value))))

        # ここから追加した数学機能の処理を記述していく
        
        # 平方根ボタンの処理
        elif data == "sqrt":
            try:
                num = float(self.result.value)  # 文字列を数値に変換
                if num < 0:
                    self.result.value = "Error"  # 負の数の平方根はエラー
                else:
                    # 平方根を計算して表示（√x）
                    self.result.value = str(self.format_number(math.sqrt(num)))
            except:
                self.result.value = "Error"  # 変換や計算エラー時
        
        # 2乗ボタンの処理
        elif data == "^2":
            try:
                num = float(self.result.value)  # 文字列を数値に変換
                # 数値を2乗して表示（x²）
                self.result.value = str(self.format_number(num * num))
            except:
                self.result.value = "Error"  # 変換や計算エラー時
        
        # 逆数ボタンの処理
        elif data == "1/x":
            try:
                num = float(self.result.value)  # 文字列を数値に変換
                if num == 0:
                    self.result.value = "Error"  # 0の逆数はエラー（ゼロ除算）
                else:
                    # 逆数を計算して表示（1/x）
                    self.result.value = str(self.format_number(1 / num))
            except:
                self.result.value = "Error"  # 変換や計算エラー時
        
        # 指数関数ボタンの処理
        elif data == "exp":
            try:
                num = float(self.result.value)  # 文字列を数値に変換
                # e^xを計算して表示
                self.result.value = str(self.format_number(math.exp(num)))
            except:
                self.result.value = "Error"  # 変換や計算エラー時
        
        # 円周率ボタンの処理
        elif data == "π":
            # πの値を表示（約3.14159...）
            self.result.value = str(self.format_number(math.pi))
            self.new_operand = True  # 次の数値入力を新しい数として扱う

        # 画面を更新
        self.update()

    # 数値の表示形式を整える関数になっている
    def format_number(self, num):
        if num % 1 == 0:
            return int(num)  # 整数部分のみの場合は小数点以下を表示しない
        else:
            return num  # 小数点以下がある場合はそのまま表示

    # 計算実行関数 - 2つの数値と演算子から計算を行う
    def calculate(self, operand1, operand2, operator):
        # 足し算
        if operator == "+":
            return self.format_number(operand1 + operand2)
        # 引き算
        elif operator == "-":
            return self.format_number(operand1 - operand2)
        # 掛け算
        elif operator == "*":
            return self.format_number(operand1 * operand2)
        # 割り算（ゼロ除算チェック付き）
        elif operator == "/":
            if operand2 == 0:
                return "Error"  # ゼロで割るとエラー
            else:
                return self.format_number(operand1 / operand2)

    # 計算状態をリセットする関数
    def reset(self):
        self.operator = "+"  # 演算子をデフォルト（+）にリセット
        self.operand1 = 0    # 最初のオペランドを0にリセット
        self.new_operand = True  # 新しい数値入力モードをオンに


# メインアプリ実行関数
def main(page: ft.Page):
    page.title = "Simple Calculator"  # ウィンドウのタイトル設定
    calc = CalculatorApp()  # 電卓アプリのインスタンス作成
    page.add(calc)  # ページに電卓を追加


# アプリの実行開始
ft.app(main)  