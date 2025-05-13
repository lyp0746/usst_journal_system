document.addEventListener('DOMContentLoaded', function() {
    console.log('通知JS已加载');

    // 选择器
    const selectAllCheckbox = document.getElementById('select-all');
    const notificationCheckboxes = document.querySelectorAll('input[name="notification_ids"]');
    const markReadButton = document.getElementById('mark-read-selected');
    const loadingOverlay = document.getElementById('loading-overlay');

    // 初始隐藏加载覆盖层
    if (loadingOverlay) loadingOverlay.style.display = 'none';

    // 调试信息
    console.log('找到复选框:', notificationCheckboxes.length);
    console.log('找到标记按钮:', !!markReadButton);

    // 全选/取消全选
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function() {
            notificationCheckboxes.forEach(checkbox => {
                checkbox.checked = this.checked;
            });
            updateMarkReadButton();
        });
    }

    // 单个复选框变更事件
    notificationCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', updateMarkReadButton);
    });

    // 更新标记按钮状态
    function updateMarkReadButton() {
        if (!markReadButton) return;
        const hasChecked = Array.from(notificationCheckboxes).some(checkbox => checkbox.checked);
        markReadButton.disabled = !hasChecked;
    }

    // 标记已读功能
    if (markReadButton) {
        markReadButton.addEventListener('click', function(e) {
            e.preventDefault();

            const checkedIds = Array.from(notificationCheckboxes)
                .filter(checkbox => checkbox.checked)
                .map(checkbox => checkbox.value);

            if (checkedIds.length === 0) {
                alert('请选择要标记的通知');
                return;
            }

            console.log('准备标记已读:', checkedIds);

            // 显示加载层
            if (loadingOverlay) loadingOverlay.style.display = 'flex';

            // 获取CSRF令牌
            const csrfToken = document.querySelector('input[name="csrfmiddlewaretoken"]').value;
            console.log('CSRF令牌:', !!csrfToken);

            // 构建数据并发送请求
            const formData = new FormData();
            checkedIds.forEach(id => formData.append('notification_ids', id));

            // 发送请求 - 使用完整URL路径
            const fetchUrl = window.location.pathname.endsWith('/')
                ? 'mark-read/'
                : '/notifications/mark-read/';

            console.log('发送请求到:', fetchUrl);

            fetch(fetchUrl, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': csrfToken
                }
            })
            .then(response => {
                console.log('响应状态:', response.status);
                if (!response.ok) {
                    throw new Error('服务器响应错误: ' + response.status);
                }
                return response.json();
            })
            .then(data => {
                console.log('响应数据:', data);

                if (data.success) {
                    // 本地更新UI
                    checkedIds.forEach(id => {
                        const row = document.querySelector(`input[value="${id}"]`).closest('tr');
                        if (row) {
                            const statusCell = row.querySelector('td:last-child');
                            if (statusCell) statusCell.textContent = '已读';
                        }
                    });

                    // 重置选择状态
                    if (selectAllCheckbox) selectAllCheckbox.checked = false;
                    notificationCheckboxes.forEach(cb => cb.checked = false);
                    updateMarkReadButton();

                    // 显示成功消息
                    alert('成功标记通知为已读');
                } else {
                    // 显示错误消息
                    alert('操作失败: ' + (data.error || '未知错误'));
                }
            })
            .catch(error => {
                console.error('请求错误:', error);
                alert('请求失败: ' + error.message);
            })
            .finally(() => {
                if (loadingOverlay) loadingOverlay.style.display = 'none';
            });
        });
    }

    // 初始化按钮状态
    updateMarkReadButton();
});