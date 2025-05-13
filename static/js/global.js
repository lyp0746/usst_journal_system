$(document).ready(function() {
  // AJAX 请求加载动画
  $(document).ajaxStart(function() {
    $('#loading-overlay').fadeIn(200);
  });
  $(document).ajaxStop(function() {
    $('#loading-overlay').fadeOut(200);
  });

  // 表单提交动画
  $('form').on('submit', function() {
    $('#loading-overlay').fadeIn(200);
  });

  // 卡片加载动画
  $('.card').each(function(index) {
    $(this).delay(index * 100).queue(function(next) {
      $(this).addClass('animate__animated animate__fadeInUp');
      next();
    });
  });
});