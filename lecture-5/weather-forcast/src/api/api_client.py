"""
API通信の基本機能を提供するモジュール
全てのAPI通信の基盤となるクラスを定義する！
"""

import requests
import time
import json as json_lib


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
    
    
    def get(self, url, params=None, headers=None):
        """
        指定されたURLからHTTP GETリクエストを送信する
        WeatherAPIクラスとの互換性のために追加
        
        Args:
            url: リクエスト先URL
            params: URLパラメータ (optional)
            headers: HTTPヘッダー (optional)
            
        Returns:
            requests.Response オブジェクト
            None エラーが発生した場合
        """
        try:
            print(f"\n📡 API GETリクエスト送信中 {url}")
            
            # HTTPリクエストを送信
            response = requests.get(
                url, 
                params=params,
                headers=headers,
                timeout=self.timeout
            )
            
            # レスポンスのエンコーディングを設定
            response.encoding = response.apparent_encoding
            
            # リクエスト情報をログとして出力
            self._log_request_info(response)
            
            # ステータスチェック（例外は発生させない）
            if response.status_code >= 400:
                print(f"⚠️ HTTPエラー：ステータスコード {response.status_code}")
            else:
                print(f"✅ リクエスト成功：ステータスコード {response.status_code}")
            
            return response
            
        except requests.exceptions.Timeout:
            # タイムアウトエラー
            error_msg = f"⚠️ タイムアウトエラー：{self.timeout}秒以内にレスポンスがありませんでした"
            self._log_error(error_msg)
            return None
            
        except requests.exceptions.ConnectionError as e:
            # 接続エラー
            error_msg = "⚠️ 接続エラー：インターネット接続を確認してください"
            self._log_error(error_msg, e)
            return None
            
        except Exception as e:
            # その他の予期しないエラー
            error_msg = "⚠️ 予期しないエラーが発生しました"
            self._log_error(error_msg, e)
            return None
    
    
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
                self._log_request_info(response)
            
            # ステータスコードが200番台でない場合はエラー
            response.raise_for_status()
            
            # JSONデータを取得して返す
            json_data = response.json()
            print(f"✅ データ取得成功（データサイズ：{len(str(json_data))} bytes）")
            return json_data
            
        except requests.exceptions.Timeout:
            # タイムアウトエラー
            error_msg = f"⚠️ タイムアウトエラー：{self.timeout}秒以内にレスポンスがありませんでした"
            self._log_error(error_msg)
            return None
            
        except requests.exceptions.ConnectionError as e:
            # 接続エラー
            error_msg = "⚠️ 接続エラー：インターネット接続を確認してください"
            self._log_error(error_msg, e)
            return None
            
        except requests.exceptions.HTTPError as e:
            # HTTPエラー（404, 500など）
            error_msg = f"⚠️ HTTPエラー：ステータスコード {response.status_code}"
            self._log_error(error_msg, e)
            return None
            
        except requests.exceptions.JSONDecodeError as e:
            # JSON解析エラー
            error_msg = "⚠️ JSONデータの解析に失敗しました"
            self._log_error(error_msg, e)
            return None
            
        except Exception as e:
            # その他の予期しないエラー
            error_msg = "⚠️ 予期しないエラーが発生しました"
            self._log_error(error_msg, e)
            return None
    
    
    def post(self, url, data=None, json=None, headers=None):
        """
        POSTリクエストを送信する
        
        Args:
            url: リクエスト先URL
            data: フォームデータ (optional)
            json: JSONデータ (optional)
            headers: HTTPヘッダー (optional)
            
        Returns:
            requests.Response オブジェクト
            None エラーが発生した場合
        """
        try:
            print(f"\n📡 API POSTリクエスト送信中 {url}")
            
            # HTTPリクエストを送信
            response = requests.post(
                url,
                data=data,
                json=json,
                headers=headers,
                timeout=self.timeout
            )
            
            # レスポンスのエンコーディングを設定
            response.encoding = response.apparent_encoding
            
            # リクエスト情報をログとして出力
            self._log_request_info(response)
            
            # ステータスチェック
            if response.status_code >= 400:
                print(f"⚠️ HTTPエラー：ステータスコード {response.status_code}")
            else:
                print(f"✅ リクエスト成功：ステータスコード {response.status_code}")
                
            return response
            
        except requests.exceptions.Timeout:
            # タイムアウトエラー
            error_msg = f"⚠️ タイムアウトエラー：{self.timeout}秒以内にレスポンスがありませんでした"
            self._log_error(error_msg)
            return None
            
        except requests.exceptions.ConnectionError as e:
            # 接続エラー
            error_msg = "⚠️ 接続エラー：インターネット接続を確認してください"
            self._log_error(error_msg, e)
            return None
            
        except Exception as e:
            # その他の予期しないエラー
            error_msg = "⚠️ 予期しないエラーが発生しました"
            self._log_error(error_msg, e)
            return None
    
    
    def _log_request_info(self, response):
        """
        HTTPリクエスト/レスポンス情報をログとして出力する
        
        Args:
            response: requests.Responseオブジェクト
        """
        req = response.request
        
        # リクエスト情報
        print(f"📤 リクエスト: {req.method} {req.url}")
        if len(req.headers) > 0:
            print("📤 リクエストヘッダー:")
            for key, value in req.headers.items():
                print(f"   {key}: {value}")
        
        # レスポンス情報
        print(f"📥 レスポンス: {response.status_code} {response.reason}")
        if len(response.headers) > 0:
            print("📥 レスポンスヘッダー:")
            for key, value in response.headers.items():
                print(f"   {key}: {value}")
    
    
    def _log_error(self, message, exception=None):
        """
        エラー情報をログとして出力する
        
        Args:
            message: エラーメッセージ
            exception: 例外オブジェクト (optional)
        """
        print(message)
        if exception:
            print(f"エラー詳細: {str(exception)}")
            
        # エラーのスタックトレースを出力（デバッグ時に役立つ）
        # import traceback
        # traceback.print_exc()