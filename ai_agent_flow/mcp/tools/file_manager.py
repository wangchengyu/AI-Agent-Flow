import os

class FileManager:
    def __init__(self):
        pass
        
    def list_files(self, path='.'):
        """列出指定路径下的文件"""
        try:
            files = os.listdir(path)
            return {'status': 'success', 'files': files}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
            
    def read_file(self, file_path):
        """读取指定文件的内容"""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            return {'status': 'success', 'content': content}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}