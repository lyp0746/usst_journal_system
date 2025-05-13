# 确保脚本在正确的Django环境中运行
import os

from django.db.models import F

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "usst_journal_system.settings")
import django

django.setup()
import random
from datetime import datetime, timedelta
from django.contrib.auth.models import User
from django.utils import timezone
from accounts.models import UserProfile, Role, UserRole, ResearchField
from manuscripts.models import Manuscript, ManuscriptType
from notifications.models import Notification
from review_process.models import ReviewerProfile, ReviewAssignment, ReviewForm
from publication.models import Volume, Issue, ManuscriptPublication
from django.core.files.uploadedfile import SimpleUploadedFile
from admin_management.models import SystemLog


def clear_database():
    """清空数据库中的测试数据"""
    print("清空数据库...")
    User.objects.all().delete()
    ResearchField.objects.all().delete()
    ManuscriptType.objects.all().delete()
    Manuscript.objects.all().delete()
    Volume.objects.all().delete()
    Notification.objects.all().delete()
    SystemLog.objects.all().delete()
    # 添加清空ReviewForm
    ReviewForm.objects.all().delete()


def create_research_fields():
    """创建研究领域"""
    print("创建研究领域...")
    fields = [
        ('MECH', '机械工程'),
        ('MAT', '材料科学'),
        ('CS', '计算机科学'),
        ('EE', '电子工程'),
        ('BIO', '生物医学工程')
    ]
    for code, name in fields:
        ResearchField.objects.get_or_create(code=code, name=name, is_active=True)


def create_roles():
    """创建用户角色"""
    print("创建用户角色...")
    roles = [
        ('Author', '投稿人'),
        ('Reviewer', '审稿人'),
        ('Editor', '编辑'),
        ('Admin', '管理员'),
    ]
    for name, desc in roles:
        Role.objects.get_or_create(name=name, description=desc)


def create_users():
    """创建用户（管理员、作者、审稿人和编辑）"""
    print("创建用户...")
    # 常用机构列表
    institutions = ["上海理工大学", "同济大学", "复旦大学", "上海交通大学", "华东师范大学", "东华大学"]

    # 创建管理员
    admin = User.objects.create_superuser(
        username='admin',
        password='admin123',
        email='admin@example.com'
    )
    UserProfile.objects.create(
        user=admin,
        full_name='管理员',
        institution='上海理工大学',
        title='系统管理员',
        email='admin@example.com',
        phone='+8612345678901',
        orcid='0000-0001-2345-6789'
    )
    UserRole.objects.create(user=admin, role=Role.objects.get(name='Admin'))

    # 创建投稿人（10人）
    for i in range(1, 11):
        user = User.objects.create_user(
            username=f'author{i}',
            password='test123',
            email=f'author{i}@example.com'
        )
        profile = UserProfile.objects.create(
            user=user,
            full_name=f'投稿人{i}',
            institution=random.choice(institutions),
            title=random.choice(["教授", "副教授", "讲师", "研究员"]),
            email=f'author{i}@example.com',
            phone=f'+86138{random.randint(10000000, 99999999)}',
            orcid=f'0000-000{i}-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}'
        )
        # 为每个作者随机选择2个研究领域
        selected_fields = random.sample([f.code for f in ResearchField.objects.all()], 2)
        profile.research_fields.set(ResearchField.objects.filter(code__in=selected_fields))
        UserRole.objects.create(user=user, role=Role.objects.get(name='Author'))

    # 创建审稿人（10人）
    for i in range(1, 11):
        user = User.objects.create_user(
            username=f'reviewer{i}',
            password='test123',
            email=f'reviewer{i}@example.com'
        )
        profile = UserProfile.objects.create(
            user=user,
            full_name=f'审稿人{i}',
            institution=random.choice(institutions),
            title=random.choice(["教授", "副教授", "研究员"]),
            email=f'reviewer{i}@example.com',
            phone=f'+86138{random.randint(10000000, 99999999)}',
            orcid=f'0000-000{i}-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}'
        )
        # 为每个审稿人随机选择2-3个研究领域 (修改：增加到3个以提高匹配率)
        selected_fields = random.sample([f.code for f in ResearchField.objects.all()],
                                        random.randint(2, 3))
        profile.research_fields.set(ResearchField.objects.filter(code__in=selected_fields))
        UserRole.objects.create(user=user, role=Role.objects.get(name='Reviewer'))

        # 创建审稿人资料
        reviewer_profile = ReviewerProfile.objects.create(
            user=user,
            expertise=",".join(selected_fields),
            max_reviews_per_month=random.randint(3, 6),  # 增加审稿量上限
            is_active=True
        )
        reviewer_profile.research_fields.set(ResearchField.objects.filter(code__in=selected_fields))

    # 创建编辑（2人）
    for i in range(1, 3):
        editor = User.objects.create_user(
            username=f'editor{i}',
            password='test123',
            email=f'editor{i}@example.com'
        )
        profile = UserProfile.objects.create(
            user=editor,
            full_name=f'编辑{i}',
            institution='上海理工大学',
            title='编辑',
            email=f'editor{i}@example.com',
            phone=f'+86138{random.randint(10000000, 99999999)}',
            orcid=f'0000-0001-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}'
        )
        selected_fields = random.sample([f.code for f in ResearchField.objects.all()], 3)
        profile.research_fields.set(ResearchField.objects.filter(code__in=selected_fields))
        UserRole.objects.create(user=editor, role=Role.objects.get(name='Editor'))


def create_manuscript_types():
    """创建稿件类型"""
    print("创建稿件类型...")
    types = [
        ('Research Paper', '研究论文'),
        ('Review', '综述'),
        ('Short Communication', '短报'),
    ]
    for name, verbose_name in types:
        ManuscriptType.objects.get_or_create(name=name, verbose_name=verbose_name, is_active=True)


def create_volumes_and_issues():
    """创建卷和期"""
    print("创建卷和期...")
    # 2024年卷期
    volume_2024 = Volume.objects.create(
        volume_number=2024,
        year=2024,
        is_published=True,
        publish_date=datetime(2024, 1, 1).date()
    )
    Issue.objects.create(
        volume=volume_2024,
        issue_number=1,
        publication_date=datetime(2024, 3, 1).date(),
        is_published=True
    )
    Issue.objects.create(
        volume=volume_2024,
        issue_number=2,
        publication_date=datetime(2024, 6, 1).date(),
        is_published=True
    )
    Issue.objects.create(
        volume=volume_2024,
        issue_number=3,
        publication_date=datetime(2024, 9, 1).date(),
        is_published=True
    )
    Issue.objects.create(
        volume=volume_2024,
        issue_number=4,
        publication_date=datetime(2024, 12, 1).date(),
        is_published=True
    )

    # 2025年卷期
    volume_2025 = Volume.objects.create(
        volume_number=2025,
        year=2025,
        is_published=True,
        publish_date=datetime(2025, 1, 1).date()
    )
    Issue.objects.create(
        volume=volume_2025,
        issue_number=1,
        publication_date=datetime(2025, 3, 1).date(),
        is_published=True
    )


def create_manuscripts(total_count=100):
    """创建稿件及相关数据"""
    print(f"创建{total_count}篇稿件及相关数据...")

    authors = User.objects.filter(roles__role__name='Author')
    editors = User.objects.filter(roles__role__name='Editor')
    default_editor = editors.first()  # 确保有默认编辑
    manuscript_types = ManuscriptType.objects.all()
    research_fields = ResearchField.objects.all()
    reviewers = User.objects.filter(roles__role__name='Reviewer')

    # 获取每个研究领域的审稿人分布 - 新增代码
    field_reviewers = {}
    for field in research_fields:
        # 查找专长包含此领域的审稿人
        field_reviewers[field.code] = list(reviewers.filter(
            profile__research_fields__code=field.code
        ))
        print(f"研究领域 {field.code} 有 {len(field_reviewers[field.code])} 名审稿人")

    statuses = [
        'DRAFT', 'SUBMITTED', 'UNDER_REVIEW', 'REVISION_REQUIRED',
        'REVISED', 'ACCEPTED', 'REJECTED', 'PUBLISHED'
    ]

    # 时间分布权重（2024年1月至2025年4月，3月和9月投稿高峰）
    months = [
        (2024, 1, 3), (2024, 2, 4), (2024, 3, 10), (2024, 4, 6), (2024, 5, 5),
        (2024, 6, 4), (2024, 7, 2), (2024, 8, 3), (2024, 9, 12), (2024, 10, 7),
        (2024, 11, 5), (2024, 12, 3), (2025, 1, 4), (2025, 2, 5), (2025, 3, 10), (2025, 4, 6)
    ]

    # 按月份权重分配稿件数量
    total_weight = sum(w for _, _, w in months)
    raw_counts = [total_count * weight / total_weight for _, _, weight in months]
    manuscripts_per_month = [int(count) for count in raw_counts]
    remaining = total_count - sum(manuscripts_per_month)
    indices = sorted(range(len(raw_counts)), key=lambda i: raw_counts[i] - manuscripts_per_month[i], reverse=True)
    for i in range(remaining):
        manuscripts_per_month[indices[i]] += 1

    # 确认是否等于总稿件数
    assert sum(manuscripts_per_month) == total_count, "稿件总数不一致"

    # 领域分布权重 - 修改：确保更均匀分布
    field_weights = {'CS': 0.25, 'EE': 0.25, 'MECH': 0.2, 'MAT': 0.2, 'BIO': 0.1}
    fields_list = [code for code, weight in field_weights.items() for _ in range(int(weight * 100))]

    # 审稿时间分布 - 新增代码
    review_time_ranges = [
        (1, 3),  # 30% 快速评审 (1-3天)
        (4, 7),  # 40% 中等速度 (4-7天)
        (8, 14),  # 20% 标准时间 (8-14天)
        (15, 21)  # 10% 较慢评审 (15-21天)
    ]
    review_time_weights = [30, 40, 20, 10]  # 对应百分比权重

    # 存储每个期刊的已发表稿件，用于后续创建出版记录
    published_2024_q1, published_2024_q2 = [], []
    published_2024_q3, published_2024_q4 = [], []
    published_2025_q1 = []

    # ===== 添加审稿意见相关的内容 =====
    # 创建审稿意见的通用评语列表
    general_comments = [
        "本文研究了一个重要的问题，但论述不够深入。",
        "研究方法有创新，但结果分析尚不充分。",
        "文章结构清晰，论述有条理，但创新性不足。",
        "实验设计合理，数据分析全面，但理论模型需要进一步完善。",
        "综述全面，但在某些关键领域缺乏深度探讨。",
        "研究问题有价值，但研究方法存在一定局限性。",
        "数据收集方法科学，但样本量偏小，影响结果可靠性。",
        "理论模型构建有创新，但验证过程不够严谨。"
    ]

    # 优点评语列表
    strength_comments = [
        "文章选题具有重要的理论和实践意义。",
        "研究方法设计科学合理，逻辑性强。",
        "数据分析全面深入，结论可靠。",
        "文献综述全面，对国内外研究现状把握准确。",
        "实验设计严谨，控制变量合理。",
        "论文结构清晰，层次分明，逻辑性强。",
        "研究结果具有一定的创新性和实用价值。",
        "图表制作规范，数据展示清晰。",
        "引用文献新颖，覆盖面广。",
        "语言表达流畅，专业术语使用准确。"
    ]

    # 缺点评语列表
    weakness_comments = [
        "研究方法存在一定局限性，可以考虑采用多种方法相互验证。",
        "样本量偏小，可能影响研究结论的普适性。",
        "文献综述部分对某些关键研究缺乏评述。",
        "理论模型假设条件较为理想化，与实际情况有一定差距。",
        "数据分析方法较为简单，可以尝试更先进的分析方法。",
        "研究结论部分对研究限制讨论不够。",
        "图表说明不够详细，难以理解数据含义。",
        "引言部分研究意义阐述不够充分。",
        "概念界定不够精确，可能导致理解偏差。",
        "格式不够规范，需要按照期刊要求进行调整。"
    ]

    # 修改建议列表
    suggestion_comments = [
        "建议增加样本量，提高研究结论的可靠性。",
        "可以考虑采用多种研究方法交叉验证研究结果。",
        "建议深化理论分析，增强研究的学术深度。",
        "可以扩展研究范围，探讨更多相关变量的影响。",
        "建议完善文献综述，补充最新研究进展。",
        "可以加强研究局限性的讨论，提高研究的严谨性。",
        "建议改进数据分析方法，采用更先进的统计技术。",
        "可以增加对研究结果的实践意义讨论。",
        "建议规范图表格式，提高数据展示的清晰度。",
        "可以精炼语言表达，提高论文的可读性。"
    ]

    # 编辑建议列表
    editor_comments = [
        "这篇文章质量较高，经过修改后可以发表。",
        "文章有一定创新性，但需要作者进行实质性修改。",
        "研究方法可行，但结论需要进一步验证。",
        "文章有潜力，但需要大幅提升理论深度。",
        "建议接受这篇文章，研究结果具有重要价值。",
        "文章质量一般，需要作者做重大修改。",
        "研究方向有意义，但文章组织结构需要改进。",
        "建议拒绝这篇文章，创新性不足。",
        "文章符合期刊范围，有一定学术价值。",
        "研究设计合理，但写作和表达需要大幅改进。"
    ]
    # ===== 审稿意见相关内容添加结束 =====

    # 审稿任务统计 - 新增代码
    total_review_assignments = 0
    completed_review_assignments = 0
    reviewer_assignment_counts = {reviewer.username: 0 for reviewer in reviewers}

    manuscript_count = 0
    for (year, month, _), count in zip(months, manuscripts_per_month):
        for _ in range(count):
            submitter = random.choice(authors)
            # 获取提交者的用户资料
            submitter_profile = UserProfile.objects.get(user=submitter)

            submit_date = timezone.make_aware(datetime(year, month, random.randint(1, 28)))

            # 根据提交时间设置合理的状态分布
            # 越新的稿件，处于早期状态的可能性越大
            current_date = timezone.now().date()
            days_since_submit = (current_date - submit_date.date()).days

            # 修改状态权重，增加UNDER_REVIEW和已完成状态的权重
            if days_since_submit < 7:  # 7天内
                status_weights = {'DRAFT': 0.3, 'SUBMITTED': 0.3, 'UNDER_REVIEW': 0.4, 'REVISION_REQUIRED': 0,
                                  'REVISED': 0, 'ACCEPTED': 0, 'REJECTED': 0, 'PUBLISHED': 0}
            elif days_since_submit < 30:  # 1个月内
                status_weights = {'DRAFT': 0.05, 'SUBMITTED': 0.15, 'UNDER_REVIEW': 0.6, 'REVISION_REQUIRED': 0.2,
                                  'REVISED': 0, 'ACCEPTED': 0, 'REJECTED': 0, 'PUBLISHED': 0}
            elif days_since_submit < 90:  # 3个月内
                status_weights = {'DRAFT': 0, 'SUBMITTED': 0.05, 'UNDER_REVIEW': 0.3, 'REVISION_REQUIRED': 0.3,
                                  'REVISED': 0.2, 'ACCEPTED': 0.1, 'REJECTED': 0.05, 'PUBLISHED': 0}
            elif days_since_submit < 180:  # 6个月内
                status_weights = {'DRAFT': 0, 'SUBMITTED': 0, 'UNDER_REVIEW': 0.15, 'REVISION_REQUIRED': 0.2,
                                  'REVISED': 0.2, 'ACCEPTED': 0.2, 'REJECTED': 0.15, 'PUBLISHED': 0.1}
            else:  # 6个月以上
                status_weights = {'DRAFT': 0, 'SUBMITTED': 0, 'UNDER_REVIEW': 0.05, 'REVISION_REQUIRED': 0.1,
                                  'REVISED': 0.15, 'ACCEPTED': 0.2, 'REJECTED': 0.2, 'PUBLISHED': 0.3}

            status = random.choices(
                list(status_weights.keys()),
                weights=list(status_weights.values()),
                k=1
            )[0]

            # 为不同状态分配合适的编辑
            handling_editor = None
            if status not in ['DRAFT', 'SUBMITTED']:
                handling_editor = random.choice(editors)

            # 使用encode方法将中文字符串转换为字节
            content = '测试文件内容'.encode('utf-8')
            manuscript_file = SimpleUploadedFile(f'manuscript_{manuscript_count}.pdf', content,
                                                 content_type='application/pdf')
            revised_file = None
            if status in ['REVISED', 'ACCEPTED', 'PUBLISHED']:
                revised_file = SimpleUploadedFile(f'revised_{manuscript_count}.pdf', content,
                                                  content_type='application/pdf')
            additional_file = None
            if random.choice([True, False]):
                additional_file = SimpleUploadedFile(f'additional_{manuscript_count}.zip', content,
                                                     content_type='application/zip')

            # 生成唯一的稿件ID
            manuscript_id = f'MS{year}{month:02d}{manuscript_count + 1:04d}'

            # 随机选择研究领域，但确保所有领域都有足够样本
            if manuscript_count % 5 < 5:  # 使用循环确保每个领域都有稿件
                field_code = list(field_weights.keys())[manuscript_count % 5]
            else:
                field_code = random.choice(fields_list)

            # 创建稿件
            manuscript = Manuscript.objects.create(
                manuscript_id=manuscript_id,
                title_cn=f'测试论文{manuscript_count + 1}',
                title_en=f'Test Paper {manuscript_count + 1}',
                authors=f'{submitter_profile.full_name}, 合作者A, 合作者B',
                affiliations=submitter_profile.institution,
                corresponding_author=submitter_profile.full_name,
                submitter=submitter,
                type=random.choice(manuscript_types),
                abstract_cn='中文摘要内容。' * 20,
                abstract_en='English abstract content. ' * 20,
                keywords_cn=','.join([f'关键词{i}' for i in range(1, random.randint(3, 6))]),
                keywords_en=','.join([f'keyword{i}' for i in range(1, random.randint(3, 6))]),
                category_number=random.choice(['TP391', 'TH113', 'TM301']),
                research_field=ResearchField.objects.get(code=field_code),
                similarity_rate=random.uniform(0, 30),
                manuscript_file=manuscript_file,
                revised_file=revised_file,
                additional_file=additional_file,
                created_at=submit_date,
                submit_date=submit_date if status != 'DRAFT' else None,
                handling_editor=handling_editor,
                status=status,
            )

            # 为不同状态设置相应的日期
            # 对于UNDER_REVIEW状态的稿件，不设置decision_date
            if status in ['REVISION_REQUIRED', 'REVISED', 'ACCEPTED', 'REJECTED', 'PUBLISHED']:
                decision_date = submit_date + timedelta(days=random.randint(20, 40))
                manuscript.decision_date = decision_date

                if status == 'REVISED':
                    revision_date = decision_date + timedelta(days=random.randint(7, 20))
                    manuscript.updated_at = revision_date

                if status == 'PUBLISHED':
                    # 根据提交日期确定出版日期和期刊
                    if year == 2024:
                        if month <= 3:
                            publish_date = datetime(2024, 3, 1)
                            published_2024_q1.append(manuscript)
                        elif month <= 6:
                            publish_date = datetime(2024, 6, 1)
                            published_2024_q2.append(manuscript)
                        elif month <= 9:
                            publish_date = datetime(2024, 9, 1)
                            published_2024_q3.append(manuscript)
                        else:
                            publish_date = datetime(2024, 12, 1)
                            published_2024_q4.append(manuscript)
                    else:  # 2025
                        publish_date = datetime(2025, 3, 1)
                        published_2025_q1.append(manuscript)

                    manuscript.publish_date = publish_date.date()

            manuscript.save()
            manuscript_count += 1

            # 创建系统日志
            SystemLog.objects.create(
                user=submitter,
                action='提交稿件',
                details=f'提交稿件 {manuscript.manuscript_id}'
            )

            # 创建通知
            if status != 'DRAFT':
                Notification.objects.create(
                    recipient=submitter,
                    notification_type='SUBMISSION',
                    title=f'稿件 {manuscript.manuscript_id} 已提交',
                    message=f'您的稿件《{manuscript.title_cn}》已成功提交，编号为 {manuscript.manuscript_id}。',
                    url=f'/manuscripts/detail/{manuscript.manuscript_id}/',
                    related_id=manuscript.manuscript_id,
                    created_at=submit_date,
                    is_read=random.choice([True, False])
                )

                if handling_editor:
                    # 获取编辑的用户资料
                    editor_profile = UserProfile.objects.get(user=handling_editor)

                    Notification.objects.create(
                        recipient=handling_editor,
                        notification_type='SUBMISSION',
                        title=f'新稿件 {manuscript.manuscript_id} 待处理',
                        message=f'新稿件《{manuscript.title_cn}》已提交，请处理。',
                        url=f'/editor/manuscript/{manuscript.manuscript_id}/',
                        related_id=manuscript.manuscript_id,
                        created_at=submit_date,
                        is_read=random.choice([True, False])
                    )

            # 创建审稿任务 - 修改部分
            if status in ['UNDER_REVIEW', 'REVISION_REQUIRED', 'REVISED', 'ACCEPTED', 'REJECTED', 'PUBLISHED']:
                # 确保有编辑处理这篇稿件
                assigning_editor = handling_editor or default_editor

                # 修改：优先从匹配的研究领域中选择审稿人
                field_specific_reviewers = field_reviewers.get(manuscript.research_field.code, [])

                # 如果该领域没有足够的审稿人，则从所有审稿人中选择
                if len(field_specific_reviewers) >= 3:
                    # 优先选择任务较少的审稿人
                    sorted_reviewers = sorted(
                        field_specific_reviewers,
                        key=lambda r: reviewer_assignment_counts[r.username]
                    )
                    # 选择任务少的前3-4名审稿人
                    num_reviewers = random.randint(3, 4)
                    selected_reviewers = sorted_reviewers[:num_reviewers]
                else:
                    # 不够审稿人，则混合选择
                    other_reviewers = [r for r in reviewers if r not in field_specific_reviewers]
                    # 确保每篇稿件有3-4个审稿人
                    num_reviewers = random.randint(3, 4)
                    selected_reviewers = list(field_specific_reviewers)

                    if len(selected_reviewers) < num_reviewers:
                        # 按任务数排序其他审稿人
                        sorted_other = sorted(
                            other_reviewers,
                            key=lambda r: reviewer_assignment_counts[r.username]
                        )
                        # 补充所需审稿人
                        selected_reviewers.extend(
                            sorted_other[:num_reviewers - len(selected_reviewers)]
                        )

                # 更新统计数据
                total_review_assignments += len(selected_reviewers)
                for reviewer in selected_reviewers:
                    reviewer_assignment_counts[reviewer.username] += 1

                for i, reviewer in enumerate(selected_reviewers):
                    # 根据稿件状态设置审稿任务状态
                    if status == 'UNDER_REVIEW':
                        # 对于正在审稿中的稿件，设置审稿任务为进行中
                        assignment_status = 'IN_PROGRESS'
                        # 计算相关日期
                        invited_date = submit_date + timedelta(days=random.randint(1, 3))
                        response_date = invited_date + timedelta(days=random.randint(1, 2))
                        due_date = invited_date + timedelta(days=14)
                        # 正在进行中的审稿任务没有完成日期
                        completion_date = None
                    else:
                        # 对于其他状态的稿件，审稿任务已完成
                        assignment_status = 'COMPLETED'
                        completed_review_assignments += 1

                        # 计算相关日期
                        invited_date = submit_date + timedelta(days=random.randint(1, 3))
                        response_date = invited_date + timedelta(days=random.randint(1, 2))
                        due_date = invited_date + timedelta(days=14)

                        # 根据加权分布选择审稿时间范围
                        time_range_idx = random.choices(
                            range(len(review_time_ranges)),
                            weights=review_time_weights,
                            k=1
                        )[0]
                        min_days, max_days = review_time_ranges[time_range_idx]

                        # 确保每个审稿人有不同的审稿时间（有梯度分布）
                        # 让每个审稿人的平均审稿时间略有不同
                        reviewer_idx = int(reviewer.username.replace('reviewer', ''))
                        offset = (reviewer_idx % 3) - 1  # -1, 0, 或 1天的偏移

                        # 应用偏移量，但确保在合理范围内
                        actual_min = max(1, min_days + offset)
                        actual_max = max(actual_min + 1, max_days + offset)

                        review_days = random.randint(actual_min, actual_max)
                        completion_date = invited_date + timedelta(days=review_days)

                        # 打印详细日志，帮助调试
                        print(f"稿件ID {manuscript.manuscript_id} | 审稿人 {reviewer.username} | "
                              f"领域 {manuscript.research_field.code} | 审稿天数 {review_days}")

                    # 创建审稿任务
                    assignment = ReviewAssignment.objects.create(
                        manuscript=manuscript,
                        reviewer=reviewer,
                        assigned_by=assigning_editor,
                        status=assignment_status,
                        invited_date=invited_date,
                        response_date=response_date,
                        due_date=due_date,
                        completion_date=completion_date
                    )

                    # 额外步骤：确保COMPLETED状态的审稿任务有有效的日期
                    if assignment_status == 'COMPLETED':
                        # 再次检查日期是否有效
                        if assignment.completion_date is None or assignment.invited_date is None:
                            # 如果日期无效，重新设置
                            if assignment.invited_date is None:
                                assignment.invited_date = submit_date + timedelta(days=random.randint(1, 3))
                            if assignment.completion_date is None:
                                assignment.completion_date = assignment.invited_date + timedelta(
                                    days=random.randint(3, 10))
                            assignment.save()

                        # 确保完成日期晚于邀请日期
                        if assignment.completion_date <= assignment.invited_date:
                            assignment.completion_date = assignment.invited_date + timedelta(days=random.randint(1, 5))
                            assignment.save()

                        # 验证审稿天数
                        review_days = (assignment.completion_date - assignment.invited_date).days
                        if review_days < 1:
                            assignment.completion_date = assignment.invited_date + timedelta(days=random.randint(1, 5))
                            assignment.save()
                            review_days = (assignment.completion_date - assignment.invited_date).days

                        print(
                            f"确认审稿任务: {reviewer.username}, 稿件 {manuscript.manuscript_id}, 审稿天数: {review_days}")

                    # 为进行中的审稿任务创建通知
                    if assignment_status == 'IN_PROGRESS':
                        Notification.objects.create(
                            recipient=reviewer,
                            notification_type='REVIEW_INVITATION',
                            title=f'审稿邀请：稿件 {manuscript.manuscript_id}',
                            message=f'您被邀请审阅稿件《{manuscript.title_cn}》，请在截止日期前完成审阅。',
                            url=f'/reviewer/manuscript/{manuscript.manuscript_id}/',
                            related_id=manuscript.manuscript_id,
                            created_at=invited_date,
                            is_read=random.choice([True, False])
                        )

                    # ===== 修改后的审稿意见创建代码 =====
                    if assignment_status == 'COMPLETED':
                        # 创建随机评分(1-5分)，但确保评分与稿件状态相符
                        if status in ['ACCEPTED', 'PUBLISHED']:
                            # 已接受稿件评分较高
                            originality_score = random.randint(4, 5)
                            technical_score = random.randint(4, 5)
                            presentation_score = random.randint(3, 5)
                        elif status == 'REJECTED':
                            # 已拒绝稿件评分较低
                            originality_score = random.randint(1, 3)
                            technical_score = random.randint(1, 3)
                            presentation_score = random.randint(1, 3)
                        elif status in ['REVISION_REQUIRED', 'REVISED']:
                            # 需要修改的稿件评分中等
                            originality_score = random.randint(2, 4)
                            technical_score = random.randint(2, 4)
                            presentation_score = random.randint(2, 4)
                        else:
                            # 其他状态
                            originality_score = random.randint(1, 5)
                            technical_score = random.randint(1, 5)
                            presentation_score = random.randint(1, 5)

                        # 总体评价，随机选取1条评语
                        general_comment = random.choice(general_comments)

                        # 优点评价，随机选取2-3条评语组合
                        strengths = "优点：\n" + "\n".join(
                            [random.choice(strength_comments) for _ in range(random.randint(2, 3))])

                        # 缺点评价，随机选取2-3条评语组合
                        weaknesses = "缺点：\n" + "\n".join(
                            [random.choice(weakness_comments) for _ in range(random.randint(2, 3))])

                        # 修改建议，随机选取2-3条评语组合
                        suggestions = "修改建议：\n" + "\n".join(
                            [random.choice(suggestion_comments) for _ in range(random.randint(2, 3))])

                        # 组合所有评价意见
                        comments_to_author = f"{general_comment}\n\n{strengths}\n\n{weaknesses}\n\n{suggestions}"

                        # 给编辑的意见
                        comments_to_editor = random.choice(editor_comments)

                        # 根据稿件状态设置审稿建议
                        if status == 'ACCEPTED' or status == 'PUBLISHED':
                            decision = 'ACCEPT'
                        elif status == 'REJECTED':
                            decision = 'REJECT'
                        elif status == 'REVISION_REQUIRED' or status == 'REVISED':
                            decision = random.choice(['MINOR_REVISION', 'MAJOR_REVISION'])
                        else:
                            decision = random.choice(['ACCEPT', 'MINOR_REVISION', 'MAJOR_REVISION', 'REJECT'])

                        # 创建审稿表单
                        review_form = ReviewForm.objects.create(
                            assignment=assignment,
                            originality_score=originality_score,
                            technical_score=technical_score,
                            presentation_score=presentation_score,
                            decision=decision,
                            comments_to_editor=comments_to_editor,
                            comments_to_author=comments_to_author,
                        )

                        # 创建系统日志记录审稿意见提交
                        SystemLog.objects.create(
                            user=reviewer,
                            action='提交审稿意见',
                            details=f'为稿件 {manuscript.manuscript_id} 提交审稿意见'
                        )

                        # 通知编辑审稿完成
                        Notification.objects.create(
                            recipient=assigning_editor,
                            notification_type='REVIEW_COMPLETED',
                            title=f'审稿完成：稿件 {manuscript.manuscript_id}',
                            message=f'审稿人 {UserProfile.objects.get(user=reviewer).full_name} 已完成稿件《{manuscript.title_cn}》的审阅。',
                            url=f'/editor/manuscript/{manuscript.manuscript_id}/reviews/',
                            related_id=manuscript.manuscript_id,
                            created_at=completion_date or timezone.now(),
                            is_read=random.choice([True, False])
                        )

            # 通知作者稿件状态变更
            if status == 'REVISION_REQUIRED':
                Notification.objects.create(
                    recipient=submitter,
                    notification_type='REVISION',
                    title=f'稿件 {manuscript.manuscript_id} 需要修改',
                    message=f'您的稿件《{manuscript.title_cn}》（编号：{manuscript.manuscript_id}）需要修改，请在两周内提交修改稿。',
                    url=f'/manuscripts/revise/{manuscript.manuscript_id}/',
                    related_id=manuscript.manuscript_id,
                    created_at=manuscript.decision_date,
                    is_read=random.choice([True, False])
                )

            elif status == 'ACCEPTED':
                Notification.objects.create(
                    recipient=submitter,
                    notification_type='ACCEPT',
                    title=f'稿件 {manuscript.manuscript_id} 已录用',
                    message=f'恭喜！您的稿件《{manuscript.title_cn}》（编号：{manuscript.manuscript_id}）已被录用。',
                    url=f'/manuscripts/detail/{manuscript.manuscript_id}/',
                    related_id=manuscript.manuscript_id,
                    created_at=manuscript.decision_date,
                    is_read=random.choice([True, False])
                )

            elif status == 'REJECTED':
                Notification.objects.create(
                    recipient=submitter,
                    notification_type='REJECT',
                    title=f'稿件 {manuscript.manuscript_id} 未被录用',
                    message=f'很遗憾，您的稿件《{manuscript.title_cn}》（编号：{manuscript.manuscript_id}）未被录用。',
                    url=f'/manuscripts/detail/{manuscript.manuscript_id}/',
                    related_id=manuscript.manuscript_id,
                    created_at=manuscript.decision_date,
                    is_read=random.choice([True, False])
                )

            elif status == 'PUBLISHED':
                Notification.objects.create(
                    recipient=submitter,
                    notification_type='PUBLICATION',
                    title=f'稿件 {manuscript.manuscript_id} 已出版',
                    message=f'您的稿件《{manuscript.title_cn}》（编号：{manuscript.manuscript_id}）已出版。',
                    url=f'/manuscripts/detail/{manuscript.manuscript_id}/',
                    related_id=manuscript.manuscript_id,
                    created_at=manuscript.publish_date,
                    is_read=random.choice([True, False])
                )

    # 打印审稿数据统计信息 - 新增代码
    print("\n==== 审稿数据统计 ====")
    print(f"总审稿任务数: {total_review_assignments}")
    print(f"已完成审稿任务数: {completed_review_assignments}")
    print(f"完成率: {completed_review_assignments / total_review_assignments * 100:.2f}%")

    print("\n各审稿人任务分布:")
    for username, count in sorted(reviewer_assignment_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"{username}: {count}个任务")

    # 创建出版记录
    print("\n创建出版记录...")
    # 获取期刊
    issues = {
        '2024_1': Issue.objects.get(volume__year=2024, issue_number=1),
        '2024_2': Issue.objects.get(volume__year=2024, issue_number=2),
        '2024_3': Issue.objects.get(volume__year=2024, issue_number=3),
        '2024_4': Issue.objects.get(volume__year=2024, issue_number=4),
        '2025_1': Issue.objects.get(volume__year=2025, issue_number=1)
    }

    # 为发表的稿件创建出版记录
    def create_publication_records(manuscripts, issue):
        page_number = 1
        for manuscript in manuscripts:
            pages = random.randint(6, 15)
            ManuscriptPublication.objects.create(
                manuscript=manuscript,
                issue=issue,
                page_start=page_number,
                page_end=page_number + pages - 1,
                doi=f'10.1000/USSTJES.{manuscript.manuscript_id}',
                publication_date=issue.publication_date
            )
            page_number += pages

    create_publication_records(published_2024_q1, issues['2024_1'])
    create_publication_records(published_2024_q2, issues['2024_2'])
    create_publication_records(published_2024_q3, issues['2024_3'])
    create_publication_records(published_2024_q4, issues['2024_4'])
    create_publication_records(published_2025_q1, issues['2025_1'])


def fix_review_assignment_dates():
    """修复数据库中已有的审稿任务日期"""
    print("\n开始修复审稿任务日期...")

    # 获取所有状态为COMPLETED但日期有问题的审稿任务
    problem_assignments = ReviewAssignment.objects.filter(
        status='COMPLETED',
        completion_date__isnull=True
    ) | ReviewAssignment.objects.filter(
        status='COMPLETED',
        invited_date__isnull=True
    )

    count = problem_assignments.count()
    print(f"发现{count}个有问题的审稿任务")

    # 修复这些任务的日期
    for assignment in problem_assignments:
        # 如果邀请日期为空，设置一个合理的日期
        if assignment.invited_date is None:
            # 使用稿件提交日期加几天作为邀请日期
            if assignment.manuscript.submit_date:
                assignment.invited_date = assignment.manuscript.submit_date + timedelta(days=random.randint(1, 5))
            else:
                # 如果连提交日期都没有，使用当前日期减去30天
                assignment.invited_date = timezone.now() - timedelta(days=random.randint(20, 30))

        # 如果完成日期为空，设置一个合理的日期
        if assignment.completion_date is None:
            # 完成日期应该比邀请日期晚几天
            assignment.completion_date = assignment.invited_date + timedelta(days=random.randint(5, 14))

        # 确保完成日期晚于邀请日期
        if assignment.completion_date <= assignment.invited_date:
            assignment.completion_date = assignment.invited_date + timedelta(days=random.randint(3, 10))

        assignment.save()
        print(f"已修复: 稿件ID {assignment.manuscript.manuscript_id}, "
              f"审稿人 {assignment.reviewer.username}, "
              f"邀请日期 {assignment.invited_date}, "
              f"完成日期 {assignment.completion_date}")

    print(f"已修复{count}个审稿任务")

    # 统计审稿天数分布
    completed_assignments = ReviewAssignment.objects.filter(
        status='COMPLETED',
        completion_date__isnull=False,
        invited_date__isnull=False
    )

    print(f"\n有效审稿记录总数: {completed_assignments.count()}")

    # 计算每个审稿人的平均审稿天数
    reviewer_stats = {}
    for assignment in completed_assignments:
        try:
            username = assignment.reviewer.username
            days = (assignment.completion_date - assignment.invited_date).days

            if days >= 0:  # 只统计有效天数
                if username not in reviewer_stats:
                    reviewer_stats[username] = {'total_days': 0, 'count': 0}
                reviewer_stats[username]['total_days'] += days
                reviewer_stats[username]['count'] += 1
        except Exception as e:
            print(f"计算天数出错: {e}")

    print("\n各审稿人效率统计:")
    for username, stats in sorted(reviewer_stats.items(), key=lambda x: x[1]['count'], reverse=True):
        if stats['count'] > 0:
            avg_days = round(stats['total_days'] / stats['count'], 2)
            print(f"{username}: {stats['count']}篇稿件, 平均{avg_days}天/篇")


def check_review_data():
    """检查数据库中的审稿数据"""
    print("\n==== 数据库审稿情况检查 ====")
    total = ReviewAssignment.objects.count()
    completed = ReviewAssignment.objects.filter(status='COMPLETED').count()
    with_dates = ReviewAssignment.objects.filter(
        status='COMPLETED',
        completion_date__isnull=False,
        invited_date__isnull=False
    ).count()

    print(f"总审稿任务: {total}")
    print(f"已完成任务: {completed}")
    print(f"有完整日期的已完成任务: {with_dates}")

    # 检查有问题的记录
    problematic = ReviewAssignment.objects.filter(
        status='COMPLETED'
    ).filter(
        completion_date__isnull=True
    ).count()
    print(f"状态完成但缺少完成日期: {problematic}")

    # 检查日期顺序问题
    invalid_dates = ReviewAssignment.objects.filter(
        status='COMPLETED',
        completion_date__isnull=False,
        invited_date__isnull=False
    ).filter(
        completion_date__lt=F('invited_date')
    ).count()
    print(f"完成日期早于邀请日期: {invalid_dates}")

    # 检查日期计算
    valid_assignments = ReviewAssignment.objects.filter(
        status='COMPLETED',
        completion_date__isnull=False,
        invited_date__isnull=False
    )[:5]

    print("\n示例审稿任务日期检查:")
    for a in valid_assignments:
        days = (a.completion_date - a.invited_date).days
        print(f"ID: {a.id}, 审稿人: {a.reviewer.username}, "
              f"从 {a.invited_date} 到 {a.completion_date}, 天数: {days}")


def main():
    """主函数，执行所有数据生成步骤"""
    print("开始生成测试数据...")

    clear_database()
    create_research_fields()
    create_roles()
    create_users()
    create_manuscript_types()
    create_volumes_and_issues()
    create_manuscripts(100)  # 生成100篇稿件

    # 修复审稿任务日期
    fix_review_assignment_dates()

    # 检查数据情况
    check_review_data()

    # 创建最终的系统日志
    admin = User.objects.get(username='admin')
    SystemLog.objects.create(
        user=admin,
        action='初始化测试数据',
        details=f'生成100篇稿件，10名投稿人，10名审稿人，2名编辑，1名管理员'
    )

    print("测试数据生成完成！")


if __name__ == "__main__":
    main()