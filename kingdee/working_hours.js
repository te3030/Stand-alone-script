// ==UserScript==
// @name         获取金蝶工作时长
// @namespace    http://*.ik3cloud.com
// @version      0.0.3
// @icon         http://*.ik3cloud.com/shr/images/shr-16.ico?v=20170728211854
var version = "0.0.3";
// @description  http://*.ik3cloud.com 获取金蝶工作时长
// @author       te3030
// @match        http://*.ik3cloud.com/shr/dynamic.do?uipk=com.kingdee.eas.hr.ats.app.WorkCalendar.empATSDeskTop&inFrame=true&flag=perself&type=day&fromHeader=true
// @match        http://*.ik3cloud.com/shr/dynamic.do?uipk=com.kingdee.eas.hr.ats.app.WorkCalendar.empATSDeskTop&inFrame=true&fromHeader=true
// @grant        none
// ==/UserScript==

function gradeChange() {
    console.log($(".mySelect").val());
}

(function () {
    'use strict';
    document.getElementsByTagName("title")[0].innerText = '金蝶';
    var domain = document.domain;
    var t_date = new Date();
    var t_year = t_date.getFullYear();
    var t_yonth = t_date.getMonth() + 1;
    var t_selectDay = "<select class='mySelect'  style='width:110px;'>";
    for (let i = t_year; i > 2017; i--) {
        let bl_yonth = t_yonth;
        if (i != t_year) {
            bl_yonth = 12;
        }
        for (let j = bl_yonth; j > 0; j--) {
            let jj = (j < 10 ? "0" + j : j);
            let mydate = (i.toString() + "-" + jj.toString());
            if (i == t_year) {
                if (j > t_yonth) {
                    break;
                }
                else if (j == t_yonth) {
                    t_selectDay += '<option selected = "selected" value ="' + mydate + '">' + mydate + '</option>'
                } else {
                    t_selectDay += '<option value ="' + mydate + '">' + mydate + '</option>'
                }
            } else {
                t_selectDay += '<option value ="' + mydate + '">' + mydate + '</option>'
            }
        }
    }
    t_selectDay += "</select>"


    $("body").html($("body").html() + '<div class="footer"><div class="closeDiv">关闭</div><p style="color: #ffe200">黄色表示加班</p>' + t_selectDay + '<div class="footerText"></div></div>');


    $(".footer").css({ position: "fixed", top: "20%", bottom: "0px", "height": "600px", "width": "250px", "background": "#111", "color": "white", "overflow-y": "auto", "z-index": 1000 });


    let weekday = ["星期日", "星期一", "星期二", "星期三", "星期四", "星期五", "星期六"];
    let url = "http://"+domain+"/shr/dynamic.do?";
    let data = {
        "monthLimitDay": "2019-08-31",
        "method": "getMyAttendanceDaySum",
        "uipk": "com.kingdee.eas.hr.ats.app.WorkCalendar.empATSDeskTop"
    };

    function getCountDays(d) {
        var curDate = new Date();
        var curMonth = curDate.getMonth();
        curDate.setMonth(curMonth + 1);
        curDate.setDate(0);
        return curDate.getDate();
    }

    function getEvryDay() {
        var dayArry = [];
        for (var k = 1; k <= getCountDays(); k++) {
            dayArry.push(k);
        }
        return dayArry;
    };
    function getMonthDays(year, month) {
        var thisDate = new Date(year, month, 0);
        return thisDate.getDate();
    }
    var day = getEvryDay();
    var jingdieDay = {};

    function getData(f_year_yonth, i, f_cache) {

        let q = (t_yonth < 10 ? "0" + t_yonth : t_yonth);
        let w = (t_year.toString() + "-" + q.toString())
        if (i >= getCountDays(f_year_yonth)) {
            $(".mySelect").css({ "display": "block" })
            return;
        }
        if (day[i] < 10) {
            data["monthLimitDay"] = f_year_yonth + "-0" + day[i]
        } else {
            data["monthLimitDay"] = f_year_yonth + "-" + day[i]
        }
        data["method"] = "getMyAttendanceDaySum";
        if (i % 5 == 0) {
            f_cache = true;
        }
        $.ajax({
            type: 'POST',
            url: url,
            data: data,
            cache: f_cache,
            async: f_cache,
            success: function (req) {
                var myddy = new Date(data["monthLimitDay"]).getDay();
                let aColor = 'ffffff';
                let a = '';
                if (!req.realWorkTime || req.realWorkTime == "无出勤记录") {
                    a = a + "无出勤记录</p>";
                } else {
                    let realWorkTime = req.realWorkTime.split("-");
                    if (realWorkTime.length == 2) {
                        let b = 0;
                        let c = false;
                        console.log(data["monthLimitDay"], realWorkTime);
                        if (jingdieDay[data["monthLimitDay"]] != undefined) {
                            let realWorkTime2 = jingdieDay[data["monthLimitDay"]].split("-");
                            console.log(jingdieDay[data["monthLimitDay"]], realWorkTime2);
                            if (realWorkTime2.length == 2) {
                                if (Number(realWorkTime[1].split(":")[0]) > 19) {
                                    if (Number(realWorkTime[1].split(":")[1]) > 30) {
                                        console.log(data["monthLimitDay"], "加班了1");
                                        // c = true;
                                        aColor = 'ffe200';
                                    }
                                }
                            }
                        } else {
                            console.log(data["monthLimitDay"], "加班了");
                            c = true;
                            aColor = 'ffe200';
                        }

                        let bb = realWorkTime[0].split(":");
                        let cc = realWorkTime[1].split(":");
                        if (bb.length == 2 && cc.length == 2) {
                            let aTime = 0;
                            if (c) {
                            } else {
                                b = b + 1.5;
                                // if (bb[0] < 12 && myddy < 6 && myddy > 0) {
                                // }
                            }
                            let startTime = new Date(data["monthLimitDay"] + ' ' + realWorkTime[0]);
                            let endTime = new Date(data["monthLimitDay"] + ' ' + realWorkTime[1]);
                            aTime = ((endTime - startTime) / 1000 / 60 / 60 - b).toFixed(2);
                            a = a + req.realWorkTime + "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;" + aTime + '</p>';
                        } else {
                            a = a + req.realWorkTime + "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;计算错误</p>";
                        }
                    } else {
                        a = a + req.realWorkTime + "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;计算错误</p>";
                    }
                    a = '<p style="color: #' + aColor + ';">' + weekday[myddy] + "&nbsp;" + data["monthLimitDay"].slice(5) + "&nbsp;&nbsp;&nbsp;" + a;
                }
                $(".footerText").html($(".footerText").html() + a)
                getData(f_year_yonth, i + 1, false);
            },
            dataType: "json"
        });
    }
    $(".mySelect").css({ "display": "none" })

    function getData3() {
        data["method"] = "getMyAttendanceDetail";
        $.ajax({
            type: 'POST',
            url: "http://"+domain+"/shr/dynamic.do?",
            data: data,
            success: function (req) {
                jingdieDay = [];
                for (let i = 0; i < req.length; i++) {
                    if (req[i]["planWorkTime"]) {
                        jingdieDay[req[i]["attendDtShtStr"]] = req[i]["planWorkTime"];
                    }
                }
                console.log(jingdieDay);
                // let q = (t_yonth < 10 ? "0" + t_yonth : t_yonth);
                // getData((t_year.toString() + "-" + q.toString()), 0, true)
                getData(data["monthLastDay"].slice(0, 7), 0, true)
            },
            dataType: "json"
        });
    }
    function getData2(f_year, f_yonth) {
        let q = (f_yonth < 10 ? "0" + f_yonth : f_yonth);
        data["monthLastDay"] = f_year + "-" + q + "-" + getMonthDays(f_year, f_yonth);
        setTimeout(getData3(), 0)
    }
    getData2(t_year, t_yonth);
    $(".mySelect").change(function () {
        $(".footerText").html("")
        $(".mySelect").css({ "display": "none" })
        console.log($(".mySelect").val());
        let mySelectDaty = $(".mySelect").val().split("-");
        getData2(Number(mySelectDaty[0]), Number(mySelectDaty[1]))
        // getData($(".mySelect").val(), 0, true);
    });

    $(".closeDiv").click(function () {
        $(".footer").css({ "display": "none" })
    });
})();
