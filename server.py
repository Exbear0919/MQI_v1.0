# -*- coding: utf-8 -*-
"""本地服务器：提供指标管理API + 自动重建HTML"""
import http.server
import socketserver
import json
import os
import subprocess
import sys

PORT = 8898
BASE = os.path.dirname(os.path.abspath(__file__))
JSON_FILE = os.path.join(BASE, 'indicators_clean.json')

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=BASE, **kwargs)

    def do_POST(self):
        if self.path == '/api/rebuild':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()

            try:
                result = subprocess.run(
                    [sys.executable, 'build_html.py'],
                    cwd=BASE,
                    capture_output=True, text=True, encoding='utf-8'
                )
                if result.returncode == 0:
                    self.wfile.write(json.dumps({'ok': True, 'msg': 'HTML 重建成功！刷新页面查看。'}).encode('utf-8'))
                else:
                    self.wfile.write(json.dumps({'ok': False, 'msg': result.stderr or result.stdout}).encode('utf-8'))
            except Exception as e:
                self.wfile.write(json.dumps({'ok': False, 'msg': str(e)}).encode('utf-8'))
            return

        if self.path == '/api/save':
            try:
                length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(length).decode('utf-8')
                data = json.loads(body)
                with open(JSON_FILE, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({'ok': True}).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({'ok': False, 'msg': str(e)}).encode('utf-8'))
            return

        self.send_response(404)

    def log_message(self, format, *args):
        print(f"[{self.log_date_time_string()}] {format % args}")

if __name__ == '__main__':
    print(f"管理服务器启动: http://localhost:{PORT}/management.html")
    print("按 Ctrl+C 停止")
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        httpd.serve_forever()
