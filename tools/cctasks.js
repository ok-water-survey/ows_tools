// Some helpers for running Cybercommons Tasks
// Should point to queue submission target
// Configuration object for calling cybercom queue tasks.
// Parameters can be specified in [params] list object, or a special list of 
// jQuery selectors can be provided to grab the current values of these form elements at run-time.
/*
taskdesc = { 
    "taskname":   'cybercomq.static.tasks.modiscountry',
    "taskq":      'static',
    "params":     ['MOD09A1_ndvi','MX','2010-10-10','2010-11-1'],   // Fixed params 
    "uiparams":   ['#product','#country','#start_date','#end_date'],// UI Selected
    "status":     '#status',
    "spinner":    '#spinner',
    "pollinterval": 2000,
}

*/
// Called by call task to poll queue status of task based on task_id
var QUEUE_SUBMIT = 'http://test.oklahomawatersurvey.org/queue/';

function test_auth_tkt() {
    $("#auth_dialog").hide()
    if ($.cookie('auth_tkt') ) {
        $('#auth_message').html("you're logged in")
    }
    else {
        $("#auth_dialog").dialog( { height:200, modal: true} );
        $("#auth_dialog").dialog("open");
        $('#auth_message').html('Please <a href="http://test.cybercommons.org/accounts/login/">login</a> to track your tasks via the cybercommons').addClass('label warning')
    }

}

function poll_status(task_id) {
    $.getJSON(QUEUE_SUBMIT + 'task/' + task_id + '?callback=?', function (data) {
        if (data.status == "PENDING") {
            options.onPending(task_id);
        } else if (data.status == "FAILURE") {
            options.onFailure(data);
        } else if (data.status == "SUCCESS") {
            options.onSuccess(data);
        }
    });
}

function calltask(taskdesc) {
    defaults = {
        "service_host": QUEUE_SUBMIT + 'run/',
        "poll_target": 'http://test.oklahomawatersurvey.org/queue/task/',
        "status": '#status',
        "spinner": '#spinner',
        "pollinterval": 2000,
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
            $(options.status).html('<a href="' + option.poll_target + data.task_id +'?type=result' + '">Download</a>');
            $(options.spinner).hide();
        },
    }
    options = $.extend(true, {}, defaults, taskdesc)

    var taskparams = ""
    if (options.params) {
        for (item in options.params) {
            taskparams = taskparams.concat('/' + options.params[item]);
        }
    } else if (options.uiparams) {
        for (item in options.uiparams) {
            taskparams = taskparams.concat('/' + $(options.uiparams[item]).val());
        }
    }
    var taskcall = ""
    if (options.taskq) {
        taskcall = options.taskname + '@' + options.taskq;
    } else {
        taskcall = options.taskname;
    }

    var request = options.service_host + taskcall + taskparams;

    $.getJSON(request + '?callback=?', function (data) {
        $(options.status).text('Task submitted...');
        var task_id = data.task_id;
        setTimeout(function () {
            poll_status(task_id);
        }, taskparams.pollinterval);
    });
}

