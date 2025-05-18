上海理工大学学报智能管理系统
项目概述
《上海理工大学学报》智能管理系统是一个基于 Django 框架开发的学术期刊管理平台，旨在实现学术稿件的提交、审稿、编辑、出版和数据分析全流程的自动化管理。该系统支持多角色用户（投稿人、审稿人、编辑、管理员），提供编号设计、通知中心、数据可视化等功能，确保稿件管理的唯一性、可追溯性和高效性。
主要功能

用户管理：支持投稿人、审稿人、编辑和管理员的注册、权限分配和资料管理。
稿件管理：实现稿件提交、状态跟踪（草稿、已提交、外审中、需要修改、已修改、已接受、已拒绝、初审拒绝、已发表）、文件上传和下载。
审稿流程：支持审稿人邀请、评审表提交、编辑初审和终审，自动分配审稿任务。
通知中心：为投稿、审稿邀请、审稿提醒、修改要求、录用、退稿、出版等动作生成实时通知。
出版管理：支持卷期创建、稿件排版、目录生成和 DOI 分配。
数据分析：提供投稿趋势（折线图）、领域分布（饼图）等可视化报表，支持 PDF 和 CSV 导出。
编号设计：为稿件、用户、审稿任务、通知、卷期、出版、报表和日志生成唯一编号（如 MS20250001、AU-250430-001）。
系统日志：记录用户操作和错误日志，支持问题排查。

技术栈

后端：Django 4.x, Python 3.8+
前端：Bootstrap 5, Chart.js（数据可视化）
数据库：SQLite（开发环境），支持 PostgreSQL/MySQL（生产环境）
文件存储：Django FileField（稿件文件、报表等）
依赖管理：pip, requirements.txt

安装步骤
1. 环境准备
确保已安装以下工具：

Python 3.8 或更高版本
pip（Python 包管理器）
Git（版本控制）

2. 克隆项目
git clone https://github.com/lyp0746/usst-journal-system.git
cd usst-journal-system

3. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows 使用: venv\Scripts\activate

4. 安装依赖
pip install -r requirements.txt

5. 配置环境变量
复制 .env.example 为 .env，并根据需要修改配置（如数据库、密钥）：
SECRET_KEY=your-secret-key
DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3

6. 数据库迁移
python manage.py makemigrations
python manage.py migrate

7. 创建超级用户
python manage.py createsuperuser

8. 运行开发服务器
python manage.py runserver

访问 http://127.0.0.1:8000 查看系统。
使用说明
1. 用户角色与功能

投稿人：
登录后访问 /accounts/dashboard/ 查看稿件列表。
提交新稿件：/manuscripts/submission/。
查看通知：/notifications/list/。


审稿人：
接受审稿邀请：/review_process/invitation_list/。
提交评审表：/review_process/review_form/{manuscript_id}/。


编辑：
初审稿件：/editor/initial_review/{manuscript_id}/。
分配审稿人：/editor/assign_reviewer/{manuscript_id}/。
管理卷期：/publication/volume_list/。


管理员：
查看系统概览：/admin_management/dashboard/。
管理用户：/admin_management/user_list/。
查看错误日志：/admin_management/error_logs/。



2. 编号设计
系统为各模块生成唯一编号，确保数据可追溯：

稿件：MS{YYYY}{4位序号}（如 MS20250001）
用户：AU-/RV-/ED-{YYMMDD}-{NNN}（如 AU-250430-001）
审稿任务：RA-{MSID}-{RVID}-{S}（如 RA-20250001-250430001-I）
通知：NT-{YYMMDD}-{TYPE}-{NNN}（如 NT-250430-SUB-001）
卷期：VOL-{YY}-{NN}（如 VOL-25-01）
出版：PUB-{MSID}-P{NNN}（如 PUB-20250001-P001）
报表：RPT-{YYMMDD}-{TYPE}-{NNN}（如 RPT-250430-SUB-001）
日志：LOG-{YYMMDD}-{HHMMSS}-{TYPE}（如 LOG-250430-143025-INFO）
DOI：10.1000/MS{YYYY}{4位序号}（如 10.1000/MS20250001）

3. 数据分析
访问 /analytics/report_generate/ 查看：

投稿趋势：折线图展示月度投稿量。
领域分布：饼图展示研究领域占比（如 CS 35%、EE 30%）。
导出报表：支持 PDF 和 CSV 格式。

测试指引
1. 生成测试数据
运行测试数据生成脚本以填充数据库：
python populate_test_data.py

生成内容：

10 名投稿人、10 名审稿人、1 名编辑、1 名管理员
20 篇稿件，覆盖所有状态
通知、审稿任务、卷期、出版记录和报表日志

2. 测试账号

投稿人：author1 - author10（密码：test123）
审稿人：reviewer1 - reviewer10（密码：test123）
编辑：editor1（密码：test123）
管理员：admin（密码：admin123）

3. 测试流程
投稿人

登录 author1，访问 /accounts/dashboard/，验证用户编号（如 AU-250430-001）和稿件列表。
提交新稿件：/manuscripts/submission/，验证通知（如 NT-250430-SUB-001）。
查看稿件详情：/manuscripts/detail/MS20250001/，验证 DOI 和状态。

审稿人

登录 reviewer1，验证审稿任务编号（如 RA-20250001-250430001-I）。
接受邀请并提交评审表：/review_process/review_form/MS20250001/。

编辑

登录 editor1，进行初审：/editor/initial_review/MS20250001/。
分配审稿人：/editor/assign_reviewer/MS20250001/。
查看卷期：/publication/volume_list/，验证编号（如 VOL-25-01）。

管理员

登录 admin，查看系统日志：/admin_management/error_logs/，验证日志编号（如 LOG-250430-143025-INFO）。
查看数据分析：/analytics/report_generate/，验证报表编号（如 RPT-250430-SUB-001）。

4. 验收标准

所有编号生成正确，格式符合设计规则。
通知中心显示所有动作的通知（如投稿、审稿邀请、录用）。
数据分析图表反映投稿趋势和领域分布。
全流程（投稿→审稿→编辑→出版）运行顺畅，无 404 错误。

常见问题

数据库迁移失败：删除 migrations/ 文件（保留 __init__.py），重新运行 makemigrations 和 migrate。
编号重复：检查模型的 save 方法，确保计数逻辑正确。
图表不显示：验证 analytics/views.py 中的查询逻辑，确保 Chart.js 正确加载。
通知缺失：检查 populate_test_data.py 中的通知生成逻辑，验证 Notification 模型的保存。

贡献指南
欢迎为项目贡献代码！请遵循以下步骤：

Fork 项目并克隆到本地。
创建新分支：git checkout -b feature/your-feature。
提交更改：git commit -m "添加新功能：描述"。
推送分支：git push origin feature/your-feature。
提交 Pull Request，说明更改内容。

代码规范

遵循 PEP 8（Python 代码规范）。
使用 Django 模板语法，避免硬编码。
为新功能编写测试用例（位于 tests/ 目录）。

联系方式

项目负责人：上海理工大学学报编辑部
邮箱：journal@usst.edu.cn
问题反馈：请在 GitHub Issues 中提交 bug 或建议。

