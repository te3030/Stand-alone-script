// ==UserScript==
// @name         Jumpserver full screen
// @namespace    http://tampermonkey.net/
// @version      0.1
// @description  try to take over the world!
// @author       te3030
// @match        http://192.168.1.251:8002/luna/
// @icon         data:image/gif;base64,R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw==
// @grant        none
// @license      MIT
// @downloadURL https://raw.githubusercontent.com/te3030/Stand-alone-script/refs/heads/main/Tampermonkey/Jumpserver/jumpserver_full_screen.js
// @updateURL https://raw.githubusercontent.com/te3030/Stand-alone-script/refs/heads/main/Tampermonkey/Jumpserver/jumpserver_full_screen.js
// ==/UserScript==

(function () {
    'use strict';
    functionName()
})();

function functionName() {
    let a = false;
    if ($('#ztree_2_span') != undefined && $('#ztree_2_span')[0] != undefined) {
        $('#ztree_2_span')[0].click()
        while (true) {
            if ($('iframe') != undefined && $('iframe')[0] != undefined && $('iframe')[0].src != "") {
                setTimeout(function () {
                    functionName2()
                }, 1000);
                return;
            }
        }
    }
    if (!a) {
        setTimeout(function () {
            functionName()
        }, 200);
    }
}
function functionName2() {
    var tp = window.open('_blank');
    tp.location =  $('iframe')[0].src;
    // alert($('iframe')[0].src)

    var userAgent = navigator.userAgent;
    if (userAgent.indexOf("Firefox") != -1 || userAgent.indexOf("Chrome") != -1) {
        location.href = "about:blank";
    } else {
        window.opener = null;
        window.open('', '_self');
    }
    window.close();
}
