# AcssBackend

智能(A)充电/计费(C)调度(S)系统(S)的后端仓库，基于Django框架与Python3.10开发。

[toc]

## 目录结构

repo根目录：AcssBackend

​	站点模块：accs_site

​		配置文件、根路由模块

​	数据模块：data

​		ORM模型、控制器、服务

​	调度模块：schd

​		控制器、服务

## 开发环境配置

### 基本环境配置

1. 下载安装Visual Studio Code
2. 下载安装Python3.10
   - Windows平台可以在官网[下载](https://www.python.org/ftp/python/3.9.13/python-3.9.13-amd64.exe)x86_64安装包
   - Linux平台可以直接使用包管理工具安装
   - macOS平台在安装Homebrew后，可以使用`brew`安装
   - 若感兴趣，可以尝试使用`pyenv`管理不同版本的Python
3. 使用`git clone https://e.coding.net/segb/ACSS/AcssBackend.git`克隆仓库到自己喜欢的位置
4. 打开Visual Studio Code，打开AcssBackend文件夹，在拓展页面搜索并安装`Python`与`Django`拓展
5. 在项目根目录打开命令行/控制台（通过Visual Studio Code的菜单可以直接打开）
6. 运行`pip install -r requirements.txt`安装项目依赖
7. 运行`python manage.py runserver`，启动服务器，若没有出现错误信息并显示了服务地址，配置成功

### 调试方法

1. 在需要调试的地方打断点

2. 进入Visual Studio Code的*运行与调试*页面，点击*创建launch.json*，选择*Django*

3. 创建完成后，直接关闭*launch.json*，在*运行与调试*点击调试按钮，或者使用F5功能键

4. 服务器启动后，需要触发断点，请使用接口测试工具进行触发，例如Postman

5. (可选) Windows平台[下载](https://dl.pstmn.io/download/latest/win64)并安装Postman

   (可选) Linux平台[下载](https://dl.pstmn.io/download/latest/linux64)并安装Postman

   (可选) macOS平台前往[下载页](https://www.postman.com/downloads/)选择芯片版本下载并安装Postman

6. (可选) 根据Postman指导步骤添加接口用例

## 版本管理策略

### 主要分支

主要分支为`master`与`dev`分支，默认分支为`master`分支。

- `master`分支
  描述：产品的发布分支，用于进行稳定版本的迭代
  是否受保护：是
  管理员：jinuo
- `dev`分支
  描述：产品最新的开发版本，用于进行新功能的测试
  是否受保护：是
  管理员：jinuo

### 分支的分类

为了便于分支管理，将不同功能的分支以特定的格式命名，分支分类如下：

- feature分支：用于进行新功能的开发，命名规则为`dev-feat-{feat_name}`，`feat_name`应该由数字、字母、以及**下划线**组成
- fix分支：用于issue的修复，命名方式为`dev-fix-{fix_name}`，`fix_name`的命名规则同上
- refactor分支：用于代码的重构，大概率不需要使用，命名方式为`dev-refactor-{refactor_name}`，`refactor_name`的命名规则同上

>  注：使用下划线的目的是将分支的名称与前缀区分开，方便阅读

### 开发流程

1. 确认需要执行的任务类别
2. 基于`dev`分支或者自己的子分支按照命名规范创建新分支
3. 进行开发
4. (可选) 使用`merge`或`rebase`指令（建议用`merge`）将`dev`分支的提交更新到自己的分支上
5. 使用`push`推送全部提交
6. 在*创建合并请求*页面发起`PR`

### 创建合并请求的方法

1. 在代码仓库菜单中点击合并请求，点击右上角的创建合并请求，在打开的页面中选择源分支为你自己的分支，目标分支选择`dev`分支。若提示无法合并，则说明`dev`分支有新的提交，并且这些提交中修改的代码与你的分支修改的代码**有冲突**，这时需要执行**开发流程**中的步骤4。步骤4执行完成后，再回到*创建合并请求*页面，选择分支后，已可以进行合并。
2. 输入合并请求标题，格式为`{merge_type}. {title}`，例如“feat. 添加登录注册支持”。确保`title`在20字以内
3. (可选) 输入描述，如果改动较小，则可以不输入描述。若改动较大或认为又需要特别说明的内容，则可以写在描述中
4. 如果分支为`fix`类型，则需要在下方的关联资源中关联对应的issue

### 提交消息的规范

提交(commit)需要按照规范进行。此项目参考谷歌的AngularJS提交规范，具体规范内容可以使用搜索引擎查询。这里推荐使用Visual Studio Code进行开发，在拓展中搜索并安装`git-commit-plugin`，在版本管理页面点击“版本管理”标题右侧的Github章鱼按钮，按照提示信息填写提交信息。本项目只需要填写前三条信息，前两条（影响范围和提交标题）必须填写，第三条（提交描述）可选，当涉及到复杂变动时可以填写。

## 附录教程

### Git的基本使用方法

这里提供一些本项目开发的git使用tips。

推荐使用Visual Studio Code提供的GUI版本管理功能，可以大幅减小Git的学习成本。

**commit**

提交，一次提交会创建一个提交记录，可以在版本管理页的下方查看。

**fetch**

本地的版本信息不一定是最新的，例如选择分支时不一定会出现他人刚在代码仓库发布的分支，这时需要使用`fetch`指令更新仓库信息。建议在Visual Studio Code中开启自动定期`fetch`。

**push**

将本地的修改（本地的所有新提交）同步到远程代码仓库中，如果左下角的*版本状态*显示你的版本领先于远程版本，则可以直接推送，否则需要先进行`pull`操作。

**pull**

将远程代码仓库的修改同步到本地，如果远程与本地提交有冲突，会触发`merge`流程，这时需要手工将代码中的冲突消除。

如果在`pull`本地存在未提交的修改并且不想提交，则需要使用`stash`暂存功能将代码暂时保存，在`pull`后`apply latest stash`将暂存内容应用到现在的代码中，如果存在冲突，解决冲突的流程会在这时候进行。

**checkout**

切换分支，直接点击Visual Studio Code左下角的分支名称，即可选择需要切换到的分支。

> 注意：切换分支前需要将本地未提交的修改提交，或者`stash`暂存当前分支的修改

**merge**

在Visual Studio Code版本管理页面中选择*分支/合并分支*，选择*合并自*的分支，可以将*合并自*分支的提交合并到本分支，这样就可以在网页上创建合并请求了。