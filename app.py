import os
import json
import pandas as pd
from flask import Flask, render_template, request, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from io import BytesIO

app = Flask(__name__)

# 配置 SQLite 数据库 (无需安装，会自动创建文件)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///contacts.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- 数据库模型 (对应需求 1.1, 1.2) ---
class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    # 需求 1.1: 收藏标记 (0=普通, 1=收藏)
    is_favorite = db.Column(db.Boolean, default=False)
    # 需求 1.2: 存储多种联系方式，使用 JSON 字符串存储 (例如: [{"type":"手机","val":"123"}, ...])
    details = db.Column(db.Text, default='[]')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'is_favorite': self.is_favorite,
            'details': json.loads(self.details)
        }

# 初始化数据库
with app.app_context():
    db.create_all()

# --- 路由逻辑 ---

@app.route('/')
def index():
    return render_template('index.html')

# 获取所有联系人接口
@app.route('/api/contacts')
def get_contacts():
    # 支持只看收藏 (需求 1.1)
    only_fav = request.args.get('favorite')
    query = Contact.query
    if only_fav == 'true':
        query = query.filter_by(is_favorite=True)
    
    contacts = query.order_by(Contact.is_favorite.desc(), Contact.id.desc()).all()
    return jsonify([c.to_dict() for c in contacts])

# 添加联系人 (需求 1.2)
@app.route('/api/add', methods=['POST'])
def add_contact():
    data = request.json
    new_contact = Contact(
        name=data['name'],
        details=json.dumps(data.get('details', [])), # 将列表转为 JSON 字符串存入库
        is_favorite=False
    )
    db.session.add(new_contact)
    db.session.commit()
    return jsonify({'success': True})

# 切换收藏状态 (需求 1.1)
@app.route('/api/toggle_fav/<int:id>', methods=['POST'])
def toggle_fav(id):
    contact = Contact.query.get(id)
    if contact:
        contact.is_favorite = not contact.is_favorite
        db.session.commit()
    return jsonify({'success': True})

# 删除联系人
@app.route('/api/delete/<int:id>', methods=['POST'])
def delete_contact(id):
    contact = Contact.query.get(id)
    if contact:
        db.session.delete(contact)
        db.session.commit()
    return jsonify({'success': True})

# --- Excel 导入导出 (需求 1.3) ---

@app.route('/api/export')
def export_excel():
    contacts = Contact.query.all()
    data_list = []
    
    # 将 JSON 展开，简单的做法是把所有信息拼成字符串，
    # 或者如果你想每一种联系方式一列，逻辑会复杂点。这里采用通用的“展开逻辑”。
    for c in contacts:
        row = {'姓名': c.name, '是否收藏': '是' if c.is_favorite else '否'}
        details = json.loads(c.details)
        # 将联系方式动态加入列中 (例如: 手机: 12345)
        for item in details:
            # 防止列名重复，简单的处理
            key = item['type']
            if key in row:
                row[key] += f"; {item['val']}"
            else:
                row[key] = item['val']
        data_list.append(row)

    df = pd.DataFrame(data_list)
    output = BytesIO()
    # 写入 Excel
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
        # 读取 Excel，处理空值为 空字符串
        df = pd.read_excel(file).fillna('')
        
        for _, row in df.iterrows():
            name = row.get('姓名', '未知联系人')
            is_fav = True if row.get('是否收藏') == '是' else False
            
            # 动态解析剩余列作为联系方式
            details = []
            for col in df.columns:
                if col not in ['姓名', '是否收藏'] and row[col]:
                    details.append({'type': col, 'val': str(row[col])})
            
            new_contact = Contact(
                name=name,
                is_favorite=is_fav,
                details=json.dumps(details)
            )
            db.session.add(new_contact)
        
        db.session.commit()
        return jsonify({'success': True, 'count': len(df)})
    except Exception as e:
        return jsonify({'success': False, 'msg': str(e)})

if __name__ == '__main__':
    # 启动应用
    app.run(debug=True, port=5000)