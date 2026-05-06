# [Tampermonkey](https://www.tampermonkey.net/)

篡改猴 (Tampermonkey) 是拥有 超过 1000 万用户 的最流行的浏览器扩展之一。 它适用于 Chrome、Microsoft Edge、Safari、Opera Next 和 Firefox。

有些人也会把篡改猴(Tampermonkey)称作油猴(Greasemonkey)，尽管后者只是一款仅适用于 Firefox 浏览器的浏览器扩展程序。

它允许用户自定义并增强您最喜爱的网页的功能。用户脚本是小型 JavaScript 程序，可用于向网页添加新功能或修改现有功能。使用 篡改猴，您可以轻松在任何网站上创建、管理和运行这些用户脚本。

例如，使用 篡改猴，您可以向网页添加一个新按钮，可以快速在社交媒体上分享链接，或自动填写带有个人信息的表格。在数字化时代，这特别有用，因为网页常常被用作访问广泛的服务和应用程序的用户界面。

此外，篡改猴 使您轻松找到并安装其他用户创建的用户脚本。这意味着您可以快速轻松地访问为您喜爱的网页定制的广泛库，而无需花费数小时编写自己的代码。

无论您是希望为您的站点添加新功能的 Web 开发人员，还是只是希望 改善在线体验的普通用户，篡改猴 都是您的工具箱中的一个很好的工具。

[Tampermonkey Chrome 120+](https://chromewebstore.google.com/detail/tampermonkey/dhdgffkkebhmkfjojejmpbldmpobfkfo)

[Tampermonkey Chrome 120+ crx](https://www.tampermonkey.net/crx/tampermonkey_stable.crx)

[Tampermonkey Microsoft Edge 79+](https://microsoftedge.microsoft.com/addons/detail/iikmkjmpaadaobahmlepeloendndfphd)

[Tampermonkey Firefox 78+](https://addons.mozilla.org/firefox/addon/tampermonkey/)

[Tampermonkey iOS 15+ || MacOS 11+](https://apps.apple.com/app/tampermonkey/id6738342400)

[Tampermonkey Opera Opera 15+](https://addons.opera.com/en/extensions/details/tampermonkey-beta/)



# [violentmonkey](https://github.com/violentmonkey/violentmonkey)

Violentmonkey provides userscripts support for browsers.
It works on browsers with [WebExtensions](https://developer.mozilla.org/en-US/Add-ons/WebExtensions) support.

More details can be found [here](https://violentmonkey.github.io/).

## Dockerfile build violentmonkey

### Dockerfile

```Dockerfile
FROM node:25 AS builder

RUN apt-get update && apt-get install -y \
    git \
    python3 \
    make \
    g++ \
    libvips-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build
RUN git clone https://github.com/violentmonkey/violentmonkey.git .

RUN yarn install --frozen-lockfile
RUN yarn build

RUN cp -r dist/ /output/
```

### build

```bash
docker build -t violentmonkey-build
docker create --name violentmonkey-build violentmonkey-build
docker cp violentmonkey-build:/output ./dist-output
docker rm violentmonkey-build
```


# scripts

[Userscript.Zone](https://www.userscript.zone/) 搜索 是一个新网站，允许通过输入合适的URL或域来搜索用户脚本。

 大量的脚本资源
 很容易找到合适的用户脚本
 仅显示受审核的用户脚本页面或至少具有注释功能的页面中的用户脚本


[GreasyFork](https://greasyfork.org/) 或许是最受欢迎的后起之秀了。它由 Jason Barnabe 创建,Jason Barnabe 同时也是Stylish 网站的创办者,在其储存库中有大量的脚本资源。

 大量的脚本资源
 拥有可以从 Github 中进行脚本同步的功能
 非常活跃的[开放源代码发展模式](https://github.com/JasonBarnabe/greasyfork)


[OpenUserJS](https://openuserjs.org/) 继 GreasyFork 之后开始创办。它由 Sizzle McTwizzle 创建,同样地,在其储存库中也拥有大量的脚本资源。

 拥有可以从 Github、fork scripts 中进行脚本同步的功能
 非常活跃的[开放源代码发展模式](https://github.com/OpenUserJs/OpenUserJS.org)

