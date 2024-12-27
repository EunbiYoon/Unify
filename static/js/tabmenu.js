$(document).ready(function(){
    $('#registerTabs a').click(function (e) {
        e.preventDefault();
        $(this).tab('show active');
    });
});