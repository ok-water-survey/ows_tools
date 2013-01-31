$(document).ready(function(){

//test_auth_tkt();

$("#spinner").hide();
$("#status").hide();

// Set up the UI 
 /*
// Get list of modis products (This should come from the catalog, but it is presently coming from a cache of the catalog.
$.getJSON('http://test.cybercommons.org/mongo/db_find/eomf/modis_products/{"sort":[("cat_name",1)]}?callback=?', 
    function(products) {
        pickproduct = $("#product");
        $.each(products, function() {
            pickproduct.append($("<option/>").val(this.cat_name).text(this.cat_name));
        });
    }
);

// Get list of countries to pick from
$.getJSON('http://test.cybercommons.org/mongo/db_find/eomf/countries/{"sort":[("country_name",1)]}?callback=?', 
    function(countries) {
        pickcountry = $("#country");
        $.each(countries, function() {
            pickcountry.append($("<option/>").val(this.country_code).text(this.country_name));
        });
    }
);

$(".datepick").change(function() { $(".datepick").datepicker("option", "dateFormat", 'yy-mm-dd');} );
$("#start_date").datepicker({ minDate: new Date(2000,2-1,24), maxDate: new Date(),  changeYear: true }); 
$("#end_date").datepicker({ minDate: new Date(2000,2-1,24), maxDate: new Date(), changeYear: true } );
*/

// Pass US 
taskdesc = { 
    "taskname":   'owsq.data.usgs.get_metadata_site',
    //"taskq":      'static',
    //"uiparams":   ['#product','#country','#start_date','#end_date', '#email'],// UI Selected
    "status":     '#status',
    "spinner":    '#spinner',
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
        $(options.status).html('<a href="' + data.tombstone[0].result + '">Download</a>');
        $(options.spinner).hide();
    },
};
function set_param(params){
    taskdesc = $.extend(true, {}, params, taskdesc);
    calltask(taskdesc);
}
/*
$(".button").click( function() {calltask(taskdesc);} );
*/
});


