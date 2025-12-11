# 通讯录管理系统

一个基于Flask开发的简单易用的通讯录管理系统，支持联系人的增删改查、收藏标记和Excel导入导出功能。

## 功能特性

- 📋 **联系人管理**：添加、查看、删除联系人
- ⭐ **收藏功能**：标记常用联系人
- 📱 **多联系方式**：支持存储多种类型的联系方式（手机、邮箱、地址等）
- 📊 **Excel导入导出**：支持批量导入导出联系人数据
- 💾 **数据持久化**：使用SQLite数据库存储数据

## 技术栈

- **后端框架**：Flask
- **数据库ORM**：SQLAlchemy
- **数据库**：SQLite（可扩展为其他关系型数据库）
- **前端**：HTML/CSS/JavaScript（使用原生技术，无需额外框架）
- **Excel处理**：Pandas + Openpyxl


## 快速开始

### 1. 安装依赖

```bash
# 安装项目依赖
pip install flask flask_sqlalchemy pandas openpyxl
```

### 2. 运行项目

```bash
# 启动应用
python app.py
```


## 使用说明

### 添加联系人

1. 点击"添加联系人"按钮
2. 输入姓名
3. 点击"添加联系方式"添加需要的联系方式类型和值
4. 点击"保存"完成添加

### 收藏联系人

点击联系人卡片上的⭐图标，即可将联系人标记为收藏。再次点击可取消收藏。

### 查看收藏联系人

点击页面顶部的"只看收藏"按钮，可以筛选出所有收藏的联系人。

### 删除联系人

点击联系人卡片上的🗑️图标，即可删除该联系人。

### 导入/导出数据

- **导出**：点击页面顶部的"导出Excel"按钮，即可将所有联系人导出为Excel文件
- **导入**：点击页面顶部的"导入Excel"按钮，选择符合格式的Excel文件进行批量导入

## 云端部署

### 华为云部署

#### 方式一：弹性Web托管（Web+）

1. 准备项目代码包（包含app.py、requirements.txt和templates文件夹）
2. 在华为云控制台创建弹性Web托管环境
3. 上传代码包并配置启动命令
4. 配置环境变量和数据库连接
5. 完成部署并访问应用

#### 方式二：弹性云服务器（ECS）

1. 创建ECS实例并连接
2. 安装Python环境和依赖
3. 部署应用并配置Gunicorn
4. 配置Nginx反向代理
5. 配置系统服务确保应用持续运行

### 数据库扩展

生产环境建议使用华为云RDS服务，支持PostgreSQL或MySQL，修改`app.py`中的数据库配置即可：

```python
# 使用华为云RDS PostgreSQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://username:password@hostname:5432/database_name'
```

## 数据库设计

### 联系人表（Contact）

| 字段名 | 类型 | 描述 |
|--------|------|------|
| id | Integer | 主键ID |
| name | String | 联系人姓名 |
| is_favorite | Boolean | 是否收藏 |
| details | Text | 联系方式（JSON格式） |

### 联系方式格式

```json
[
  {"type": "手机", "val": "13800138000"},
  {"type": "邮箱", "val": "example@example.com"},
  {"type": "地址", "val": "北京市朝阳区"}
]
```

## API接口

| 接口路径 | 方法 | 功能 |
|---------|------|------|
| / | GET | 访问主页面 |
| /api/contacts | GET | 获取联系人列表 |
| /api/add | POST | 添加联系人 |
| /api/toggle_fav/<id> | POST | 切换收藏状态 |
| /api/delete/<id> | POST | 删除联系人 |
| /api/export | GET | 导出Excel |
| /api/import | POST | 导入Excel |

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！

