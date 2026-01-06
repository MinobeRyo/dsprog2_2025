"""
ログ出力用のユーティリティモジュール
APIのリクエスト/レスポンス情報を詳細に表示する
"""

def log_request_info(response):
    """
    HTTPリクエストとレスポンスの詳細情報をコンソールに出力する
    
    Args:
        response: requestsライブラリのResponseオブジェクト
    """
    print("\n" + "="*60)
    print("【レスポンス情報】")
    print("="*60)
    print(f"レスポンス：{response}")
    print(f"レスポンスの型：{type(response)}")
    print(f"ステータスコード：{response.status_code}")
    print(f"ステータスメッセージ：{response.reason}")
    
    print("\n" + "="*60)
    print("【リクエスト情報】")
    print("="*60)
    print(f"リクエスト：{response.request}")
    print(f"リクエストの型：{type(response.request)}")
    print(f"リクエストヘッダー：{response.request.headers}")
    print(f"リクエストメソッド：{response.request.method}")
    print(f"リクエストURL：{response.request.url}")
    print("="*60 + "\n")


def log_error(error_message, exception=None):
    """
    エラー情報をコンソールに出力する
    
    Args
        error_message: エラーメッセージ
        exception: 例外オブジェクト（オプション）
    """
    print("\n" + "!"*60)
    print("【エラー】")
    print("!"*60)
    print(f"エラーメッセージ：{error_message}")
    if exception:
        print(f"例外の型：{type(exception)}")
        print(f"例外の詳細：{exception}")
    print("!"*60 + "\n")