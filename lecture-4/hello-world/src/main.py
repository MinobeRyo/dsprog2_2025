import flet as ft

def main(page: ft.Page):
    #カウンター表示用テキスト
    counter = ft.Text("0", size=50, data=0)
    #ボタンクリック時に呼び出す関数
    def increment_click(e):
        counter.data += 1
        counter.value = str(counter.data)
        counter.update()
    #カウンターを減らすボタンの関数を追加
    def decrement_click(e):
        counter.data -= 1
        counter.value = str(counter.data)
        counter.update()

    #カウンターを増やすボタンを追加
    page.floating_action_button = ft.FloatingActionButton(icon=ft.Icons.ADD, on_click=increment_click)
 
    

    #sefeareaで囲んでカウンターを中央配置
    page.add(
        ft.SafeArea(
            ft.Container(
                counter,
                alignment=ft.alignment.center,
            ),
            expand=True,
        ),
        ft.FloatingActionButton(icon=ft.Icons.REMOVE, on_click=decrement_click, )
    )
ft.app(main)
