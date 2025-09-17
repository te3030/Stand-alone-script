// ==UserScript==
// @name         取消非不必要广告
// @namespace    http://tampermonkey.net/
// @version      0.3
// @description  try to take over the world!
// @author       You
// @icon         data:image/gif;base64,R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw==
// @grant        none
// @match      *://*.csdn.net/*
// @require      https://cdn.bootcdn.net/ajax/libs/jquery-cookie/1.4.1/jquery.cookie.js
// ==/UserScript==

(function () {
  'use strict';

  function findElement(selectorType, selectorName, successCallback, maxAttempts = 3, failureCallback) {
    maxAttempts = maxAttempts > 0 ? maxAttempts : 1;
    (async function attemptToFind(attempt) {
      if (attempt > maxAttempts) {
        if (typeof failureCallback === 'function') {
          failureCallback();
        }
        return;
      }

      let element;
      switch (selectorType) {
        case 'id':
          // element = document.getElementById(selectorName);
          element = document.querySelector('#' + selectorName);
          break;
        case 'class':
          element = document.querySelector('.' + selectorName);
          break;
        case 'tag':
          element = document.querySelector(selectorName);
          break;
        default:
          console.error('Invalid selector type');
          return;
      }

      if (element) {
        if (typeof successCallback === 'function') {
          successCallback(element);
        }
      } else {
        setTimeout(() => {
          attemptToFind(attempt + 1);
        }, 400 * attempt);
      }
    })(1);
  }

  function copy(e) {
    // clipboardData 对象是为通过编辑菜单、快捷菜单和快捷键执行的编辑操作所保留的，也就是你复制或者剪切内容
    let clipboardData = e.clipboardData || window.clipboardData;
    // 如果 未复制或者未剪切，直接 return
    if (!clipboardData) return;
    // Selection 对象 表示用户选择的文本范围或光标的当前位置。
    // 声明一个变量接收 -- 用户输入的剪切或者复制的文本转化为字符串
    let text = window.getSelection().toString();
    if (text) {
      // 如果文本存在，首先取消默认行为
      e.preventDefault();
      // 通过调用 clipboardData 对象的 setData(format,data) 方法，设置相关文本
      // format 一个 DOMString 类型 表示要添加到 drag object 的拖动数据的类型
      // data 一个 DOMString 表示要添加到 drag object 的数据
      clipboardData.setData('text/plain', text)
    }
  };


  if (window.location.hostname == "blog.csdn.net") {

    var removeClassList = [
      "blog_container_aside",
      "aside-box",
      "recommend-box",
      "template-box",
      "blog-footer-bottom",
      "hljs-button",
      "blog-tags-box",
      "hide-article-box",
      "passport-auto-tip-login-container",
      "csdn-side-toolbar",
      "skill-tree-box",
      "follow-nickName",
      "passport-login-tip-container",
      "directory-boxshadow-dialog",
      "second-recommend-box",
      "recommend-box",
      "recommend-box",
      "article-info-box .operating",
      "article-info-box .article-type-img"
      // "nodata .container",
      // "nodata .container",
      // "nodata .container main",
    ]

    var removeIdList = [
      "toolbarBox",
      "blog_detail_zk_collection",
      "articleSearchTip",
      "hide-article-box",
      "rightAside",
      "blogColumnPayAdvert",
      "blog_cocsdn-toolbarntainer_aside",
      "toolBarBox",
      "recommendNps",
      "pcCommentBox",
      "blogHuaweiyunAdvert",
      // "content_views pre",
      // "content_views pre code",
    ]

    var i = 0;
    var len = removeClassList.length;
    for (; i < len;) {
      findElement("class", removeClassList[i], function (element) { element.remove() });
      i = i + 1;
    }

    var i = 0;
    var len = removeIdList.length;
    for (; i < len;) {
      findElement("id", removeIdList[i], function (element) { element.remove() });
      i = i + 1;
    }

    findElement("class", "nodata .container", function (element) { element.style.width = "100%" });
    findElement("class", "nodata .container", function (element) { element.style.marginRight = "0px" });
    findElement("class", "nodata .container main", function (element) { element.style.width = "auto" });

    findElement("tag", "main", function (element) { element.style.float = "inherit" });
    findElement("tag", "body", function (element) { element.style.minWidth = "0px" });

    setTimeout(function () {

      findElement("id", "content_views", function (element) {
        element.parentNode.replaceChild(element.cloneNode(true), element);
        // element.addEventListener('copy', copy );

        //  while(true){
        //     var preCode = document.getElementsByClassName("look-more-preCode contentImg-no-view")
        //     if(preCode.length > 0){
        //         for(var i = 0; i < preCode.length; i++ ){
        //              preCode[i].click();
        //         }
        //     }else{
        //          break;
        //     }
        //  }
        // $(".passport-login-container").remove()
        findElement("class", "passport-login-container", function (element) { element.remove() });

        //   findElement("id", "content_views pre", function (element) { element.css("-webkit-user-select", "auto") });
        //   // $("#content_views pre").css("-webkit-user-select", "auto");
        //   findElement("id", "content_views pre code", function (element) { element.css("user-select", "auto") });
        //   // $("#content_views pre code").css("user-select", "auto");

      });

      $(".hl").map(function (value, index) {
        var $ele = $('<span>');
        $ele.html(index.text);
        index.before($ele[0]);
        index.remove();
      })
    }, 1000)
  }

})();