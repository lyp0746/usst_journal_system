from django.contrib.auth.models import User
from django.db.models import Avg, Count, Q
from django.utils import timezone
from datetime import timedelta
from manuscripts.models import Manuscript
from review_process.models import ReviewerProfile, ReviewAssignment, ReviewForm
from accounts.models import UserRole


def get_reviewer_candidates(manuscript):
    """  
    获取符合基本条件的审稿人候选列表  
    """
    # 获取投稿人信息  
    submitter = manuscript.submitter
    submitter_institution = submitter.profile.institution
    manuscript_field = manuscript.research_field

    # 获取所有活跃审稿人  
    reviewer_profiles = ReviewerProfile.objects.filter(
        is_active=True,
        user__roles__role__name='Reviewer',
        user__roles__is_active=True,
        research_fields=manuscript_field
    ).exclude(
        # 排除稿件提交者  
        user__id=submitter.id
    ).exclude(
        # 排除来自同一机构的审稿人  
        user__profile__institution=submitter_institution
    ).exclude(
        # 排除已分配给该稿件的审稿人  
        user__id__in=ReviewAssignment.objects.filter(
            manuscript=manuscript
        ).values_list('reviewer__id', flat=True)
    )

    return reviewer_profiles


def match_reviewers(manuscript, num_reviewers=3, prioritize_quality=False):
    """  
    智能匹配审稿人  

    参数:  
    - manuscript: Manuscript 实例  
    - num_reviewers: 推荐审稿人数量（默认3）  
    - prioritize_quality: 是否优先考虑质量而非任务均衡（默认False）  

    返回:  
    - 推荐的审稿人列表  
    """
    current_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    reviewer_profiles = get_reviewer_candidates(manuscript)

    # 获取当月审稿任务统计  
    assignments_this_month = ReviewAssignment.objects.filter(
        invited_date__gte=current_month,
        invited_date__lt=current_month + timedelta(days=31),
        status__in=['INVITED', 'ACCEPTED', 'IN_PROGRESS']
    ).values('reviewer').annotate(task_count=Count('id'))

    # 统计任务量映射  
    task_counts = {item['reviewer']: item['task_count'] for item in assignments_this_month}

    reviewer_candidates = []
    for profile in reviewer_profiles:
        # 检查当月审稿量是否已满  
        current_reviews = task_counts.get(profile.user.id, 0)
        if current_reviews < profile.max_reviews_per_month:
            # 计算历史审稿质量  
            review_quality = ReviewForm.objects.filter(
                assignment__reviewer=profile.user
            ).aggregate(
                avg=Avg('originality_score') + Avg('technical_score') + Avg('presentation_score')
            )['avg'] or 0

            # 标准化评分  
            quality_score = review_quality / 3 if review_quality else 0

            reviewer_candidates.append({
                'reviewer': profile.user,
                'quality_score': quality_score,
                'current_reviews': current_reviews,
                'expertise': profile.expertise
            })

            # 根据优先级参数决定排序方式
    if prioritize_quality:
        # 优先考虑质量评分，其次是任务量  
        reviewer_candidates.sort(key=lambda x: (-x['quality_score'], x['current_reviews']))
    else:
        # 优先考虑任务均衡，其次是质量评分  
        reviewer_candidates.sort(key=lambda x: (x['current_reviews'], -x['quality_score']))

    return [r['reviewer'] for r in reviewer_candidates[:num_reviewers]]  