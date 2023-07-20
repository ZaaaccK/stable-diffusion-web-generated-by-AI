from flask import Flask, render_template, request, jsonify,session,redirect,url_for
import requests
import os
import base64
import random
import string
from datetime import date
from PIL import Image
from io import BytesIO
import json
import hashlib
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

@app.route('/')
def index():
    if 'username' in session:
        username = session['username']
        return render_template('index.html', username=username)
    else:
        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    elif request.method == 'POST':
        data = request.get_json()

        # 读取 userlist.json
        try:
            with open('data/userlist.json', 'r') as f:
                userlist = json.load(f)
        except FileNotFoundError:
            return {'code': 2, 'message': '用户不存在'}

        # 判断用户名是否存在
        if data['username'] not in userlist:
            return {'code': 2, 'message': '用户不存在'}

        # 判断密码是否正确
        password = data['password']
        hashed_password = hashlib.md5(password.encode()).hexdigest()
        if hashed_password == userlist[data['username']]['password']:
            # 登录成功，设置 Session
            session['username'] = data['username']
            return {'code': 1, 'message': '用户登录成功'}
        else:
            return {'code': 3, 'message': '密码错误'}


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    elif request.method == 'POST':
        data = request.get_json()

        # 获取传入的 JSON 数据中的用户名和密码
        username = data.get('username')
        password = data.get('password')

        # 加载用户列表
        try:
            with open('data/userlist.json', 'r') as file:
                userlist = json.load(file)
        except FileNotFoundError:
            userlist = {}

        # 检查用户名是否已存在
        if username in userlist:
            response_data = {
                'code': 2,
                'message': '用户已存在'
            }
        else:
            # 对密码进行 MD5 加密
            password_hash = hashlib.md5(password.encode()).hexdigest()

            # 添加新用户到用户列表
            userlist[username] = {
                'username': username,
                'password': password_hash
            }

            # 更新用户列表文件
            with open('data/userlist.json', 'w') as file:
                json.dump(userlist, file)

            response_data = {
                'code': 1,
                'message': '注册成功'
            }

        return jsonify(response_data)

@app.route('/imglist')
def imglist():
    imglist_json_path = os.path.join('data', 'imglist.json')
    if os.path.exists(imglist_json_path):
        with open(imglist_json_path, 'r') as f:
            imglist_data = json.load(f)
    else:
        imglist_data = []

    return render_template('imglist.html', imglist=imglist_data)

@app.route('/txt2img', methods=['POST'])
def txt2img():
    data = request.get_json()
    url = 'http://43.159.53.163:7860/sdapi/v1/txt2img'

    response = requests.post(url, json=data)
    result = response.json()

    # 获取今天的日期
    today = date.today().strftime('%Y-%m-%d')

    # 创建以今天日期命名的文件夹
    folder_path = os.path.join('static', today)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    imglist = []

    # 遍历 images 列表并保存为 PNG 图片
    for i, img_base64 in enumerate(result['images']):
        img_data = base64.b64decode(img_base64)
        img = Image.open(BytesIO(img_data))

        # 生成随机文件名
        filename = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
        img_path = os.path.join(folder_path, f'{filename}.png')
        img.save(img_path, 'PNG')

        # 构建要添加到 imglist.json 的字典
        img_dict = {
            'imgurl': img_path,
            'date': today
        }

        # 将图片路径添加到 imglist 中
        imglist.append(img_dict)

    # 将新生成的字典合并到原有数据中
    imglist_json_path = os.path.join('data', 'imglist.json')
    if os.path.exists(imglist_json_path):
        with open(imglist_json_path, 'r') as f:
            existing_data = json.load(f)
        existing_data.extend(imglist)
    else:
        existing_data = imglist

    # 将合并后的数据写入 imglist.json 文件
    with open(imglist_json_path, 'w') as f:
        json.dump(existing_data, f)

    # 返回生成成功的响应
    response_data = {
        'code': 1,
        'message': '图片生成成功',
        'imglist': [img['imgurl'] for img in imglist]
    }
    return jsonify(response_data)

if __name__ == '__main__':
    app.run(debug=True, port=8888,host='0.0.0.0')
