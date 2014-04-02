//$(document).ready(function(){
$("#spinner").hide();
$(".status").hide();
//});
function set_param(params){
    taskdesc = $.extend(true, {}, params, taskdesc);
    calltask(taskdesc);
}
function set_taskname(name){
    taskdesc.taskname=name
}
// Pass US 
var taskdesc = { 
    "taskname":   'owsq.data.usgs.usgs_get_sitedata',
    //"taskq":      'static',
    //"uiparams":   ['#product','#country','#start_date','#end_date', '#email'],// UI Selected
    "status":     '#status',
    "spinner":    '#spinner',
    "pollinterval": 4000,
    "onPending": function (task_id) {
        setTimeout(function () {
            poll_status(task_id);
        }, options.pollinterval);
        $(options.status).show();
        $(options.status).removeClass('label success warning important').addClass('label warning');
        $(options.status).text("Working...");
        $(options.spinner).show();
    },
    "onFailure": function (data) {
        $(options.status).show();
        $(options.status).removeClass('label success warning important').addClass('label important');
        $(options.status).text("Task failed!");
        $(options.spinner).hide();
    },
    "onSuccess": function (data) {
        $(options.status).show();
        $(options.status).removeClass('label success warning important').addClass('label success');
        $(options.status).html('<a href="' + options.poll_target + data.task_id +'?type=result' + '">Download</a>');
        $(options.spinner).hide();
    },
};
