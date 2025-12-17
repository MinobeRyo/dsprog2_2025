"""
API通信の基本機能を提供するモジュール
全てのAPI通信の基盤となるクラスを定義する！
"""

import requests
from utils.logger import log_request_info, log_error


class APIClient:
    """
    API通信の基本機能を提供するクラス
    エラーハンドリングとログ出力を標準で実装
    """
    
    def __init__(self, timeout=10):
        """
        APIClientの初期化
        
        Args
            timeout: リクエストのタイムアウト時間（秒）
        """
        self.timeout = timeout
        print(f"APIClient初期化完了（タイムアウト：{timeout}秒）")
    
    
    def get_json(self, url, log_detail=True):
        """
        指定されたURLからJSONデータを取得する
        
        Args:
            url: アクセスするAPIのURL
            log_detail: 詳細ログを出力するかどうか
            
        Returns:
            dict 取得したJSONデータ（辞書形式）
            None エラーが発生した場合
        """
        try:
            print(f"\n📡 APIにリクエスト送信中 {url}")
            
            # HTTPリクエストを送信
            response = requests.get(url, timeout=self.timeout)
            
            # レスポンスのエンコーディングを設定
            response.encoding = response.apparent_encoding
            
            # 詳細ログを出力
            if log_detail:
                log_request_info(response)
            
            # ステータスコードが200番台でない場合はエラー
            response.raise_for_status()
            
            # JSONデータを取得して返す
            json_data = response.json()
            print(f"✅ データ取得成功（データサイズ：{len(str(json_data))} bytes）")
            return json_data
            
        except requests.exceptions.Timeout:
            # タイムアウトエラー
            error_msg = f"タイムアウトエラー：{self.timeout}秒以内にレスポンスがありませんでした"
            log_error(error_msg)
            return None
            
        except requests.exceptions.ConnectionError as e:
            # 接続エラー
            error_msg = "接続エラー：インターネット接続を確認してください"
            log_error(error_msg, e)
            return None
            
        except requests.exceptions.HTTPError as e:
            # HTTPエラー（404, 500など）
            error_msg = f"HTTPエラー：ステータスコード {response.status_code}"
            log_error(error_msg, e)
            return None
            
        except requests.exceptions.JSONDecodeError as e:
            # JSON解析エラー
            error_msg = "JSONデータの解析に失敗しました"
            log_error(error_msg, e)
            return None
            
        except Exception as e:
            # その他の予期しないエラー
            error_msg = "予期しないエラーが発生しました"
            log_error(error_msg, e)
            return None