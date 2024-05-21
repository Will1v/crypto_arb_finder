import websocket
import json
import os

class FeedHandler:
    def __init__(self, feed_url: str, cc_api_key: str):
        self.feed_url = feed_url
        self.cc_api_key = cc_api_key
        print(f"Init FH with feed_url = {feed_url} / cc_api_key = {cc_api_key}")

    def on_message(self, ws, message):
        data = json.loads(message)
        print("Received message:", data)

    def on_error(self, ws, error):
        print("Error:", error)

    def on_close(self, ws, close_status_code, close_msg):
        print("Connection closed")

    def on_open(self, ws):
        # Subscribe to the desired channels
        subscription_message = {
            "action": "SubAdd",
            "subs": [f"5~CCCAGG~{self.ccy_1}~{self.ccy_2}"]
        }
        print(f"Opening WS with: {subscription_message}")
        ws.send(json.dumps(subscription_message))

    def pull_live_data(self, ccy_1: str, ccy_2: str):
        self.ccy_1 = ccy_1
        self.ccy_2 = ccy_2
        ws_url = f"{self.feed_url}?api_key={self.cc_api_key}"

        # Initialize the WebSocket
        try:
            websocket.enableTrace(True)
            ws = websocket.WebSocketApp(ws_url,
                                        on_open=self.on_open,
                                        on_message=self.on_message,
                                        on_error=self.on_error,
                                        on_close=self.on_close)
            # Run the WebSocket
            ws.run_forever()

        except Exception as e:
            print(f"Exception occurred: {e}")
            if ws:
                ws.close()