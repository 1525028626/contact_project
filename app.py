import os
import json
import pandas as pd
from flask import Flask, render_template, request, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_  # [新增] 用于多条件查询
from io import BytesIO

app = Flask(__name__)

# --- 核心修改：智能数据库配置 ---
# 1. 尝试获取云端数据库地址
database_url = os.environ.get("POSTGRES_URL")

if database_url:
    # 适配 Vercel Postgres 的连接头
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    print("✅ 使用云端数据库 (Postgres)")
else:
    # 2. 如果没有配置云端数据库
    if os.environ.get('VERCEL'):
        # 在 Vercel 环境下，强制使用 /tmp 目录（防止 500 只读错误）
        print("⚠️ 未检测到数据库配置，使用临时文件系统 /tmp")
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/contacts.db'
    else:
        # 本地开发环境，正常使用当前目录
        print("💻 本地开发模式")
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///contacts.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- 数据库模型 ---
class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    is_favorite = db.Column(db.Boolean, default=False)
    details = db.Column(db.Text, default='[]')

    def to_dict(self):
        try:
            details_json = json.loads(self.details) if self.details else []
        except:
            details_json = []
        return {
            'id': self.id,
            'name': self.name,
            'is_favorite': self.is_favorite,
            'details': details_json
        }

# 初始化数据库
with app.app_context():
    try:
        db.create_all()
        print("✅ 数据库初始化成功")
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")

# --- 路由逻辑 ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/contacts')
def get_contacts():
    only_fav = request.args.get('favorite')
    search_query = request.args.get('q') # [新增] 获取搜索参数
    
    query = Contact.query
    
    # [新增] 搜索逻辑
    if search_query:
        # 在姓名或详情JSON字符串中查找
        query = query.filter(
            or_(
                Contact.name.contains(search_query),
                Contact.details.contains(search_query)
            )
        )

    if only_fav == 'true':
        query = query.filter_by(is_favorite=True)
        
    contacts = query.order_by(Contact.is_favorite.desc(), Contact.id.desc()).all()
    return jsonify([c.to_dict() for c in contacts])

@app.route('/api/add', methods=['POST'])
def add_contact():
    data = request.json
    new_contact = Contact(
        name=data['name'],
        details=json.dumps(data.get('details', [])),
        is_favorite=False
    )
    db.session.add(new_contact)
    db.session.commit()
    return jsonify({'success': True})

# [新增] 更新联系人接口
@app.route('/api/update/<int:id>', methods=['POST'])
def update_contact(id):
    contact = Contact.query.get(id)
    if not contact:
        return jsonify({'success': False, 'msg': '联系人不存在'})
    
    data = request.json
    contact.name = data['name']
    contact.details = json.dumps(data.get('details', [])) # 更新详情
    
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/toggle_fav/<int:id>', methods=['POST'])
def toggle_fav(id):
    contact = Contact.query.get(id)
    if contact:
        contact.is_favorite = not contact.is_favorite
        db.session.commit()
    return jsonify({'success': True})

@app.route('/api/delete/<int:id>', methods=['POST'])
def delete_contact(id):
    contact = Contact.query.get(id)
    if contact:
        db.session.delete(contact)
        db.session.commit()
    return jsonify({'success': True})

@app.route('/api/export')
def export_excel():
    contacts = Contact.query.all()
    data_list = []
    for c in contacts:
        row = {'姓名': c.name, '是否收藏': '是' if c.is_favorite else '否'}
        try:
            details = json.loads(c.details)
        except:
            details = []
        for item in details:
            key = item.get('type', '其他')
            row[key] = row.get(key, '') + f" {item.get('val', '')}"
        data_list.append(row)

    if not data_list:
        df = pd.DataFrame(columns=['姓名', '是否收藏'])
    else:
        df = pd.DataFrame(data_list)
        
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='通讯录')
    output.seek(0)
    return send_file(output, download_name="contacts.xlsx", as_attachment=True)

@app.route('/api/import', methods=['POST'])
def import_excel():
    file = request.files.get('file')
    if not file:
        return jsonify({'success': False, 'msg': '没有文件'})
    try:
        df = pd.read_excel(file).fillna('')
        for _, row in df.iterrows():
            name = row.get('姓名', '未知')
            is_fav = (row.get('是否收藏') == '是')
            details = []
            for col in df.columns:
                if col not in ['姓名', '是否收藏'] and row[col]:
                    details.append({'type': col, 'val': str(row[col])})
            
            db.session.add(Contact(name=name, is_favorite=is_fav, details=json.dumps(details)))
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'msg': str(e)})

if __name__ == '__main__':
    app.run(debug=True, port=5000)