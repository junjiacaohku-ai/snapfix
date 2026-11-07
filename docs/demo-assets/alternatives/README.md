# 没有设备时的演示替代方案

用公开外观图演示页面和接口，用手动错误码检查E24流程，用暗化／模糊图检查重拍。素材已准备并跑过后端；原要求中的真实故障识别验收仍需实拍，或者由组长确认调整课堂演示范围。

## 六场景怎么跑

| 场景 | 已准备的替代材料 | 能检查什么 | 暂时不能说明什么 |
|---|---|---|---|
| S1 路由器 | 3张TP-Link公开照片，`router-01..03.jpg` | 上传、诊断卡、外部检查步骤 | 是否从照片识别出红灯故障 |
| S2 洗碗机E24 | 3张Bosch公开照片，`e24-01..03.jpg`；手动输入Bosch／博世＋E24／E:24 | 类别展示、错误码查询、型号不明时转专业处理 | 照片里真的显示E24，或OCR识别正确 |
| S3 BILLY | 3张书架公开照片，`billy-01..03.jpg` | 步骤、来源和防倾倒提醒 | 能否判断组装错误或缺少零件 |
| S4 微波炉 | 3张公开照片，`microwave-01..03.jpg` | 高危场景的拒答状态 | 对真实内部故障的诊断能力 |
| S5 重拍 | 3张暗化图和3张模糊图，`router-dark-*`／`router-blur-*` | 实际图片质量检查和重拍提示 | 各种手机／拍摄环境下的可靠性 |
| S6 报修 | 复用S1照片，勾选已完成步骤后生成中英文报修 | 反馈保存、双语草稿、档案读取 | 手机复制／系统分享／附件是否正常 |

共18个不同输入文件，S6复用S1照片。Bosch的3张照片来自同一作者、同一设备的不同视角；TP-Link的3张也属于同一组，不能当作独立故障样本统计。

## 来源和处理

新增的三张Bosch照片由 **Yelderberry** 拍摄，许可为 [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)。保存的是Commons提供的960×1280版本，没有添加错误码、红灯或其他故障。原图为4284×5712，下载链接、原图链接、校验值见 `sources.json`。

- [Bosch照片1](https://commons.wikimedia.org/wiki/File:Bosch_Dishwasher_2026-08-23_1.jpg)
- [Bosch照片2](https://commons.wikimedia.org/wiki/File:Bosch_Dishwasher_2026-08-23_2.jpg)
- [Bosch照片3](https://commons.wikimedia.org/wiki/File:Bosch_Dishwasher_2026-08-23_3.jpg)

其他外观照片沿用 `../public/sources.json` 中的作者和许可。处理图选自已经完成的13张原图实验：亮度乘0.15，或在原尺寸上做半径12像素的高斯模糊，保存无损PNG。每张文件的作者、许可、来源和处理方式都合并到本目录的 `manifest.json`，打包时一起提供。

继续找图片可以在Google图片使用“使用权限”筛选，再回到原站核对来源和许可，不能只保存搜索结果缩略图。方法见 [Google官方说明](https://support.google.com/websearch/answer/29508?hl=en)。E24含义用 [Bosch官方说明](https://www.bosch-home.com/us/owner-support/dishwashers/error-codes/e24) 和语料中的官方手册核对。

## 给接接口的队友

图片接口为 `POST /api/analyze/image`，字段名 `file`。本分支按上传文件名选择离线场景，因此打包文件已取好 `router-*`、`e24-*`、`billy-*`、`microwave-*` 的名字。前端压缩上传时需保留场景名，或提供明确的演示场景选择；普通相册随机文件名目前不能自动识别设备。图片质量检查仍然读取实际像素。

手动输入接口为 `POST /api/diagnose/manual`：

```json
{"brand":"Bosch","error_code":"E:24"}
```

预期返回 `dishwasher`、`professional`、`model: null`。`E240`或未知品牌返回200、空步骤和明确的无引用提示，不能误匹配成E24。报修草稿不自动附照片，手机分享时由使用者另附。

## 检查记录和复跑

本轮26项检查全部通过：21次图片流程、3种有效手动输入和2个错误输入。每个场景分别运行；S6还检查反馈、中英文草稿和档案读取。没有调用真实视觉模型。

在 `server/` 安装现有依赖后运行：

```sh
python experiments/evaluate_demo_alternatives.py
python experiments/package_demo_assets.py --output ../snapfix-demo-inputs.zip
```

结果保存在 `server/experiments/demo-alternative-results.json`。打包仅复制已核对的18个文件，保留作者和处理说明，不改动原图或日常数据库。

这些材料可以先用于接口联调和离线演示。后续等完整App接好，再补手机拍摄、重拍、分享和真实耗时；真实故障照片由有设备的队友补充。若本次课堂只采用替代方案，请组长在PR里确认，原计划中的实拍要求暂不勾选完成。
