import 'dart:convert';
import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';

import 'api.dart';
import 'style.dart';
import 'report_page.dart';

/// Native Flutter rendering of Rachel's approved AI Studio interaction design.
class SnapFixProductApp extends StatelessWidget {
  const SnapFixProductApp({this.api, this.initialSessionId, super.key});
  final ProductApi? api;
  final String? initialSessionId;
  @override
  Widget build(BuildContext context) => MaterialApp(
    title: 'SnapFix 随手修',
    debugShowCheckedModeBanner: false,
    theme: productTheme(),
    builder: (context, child) => ColoredBox(
      color: Colors.black,
      child: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 430),
          child: child,
        ),
      ),
    ),
    home: ProductHome(api: api, initialSessionId: initialSessionId),
  );
}

class ProductHome extends StatefulWidget {
  const ProductHome({this.api, this.initialSessionId, super.key});
  final ProductApi? api;
  final String? initialSessionId;
  @override
  State<ProductHome> createState() => _ProductHomeState();
}

class _ProductHomeState extends State<ProductHome> {
  late final ProductApi api = widget.api ?? ProductApi();
  String screen = 'splash',
      filter = '全部',
      dimension = 'appliance',
      query = '',
      statusFilter = 'all';
  bool busy = false, sourceOpen = false, casePreview = false;
  Json? session, selectedCase;
  Uint8List? selectedPhoto;
  String selectedName = 'photo.jpg';
  int stepIndex = 0;
  Future<List<Json>>? listing;
  final picker = ImagePicker();
  final codeEditor = TextEditingController();
  final caseCodeEditor = TextEditingController();
  final followUpEditor = TextEditingController();
  @override
  void initState() {
    super.initState();
    if (widget.initialSessionId != null) {
      screen = 'camera';
      WidgetsBinding.instance.addPostFrameCallback((_) {
        run(() async {
          accept(await api.importV1(widget.initialSessionId!));
        });
      });
      return;
    }
    Future<void>.delayed(const Duration(milliseconds: 1100), () {
      if (mounted) setState(() => screen = 'camera');
    });
  }

  @override
  void dispose() {
    codeEditor.dispose();
    caseCodeEditor.dispose();
    followUpEditor.dispose();
    if (widget.api == null) api.close();
    super.dispose();
  }

  void message(Object value) {
    if (mounted) {
      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text('$value')));
    }
  }

  Future<void> run(Future<void> Function() fn) async {
    if (busy) return;
    setState(() => busy = true);
    try {
      await fn();
    } catch (e) {
      message(e);
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  void go(String value) {
    setState(() {
      screen = value;
      if (value == 'my_repairs') listing = api.list();
      if (value == 'collection') reloadCases();
    });
  }

  void reloadCases() {
    listing = api.cases(
      q: query,
      brand: dimension == 'brand' && filter != '全部' ? filter : '',
      appliance: dimension == 'appliance' && filter != '全部' ? filter : '',
    );
  }

  void accept(Json value, {String page = 'diagnosis'}) {
    if (mounted) {
      setState(() {
        session = value;
        screen = page;
        casePreview = false;
        sourceOpen = false;
      });
    }
  }

  Future<void> pick(ImageSource source) async {
    await run(() async {
      final file = await picker.pickImage(
        source: source,
        maxWidth: 1600,
        imageQuality: 85,
      );
      if (file == null) return;
      final bytes = await file.readAsBytes();
      if (bytes.length > 5 * 1024 * 1024) {
        throw const ProductFailure('请选择不超过 5MB 的照片。');
      }
      if (mounted) {
        setState(() {
          selectedPhoto = bytes;
          selectedName = file.name;
          screen = 'preview';
        });
      }
    });
  }

  Widget photo(String? value, {double height = 180}) {
    final placeholder = Container(
      height: height,
      color: panel,
      child: const Center(
        child: Icon(Icons.home_repair_service_outlined, size: 40, color: muted),
      ),
    );
    if (value == null || value.isEmpty) return placeholder;
    if (value.startsWith('data:')) {
      try {
        return Image.memory(
          base64Decode(value.split(',').last),
          height: height,
          width: double.infinity,
          fit: BoxFit.cover,
          errorBuilder: (_, e, s) => placeholder,
        );
      } catch (_) {
        return placeholder;
      }
    }
    return Image.network(
      value,
      height: height,
      width: double.infinity,
      fit: BoxFit.cover,
      errorBuilder: (_, e, s) => placeholder,
    );
  }

  Future<void> previewEntry() async {
    await showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      builder: (ctx) => SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(24, 0, 24, 24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              heading('预览使用流程'),
              gap(8),
              const Text(
                '这里使用预设数据体验操作流程，预览记录与自己的维修记录分开保存。',
                style: TextStyle(fontSize: 13, color: muted),
              ),
              gap(),
              for (final entry in {
                'e24': '洗碗机 E24',
                'router': '路由器外部检查',
                'billy': 'IKEA BILLY',
                'microwave': '微波炉安全拒答',
              }.entries)
                action(entry.value, () {
                  Navigator.pop(ctx);
                  run(() async {
                    final value = await api.scenario(entry.key);
                    api.demo = true;
                    accept(value);
                  });
                }, primary: false),
              if (api.demo)
                action('退出预览，返回正式使用', () {
                  api.demo = false;
                  Navigator.pop(ctx);
                  go('camera');
                }),
            ],
          ),
        ),
      ),
    );
  }

  Future<void> codeEntry() async {
    final code = codeEditor..clear();
    String brand = '未知', category = '洗碗机';
    final data = await showModalBottomSheet<Json>(
      context: context,
      isScrollControlled: true,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, local) => Padding(
          padding: EdgeInsets.fromLTRB(
            24,
            0,
            24,
            24 + MediaQuery.viewInsetsOf(ctx).bottom,
          ),
          child: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                heading('输入错误代码'),
                gap(),
                TextField(
                  key: const Key('error-code'),
                  controller: code,
                  textCapitalization: TextCapitalization.characters,
                  decoration: const InputDecoration(hintText: '输入代码 (如 E24)'),
                ),
                gap(),
                DropdownButtonFormField<String>(
                  initialValue: brand,
                  decoration: const InputDecoration(labelText: '品牌'),
                  items: [
                    for (final v in [
                      '未知',
                      'Bosch / 博世',
                      'Siemens / 西门子',
                      'Daikin / 大金',
                      'Dyson / 戴森',
                    ])
                      DropdownMenuItem(value: v, child: Text(v)),
                  ],
                  onChanged: (v) => local(() => brand = v!),
                ),
                gap(),
                DropdownButtonFormField<String>(
                  initialValue: category,
                  decoration: const InputDecoration(labelText: '电器'),
                  items: [
                    for (final v in ['洗碗机', '空调', '吸尘器', '微波炉', '常用电器'])
                      DropdownMenuItem(value: v, child: Text(v)),
                  ],
                  onChanged: (v) => local(() => category = v!),
                ),
                gap(),
                action('立即分析', () {
                  if (code.text.trim().isEmpty) {
                    message('请输入错误代码');
                    return;
                  }
                  Navigator.pop(ctx, {
                    'brand': brand == '未知' ? '' : brand,
                    'category': category,
                    'code': code.text.trim().toUpperCase(),
                  });
                }),
              ],
            ),
          ),
        ),
      ),
    );
    if (data != null) {
      await run(() async {
        accept(
          await api.diagnose(
            brand: data['brand'] as String,
            category: data['category'] as String,
            code: data['code'] as String,
          ),
        );
      });
    }
  }

  Widget camera() => Column(
    children: [
      Expanded(
        child: Stack(
          fit: StackFit.expand,
          children: [
            Container(
              decoration: const BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                  colors: [panel, ink],
                ),
              ),
            ),
            const Positioned(
              top: 20,
              left: 24,
              child: Text(
                'SnapFix',
                style: TextStyle(fontSize: 24, fontWeight: FontWeight.w800),
              ),
            ),
            Center(
              child: Container(
                width: 250,
                height: 250,
                decoration: BoxDecoration(
                  border: Border.all(color: Colors.white24),
                  borderRadius: BorderRadius.circular(28),
                ),
                child: IconButton(
                  tooltip: '打开相机',
                  onPressed: () => pick(ImageSource.camera),
                  icon: const Icon(
                    Icons.camera_alt_outlined,
                    size: 48,
                    color: Colors.white54,
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
      Padding(
        padding: const EdgeInsets.symmetric(horizontal: 24),
        child: action(
          '输入错误代码排查',
          codeEntry,
          primary: false,
          key: const Key('open-code'),
        ),
      ),
      Padding(
        padding: const EdgeInsets.fromLTRB(24, 12, 24, 14),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            IconButton.filledTonal(
              tooltip: '相册',
              onPressed: () => pick(ImageSource.gallery),
              icon: const Icon(Icons.photo_library_outlined, color: amber),
            ),
            SizedBox(
              width: 74,
              height: 74,
              child: OutlinedButton(
                style: OutlinedButton.styleFrom(
                  side: const BorderSide(color: Colors.white, width: 3),
                  shape: const CircleBorder(),
                  padding: const EdgeInsets.all(5),
                ),
                onPressed: () => pick(ImageSource.camera),
                child: Container(
                  decoration: const BoxDecoration(
                    color: Colors.white,
                    shape: BoxShape.circle,
                  ),
                ),
              ),
            ),
            const SizedBox(width: 48),
          ],
        ),
      ),
    ],
  );
  Widget previewPhoto() => ListView(
    padding: const EdgeInsets.all(24),
    children: [
      heading('确认照片'),
      gap(),
      ClipRRect(
        borderRadius: BorderRadius.circular(24),
        child: Image.memory(selectedPhoto!, height: 300, fit: BoxFit.contain),
      ),
      gap(),
      const ProductCard(child: Text('请确认设备主体、错误代码与光线清晰可见。')),
      gap(),
      action(
        '开始诊断',
        () => run(() async {
          accept(await api.photo(selectedPhoto!, selectedName));
        }),
      ),
      action('重新选择', () => pick(ImageSource.gallery), primary: false),
    ],
  );
  Widget metric(String value, String label, {Color color = Colors.white}) =>
      Expanded(
        child: Column(
          children: [
            Text(
              value,
              style: TextStyle(
                color: color,
                fontWeight: FontWeight.bold,
                fontSize: 18,
              ),
            ),
            Text(label, style: const TextStyle(color: muted, fontSize: 12)),
          ],
        ),
      );
  Widget diagnosis() {
    final value = session!, rev = revision(value), steps = revisionSteps(value);
    final danger = rev['is_high_risk'] == true;
    final demo = value['mode'] == 'demo';
    return Column(
      children: [
        Expanded(
          child: ListView(
            padding: const EdgeInsets.all(24),
            children: [
              Text(
                '${value['category']} ${value['error_code'] ?? ''}',
                style: const TextStyle(color: muted),
              ),
              gap(6),
              heading('${value['brand'] ?? ''} ${value['category']}'),
              Text(
                '${value['model'] ?? '型号待机身铭牌确认'}',
                style: const TextStyle(color: muted, fontSize: 13),
              ),
              gap(),
              ProductCard(
                child: Row(
                  children: [
                    metric('${steps.length}', danger ? '自行步骤' : '排查步骤'),
                    metric(
                      danger
                          ? '极高'
                          : demo
                          ? '15m'
                          : '待核实',
                      danger ? '电击风险' : '预计耗时',
                      color: danger ? Colors.redAccent : Colors.white,
                    ),
                    metric(
                      danger
                          ? '阻断'
                          : demo
                          ? '低风险'
                          : '待评估',
                      danger ? '安全策略' : '操作难度',
                      color: danger
                          ? Colors.redAccent
                          : demo
                          ? const Color(0xff34d399)
                          : amber,
                    ),
                  ],
                ),
              ),
              gap(),
              if (danger)
                ProductCard(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        '高压触电危险 · 严禁自行拆解',
                        style: TextStyle(
                          color: Colors.redAccent,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                      gap(8),
                      Text('${rev['high_risk_reason'] ?? '请联系专业人员。'}'),
                    ],
                  ),
                )
              else
                ProductCard(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        '故障成因',
                        style: TextStyle(color: muted, fontSize: 13),
                      ),
                      gap(6),
                      Text('${rev['explanation']}'),
                    ],
                  ),
                ),
              if (!danger) ...[
                gap(),
                ProductCard(
                  borderColor: amber.withValues(alpha: .35),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        rev['suggestion'] == 'self_check'
                            ? '建议优先自行排查'
                            : rev['suggestion'] == 'contact_landlord'
                            ? '建议联系房东安排检修'
                            : '建议联系专业人员核实',
                        style: const TextStyle(fontWeight: FontWeight.w700),
                      ),
                      gap(6),
                      Text(
                        rev['suggestion'] == 'self_check'
                            ? (demo
                                  ? '常规滤网异物堵塞或卡扣脱开，步骤安全可控，无需破拆。'
                                  : '请先核对实际设备、型号和适用的说明书。')
                            : '诊断信息或适用型号尚需确认，请联系专业人员核实。',
                        style: const TextStyle(
                          fontSize: 14,
                          color: Colors.white70,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ],
          ),
        ),
        Padding(
          padding: const EdgeInsets.all(20),
          child: Column(
            children: [
              if (steps.isNotEmpty && !danger)
                action('开始自行排查 (${steps.length} 步)', () => go('overview')),
              action(
                steps.isNotEmpty && !danger
                    ? '转交报修助手 (房东 / 师傅)'
                    : '生成报修说明 (联系房东 / 师傅)',
                () => go('report'),
                primary: steps.isEmpty || danger,
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget collection() => Column(
    children: [
      Padding(
        padding: const EdgeInsets.fromLTRB(24, 8, 24, 8),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(child: heading('案例合集')),
                IconButton(
                  tooltip: '切换维度',
                  onPressed: () {
                    setState(() {
                      dimension = dimension == 'brand' ? 'appliance' : 'brand';
                      filter = '全部';
                      reloadCases();
                    });
                  },
                  icon: const Icon(Icons.tune),
                ),
              ],
            ),
            const Text(
              '真实设备排查与解决记录',
              style: TextStyle(color: muted, fontSize: 13),
            ),
            gap(),
            TextField(
              key: const Key('case-search'),
              decoration: const InputDecoration(
                hintText: '搜索设备、故障或代码...',
                prefixIcon: Icon(Icons.search),
              ),
              onChanged: (v) => setState(() {
                query = v;
                reloadCases();
              }),
            ),
            gap(8),
            SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: Row(
                children: [
                  for (final tag
                      in dimension == 'brand'
                          ? ['全部', 'Bosch / 博世', 'Siemens / 西门子', 'Dyson / 戴森']
                          : ['全部', '洗碗机', '吸尘器', '破壁机', '空调', '微波炉'])
                    Padding(
                      padding: const EdgeInsets.only(right: 6),
                      child: ChoiceChip(
                        label: Text(tag),
                        selected: filter == tag,
                        onSelected: (_) => setState(() {
                          filter = tag;
                          reloadCases();
                        }),
                      ),
                    ),
                ],
              ),
            ),
          ],
        ),
      ),
      Expanded(
        child: records(
          (rows) => ListView(
            padding: const EdgeInsets.all(24),
            children: [
              for (final item in rows)
                Padding(
                  padding: const EdgeInsets.only(bottom: 16),
                  child: InkWell(
                    borderRadius: BorderRadius.circular(22),
                    onTap: () {
                      selectedCase = item;
                      go('case');
                    },
                    child: ProductCard(
                      padding: EdgeInsets.zero,
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          ClipRRect(
                            borderRadius: const BorderRadius.vertical(
                              top: Radius.circular(22),
                            ),
                            child: photo(item['image_url'] as String?),
                          ),
                          Padding(
                            padding: const EdgeInsets.all(16),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  '${item['brand']} · ${item['appliance']}',
                                  style: const TextStyle(
                                    color: muted,
                                    fontSize: 12,
                                  ),
                                ),
                                gap(4),
                                Text(
                                  '${item['title']}',
                                  style: const TextStyle(
                                    fontWeight: FontWeight.w700,
                                  ),
                                ),
                                gap(6),
                                Text(
                                  '${item['problem_description']}',
                                  maxLines: 3,
                                  overflow: TextOverflow.ellipsis,
                                  style: const TextStyle(
                                    fontSize: 14,
                                    color: Colors.white70,
                                  ),
                                ),
                                gap(8),
                                if (item['is_resolved'] == true)
                                  const Text(
                                    '已验证解决',
                                    style: TextStyle(
                                      color: Colors.greenAccent,
                                      fontSize: 12,
                                    ),
                                  ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
            ],
          ),
        ),
      ),
    ],
  );
  Widget records(Widget Function(List<Json>) render) =>
      FutureBuilder<List<Json>>(
        future: listing,
        builder: (ctx, snapshot) {
          if (snapshot.connectionState != ConnectionState.done) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snapshot.hasError) {
            return Center(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text('${snapshot.error}'),
                    action(
                      '重试',
                      () => setState(() {
                        if (screen == 'collection') {
                          reloadCases();
                        } else {
                          listing = api.list();
                        }
                      }),
                    ),
                  ],
                ),
              ),
            );
          }
          final rows = snapshot.data ?? [];
          return render(rows);
        },
      );
  Widget caseDetail() {
    final item = selectedCase!;
    return Column(
      children: [
        Expanded(
          child: ListView(
            children: [
              photo(item['image_url'] as String?, height: 230),
              Padding(
                padding: const EdgeInsets.all(24),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      '${item['brand']} · ${item['appliance']}',
                      style: const TextStyle(color: amber, fontSize: 13),
                    ),
                    heading('${item['title']}'),
                    gap(),
                    ProductCard(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text('故障现象', style: TextStyle(color: muted)),
                          Text('${item['problem_description']}'),
                        ],
                      ),
                    ),
                    gap(),
                    ProductCard(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text('成因与处理方案', style: TextStyle(color: muted)),
                          Text('${item['cause_analysis']}'),
                          gap(),
                          Text(
                            '方案摘要：${item['solution_summary']}',
                            style: const TextStyle(color: amber),
                          ),
                        ],
                      ),
                    ),
                    gap(),
                    if (item['is_resolved'] == true)
                      ProductCard(
                        child: Text('解决依据\n${item['resolved_evidence']}'),
                      ),
                  ],
                ),
              ),
            ],
          ),
        ),
        Padding(
          padding: const EdgeInsets.all(20),
          child: Column(
            children: [
              action('查看排查步骤 (${(item['steps'] as List).length} 步)', () {
                setState(() {
                  casePreview = true;
                  screen = 'overview';
                });
              }),
              action('比对设备适用性', checkCase, primary: false),
            ],
          ),
        ),
      ],
    );
  }

  Future<void> checkCase() async {
    final code = caseCodeEditor
      ..text = selectedCase!['error_code'] as String? ?? '';
    String? advice;
    bool checking = false;
    await showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, local) => Padding(
          padding: EdgeInsets.fromLTRB(
            24,
            0,
            24,
            24 + MediaQuery.viewInsetsOf(ctx).bottom,
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              heading('比对设备适用性'),
              gap(),
              TextField(
                controller: code,
                decoration: const InputDecoration(hintText: '例如 E24...'),
              ),
              gap(),
              action(
                checking ? '比对中…' : '比对',
                checking
                    ? null
                    : () async {
                        local(() => checking = true);
                        try {
                          final result = await api.check(
                            selectedCase!['id'] as String,
                            code.text,
                          );
                          if (ctx.mounted) {
                            local(() => advice = result['advice'] as String);
                          }
                        } catch (e) {
                          message(e);
                        } finally {
                          if (ctx.mounted) local(() => checking = false);
                        }
                      },
              ),
              if (advice != null) ...[
                Text(advice!),
                action('记录问题，继续核对型号', () {
                  Navigator.pop(ctx);
                  run(() async {
                    accept(
                      await api.diagnose(
                        category: selectedCase!['appliance'] as String,
                        note: '参考案例：${selectedCase!['title']}；实际设备待确认。',
                      ),
                    );
                  });
                }),
              ],
            ],
          ),
        ),
      ),
    );
  }

  List<Json> get shownSteps => casePreview
      ? (selectedCase!['steps'] as List)
            .map((e) => Json.from(e as Map))
            .toList()
      : revisionSteps(session!);
  Widget overview() {
    final steps = shownSteps;
    final demo = casePreview || session?['mode'] == 'demo';
    return Column(
      children: [
        Expanded(
          child: ListView(
            padding: const EdgeInsets.all(24),
            children: [
              heading('排查操作清单'),
              Text(
                '共 ${steps.length} 步 · 操作前务必断开电源',
                style: const TextStyle(color: muted, fontSize: 13),
              ),
              gap(),
              ProductCard(
                child: Row(
                  children: [
                    metric(demo ? '10–15 分钟' : '待核实', '预计耗时'),
                    metric(demo ? '毛巾 / 软毛刷' : '以适用手册为准', '所需工具'),
                  ],
                ),
              ),
              gap(),
              for (var i = 0; i < steps.length; i++)
                Padding(
                  padding: const EdgeInsets.only(bottom: 12),
                  child: ProductCard(
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        CircleAvatar(
                          radius: 14,
                          backgroundColor: amber.withValues(alpha: .15),
                          child: Text(
                            '${i + 1}',
                            style: const TextStyle(color: amber, fontSize: 13),
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                '${steps[i]['title']}',
                                style: const TextStyle(
                                  fontWeight: FontWeight.w700,
                                ),
                              ),
                              gap(6),
                              Text(
                                '${steps[i]['description']}',
                                style: const TextStyle(fontSize: 16),
                              ),
                              if (steps[i]['feedback'] != null)
                                Text(
                                  feedbackLabel(steps[i]['feedback'] as String),
                                  style: const TextStyle(
                                    color: amber,
                                    fontSize: 13,
                                  ),
                                ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
            ],
          ),
        ),
        Padding(
          padding: const EdgeInsets.all(20),
          child: action(
            casePreview
                ? '返回案例详情'
                : steps.isEmpty
                ? '暂无适用步骤，生成报修说明'
                : '开始逐步排查',
            () {
              if (casePreview) {
                casePreview = false;
                go('case');
              } else if (steps.isEmpty) {
                go('report');
              } else {
                stepIndex = steps.indexWhere((s) => s['feedback'] == null);
                if (stepIndex < 0) stepIndex = 0;
                go('guide');
              }
            },
          ),
        ),
      ],
    );
  }

  String feedbackLabel(String v) =>
      {'done': '已完成', 'not_useful': '无改善', 'skipped': '已跳过'}[v] ?? v;
  Future<void> stepFeedback(String value) async {
    await run(() async {
      final steps = revisionSteps(session!);
      final updated = await api.feedback(
        session!['id'] as String,
        steps[stepIndex]['id'] as String,
        value,
      );
      if (!mounted) return;
      setState(() => session = updated);
      if (value == 'not_useful') {
        await followUp();
      } else if (stepIndex + 1 < steps.length) {
        setState(() => stepIndex++);
      } else {
        final yes = await confirm(
          '排查步骤已结束',
          '设备运行是否已恢复正常？',
          yes: '已解决',
          no: '尚未解决',
        );
        if (yes) {
          accept(
            await api.status(session!['id'] as String, 'resolved'),
            page: 'session',
          );
        } else {
          await followUp();
        }
      }
    });
  }

  Future<bool> confirm(
    String title,
    String content, {
    String yes = '确认',
    String no = '取消',
  }) async =>
      await showDialog<bool>(
        context: context,
        builder: (ctx) => AlertDialog(
          title: Text(title),
          content: Text(content),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(ctx, false),
              child: Text(no),
            ),
            FilledButton(
              onPressed: () => Navigator.pop(ctx, true),
              child: Text(yes),
            ),
          ],
        ),
      ) ??
      false;
  Future<void> followUp() async {
    final note = followUpEditor..clear();
    String? photoRef;
    bool submitting = false;
    await showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, local) => Padding(
          padding: EdgeInsets.fromLTRB(
            24,
            0,
            24,
            24 + MediaQuery.viewInsetsOf(ctx).bottom,
          ),
          child: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                heading('步骤未奏效？'),
                gap(),
                const Text('再试一下！补充照片或描述。'),
                gap(),
                TextField(
                  controller: note,
                  minLines: 2,
                  maxLines: 4,
                  decoration: const InputDecoration(hintText: '描述尝试后的现象...'),
                ),
                gap(),
                action(
                  photoRef == null ? '添加照片' : '已附照片',
                  submitting
                      ? null
                      : () async {
                          try {
                            final file = await picker.pickImage(
                              source: ImageSource.gallery,
                              maxWidth: 1600,
                              imageQuality: 85,
                            );
                            if (file == null) return;
                            final bytes = await file.readAsBytes();
                            if (bytes.length > 5 * 1024 * 1024) {
                              throw const ProductFailure('照片不能超过 5MB。');
                            }
                            if (ctx.mounted) {
                              local(() => photoRef = file.name);
                            }
                          } catch (e) {
                            message(e);
                          }
                        },
                  primary: false,
                ),
                action(
                  submitting ? '提交中…' : '确认并再试',
                  submitting
                      ? null
                      : () async {
                          if (note.text.trim().isEmpty && photoRef == null) {
                            message('请补充照片或描述。');
                            return;
                          }
                          local(() => submitting = true);
                          try {
                            final updated = await api.followUp(
                              session!['id'] as String,
                              note.text,
                              photoRef,
                            );
                            if (ctx.mounted) Navigator.pop(ctx);
                            accept(updated, page: 'overview');
                          } catch (e) {
                            message(e);
                            if (ctx.mounted) local(() => submitting = false);
                          }
                        },
                ),
                action(
                  '放弃，去报修了！',
                  submitting
                      ? null
                      : () {
                          Navigator.pop(ctx);
                          go('report');
                        },
                  primary: false,
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget guide() {
    final steps = revisionSteps(session!);
    if (steps.isEmpty) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text('${revision(session!)['explanation']}'),
              action('生成报修说明', () => go('report')),
            ],
          ),
        ),
      );
    }
    final step = steps[stepIndex.clamp(0, steps.length - 1)];
    final source = step['source'] as Map?;
    return Column(
      children: [
        LinearProgressIndicator(
          value: (stepIndex + 1) / steps.length,
          minHeight: 3,
        ),
        Expanded(
          child: ListView(
            padding: const EdgeInsets.all(24),
            children: [
              Text(
                '步骤 ${stepIndex + 1} / ${steps.length}',
                style: const TextStyle(color: amber),
              ),
              gap(),
              heading('${step['title']}'),
              gap(),
              ProductCard(
                child: Text(
                  '${step['description']}',
                  style: const TextStyle(fontSize: 17, height: 1.65),
                ),
              ),
              gap(),
              if (step['caution'] != null)
                ProductCard(
                  child: Text(
                    '${step['caution']}',
                    style: const TextStyle(color: amber),
                  ),
                ),
              gap(),
              ExpansionTile(
                title: const Text('查看说明书来源', style: TextStyle(fontSize: 14)),
                children: [
                  Padding(
                    padding: const EdgeInsets.all(16),
                    child: SelectableText(
                      source?['snippet'] as String? ??
                          '${source?['manual_title'] ?? '当前步骤未提供可核对的引用原文。'}\n${source?['chapter'] ?? ''}',
                    ),
                  ),
                ],
              ),
              gap(),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  TextButton(
                    onPressed: stepIndex > 0
                        ? () => setState(() => stepIndex--)
                        : null,
                    child: const Text('上一步'),
                  ),
                  TextButton(
                    onPressed: stepIndex + 1 < steps.length
                        ? () => setState(() => stepIndex++)
                        : null,
                    child: const Text('下一步'),
                  ),
                ],
              ),
            ],
          ),
        ),
        Padding(
          padding: const EdgeInsets.all(20),
          child: Row(
            children: [
              Expanded(
                child: action(
                  '已完成',
                  busy ? null : () => stepFeedback('done'),
                  key: const Key('feedback-done'),
                ),
              ),
              const SizedBox(width: 6),
              Expanded(
                child: action(
                  '没有效果',
                  busy ? null : () => stepFeedback('not_useful'),
                  primary: false,
                ),
              ),
              const SizedBox(width: 6),
              Expanded(
                child: action(
                  '跳过',
                  busy ? null : () => stepFeedback('skipped'),
                  primary: false,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  String statusName(String value) =>
      {
        'investigating': '排查中',
        'awaiting_repair': '待维修',
        'resolved': '已解决',
      }[value] ??
      value;
  Widget archive() => Column(
    children: [
      Padding(
        padding: const EdgeInsets.fromLTRB(24, 8, 24, 0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            heading('我的维修'),
            gap(8),
            Wrap(
              spacing: 6,
              children: [
                for (final entry in {
                  'all': '全部',
                  'investigating': '排查中',
                  'awaiting_repair': '待维修',
                  'resolved': '已解决',
                }.entries)
                  ChoiceChip(
                    label: Text(entry.value),
                    selected: statusFilter == entry.key,
                    onSelected: (_) => setState(() => statusFilter = entry.key),
                  ),
              ],
            ),
          ],
        ),
      ),
      Expanded(
        child: records((all) {
          final rows = all
              .where(
                (s) => statusFilter == 'all' || s['status'] == statusFilter,
              )
              .toList();
          return RefreshIndicator(
            onRefresh: () async {
              setState(() => listing = api.list());
              await listing;
            },
            child: ListView(
              physics: const AlwaysScrollableScrollPhysics(),
              padding: const EdgeInsets.all(24),
              children: [
                if (rows.isEmpty)
                  const Padding(
                    padding: EdgeInsets.only(top: 80),
                    child: Center(
                      child: Text('暂无维修记录', style: TextStyle(color: muted)),
                    ),
                  ),
                for (final item in rows)
                  Padding(
                    padding: const EdgeInsets.only(bottom: 12),
                    child: Dismissible(
                      key: ValueKey(item['id']),
                      direction: DismissDirection.endToStart,
                      background: Container(
                        alignment: Alignment.centerRight,
                        padding: const EdgeInsets.all(20),
                        color: Colors.redAccent,
                        child: const Icon(Icons.delete_outline),
                      ),
                      onDismissed: (_) => setState(() {}),
                      confirmDismiss: (_) async {
                        if (!await confirm(
                          '删除维修记录？',
                          '删除后无法恢复，报修草稿和步骤反馈也将删除。',
                          yes: '确认删除',
                          no: '保留',
                        )) {
                          return false;
                        }
                        try {
                          await api.delete(item['id'] as String);
                          all.remove(item);
                          return true;
                        } catch (e) {
                          message(e);
                          return false;
                        }
                      },
                      child: InkWell(
                        onTap: () => accept(item, page: 'session'),
                        borderRadius: BorderRadius.circular(22),
                        child: ProductCard(
                          child: Row(
                            children: [
                              const Icon(Icons.build_outlined, color: amber),
                              const SizedBox(width: 14),
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      '${item['device_name']}',
                                      style: const TextStyle(
                                        fontWeight: FontWeight.w700,
                                      ),
                                    ),
                                    Text(
                                      statusName(item['status'] as String),
                                      style: const TextStyle(
                                        color: amber,
                                        fontSize: 13,
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                              const Icon(Icons.chevron_right, color: muted),
                            ],
                          ),
                        ),
                      ),
                    ),
                  ),
              ],
            ),
          );
        }),
      ),
    ],
  );
  Widget sessionDetail() {
    final value = session!, rev = revision(value);
    return ListView(
      padding: const EdgeInsets.all(24),
      children: [
        heading('${value['device_name']}'),
        gap(),
        ProductCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text('维修状态', style: TextStyle(color: muted)),
              Wrap(
                spacing: 6,
                children: [
                  for (final entry in {
                    'investigating': '排查中',
                    'awaiting_repair': '待维修',
                    'resolved': '已解决',
                  }.entries)
                    ChoiceChip(
                      label: Text(entry.value),
                      selected: value['status'] == entry.key,
                      onSelected: (_) => run(() async {
                        if (await confirm(
                          '更改维修状态？',
                          '确认将这条记录标记为${entry.value}？',
                        )) {
                          accept(
                            await api.status(value['id'] as String, entry.key),
                            page: 'session',
                          );
                        }
                      }),
                    ),
                ],
              ),
            ],
          ),
        ),
        gap(),
        ProductCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text('问题描述', style: TextStyle(color: muted)),
              Text('${rev['problem_summary']}'),
              gap(8),
              Text('${rev['explanation']}'),
            ],
          ),
        ),
        gap(),
        for (final r in value['revisions'] as List)
          ProductCard(
            child: ExpansionTile(
              title: Text(
                '第 ${r['revision_number']} 次记录',
                style: const TextStyle(fontSize: 14),
              ),
              children: [
                Text('${r['problem_summary']}'),
                for (final step in r['steps'] as List)
                  ListTile(
                    dense: true,
                    title: Text('${step['title']}'),
                    subtitle: Text(
                      step['feedback'] == null
                          ? '尚未反馈'
                          : feedbackLabel(step['feedback'] as String),
                    ),
                  ),
              ],
            ),
          ),
        gap(),
        action('继续排查步骤', () => go('overview')),
        action('查看或生成报修信', () => go('report'), primary: false),
        action(
          '删除维修记录',
          () => run(() async {
            if (await confirm('删除维修记录？', '删除后无法恢复。', yes: '确认删除', no: '保留')) {
              await api.delete(value['id'] as String);
              go('my_repairs');
            }
          }),
          primary: false,
        ),
      ],
    );
  }

  void back() {
    if (screen == 'report') {
      go('session');
    } else if (screen == 'case') {
      go('collection');
    } else if (screen == 'guide') {
      go('overview');
    } else if (screen == 'overview') {
      final next = casePreview ? 'case' : 'diagnosis';
      casePreview = false;
      go(next);
    } else if (screen == 'session') {
      go('my_repairs');
    } else {
      go('camera');
    }
  }

  @override
  Widget build(BuildContext context) {
    if (screen == 'splash') {
      return Scaffold(
        body: Center(
          child: TweenAnimationBuilder<double>(
            tween: Tween(begin: .85, end: 1),
            duration: const Duration(milliseconds: 800),
            curve: Curves.easeOutBack,
            builder: (context, value, child) =>
                Transform.scale(scale: value, child: child),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Container(
                  width: 80,
                  height: 80,
                  decoration: BoxDecoration(
                    color: amber,
                    borderRadius: BorderRadius.circular(24),
                  ),
                  child: const Icon(Icons.build_rounded, color: ink, size: 36),
                ),
                gap(),
                const Text(
                  'SnapFix 随手修',
                  style: TextStyle(fontSize: 28, fontWeight: FontWeight.w800),
                ),
                const Text('先搞懂 · 再决定', style: TextStyle(color: muted)),
              ],
            ),
          ),
        ),
      );
    }
    final root = ['camera', 'collection', 'my_repairs'].contains(screen);
    final title =
        {
          'preview': '确认照片',
          'diagnosis': '诊断结果',
          'overview': '排查步骤',
          'guide': '分步指导',
          'case': '案例详情',
          'session': '维修档案',
          'report': '报修助手',
        }[screen] ??
        '';
    Widget body = switch (screen) {
      'camera' => camera(),
      'preview' => previewPhoto(),
      'diagnosis' => diagnosis(),
      'collection' => collection(),
      'case' => caseDetail(),
      'overview' => overview(),
      'guide' => guide(),
      'my_repairs' => archive(),
      'session' => sessionDetail(),
      'report' => ProductReportPage(
        api: api,
        session: session!,
        onUpdated: (v) => setState(() => session = v),
      ),
      _ => camera(),
    };
    return Scaffold(
      appBar: AppBar(
        leading: root
            ? null
            : IconButton(
                tooltip: '返回',
                onPressed: back,
                icon: const Icon(Icons.chevron_left),
              ),
        title: Text(title),
        actions: [
          TextButton(
            key: const Key('workflow-preview'),
            onPressed: busy ? null : previewEntry,
            child: Text(
              api.demo ? '退出流程预览' : '预览使用流程',
              style: const TextStyle(fontSize: 12),
            ),
          ),
        ],
      ),
      body: SafeArea(
        child: Stack(
          children: [
            Positioned.fill(child: body),
            if (busy)
              const Positioned.fill(
                child: ColoredBox(
                  color: Color(0x99020617),
                  child: Center(child: CircularProgressIndicator()),
                ),
              ),
          ],
        ),
      ),
      bottomNavigationBar: root
          ? SafeArea(
              child: Padding(
                padding: const EdgeInsets.fromLTRB(70, 4, 70, 12),
                child: Container(
                  decoration: BoxDecoration(
                    color: panel,
                    borderRadius: BorderRadius.circular(40),
                    border: Border.all(color: line),
                  ),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                    children: [
                      IconButton(
                        tooltip: '合集',
                        onPressed: () => go('collection'),
                        icon: Icon(
                          Icons.search,
                          color: screen == 'collection' ? amber : muted,
                        ),
                      ),
                      IconButton.filled(
                        tooltip: '拍照诊断',
                        onPressed: () => go('camera'),
                        icon: const Icon(Icons.camera_alt_outlined),
                      ),
                      IconButton(
                        tooltip: '我的维修档案',
                        onPressed: () => go('my_repairs'),
                        icon: Icon(
                          Icons.history,
                          color: screen == 'my_repairs' ? amber : muted,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            )
          : null,
    );
  }
}
