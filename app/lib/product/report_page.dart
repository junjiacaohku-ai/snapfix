import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:share_plus/share_plus.dart';

import 'api.dart';
import 'style.dart';

class ProductReportPage extends StatefulWidget {
  const ProductReportPage({
    required this.api,
    required this.session,
    required this.onUpdated,
    super.key,
  });
  final ProductApi api;
  final Json session;
  final ValueChanged<Json> onUpdated;
  @override
  State<ProductReportPage> createState() => _ReportState();
}

class _ReportState extends State<ProductReportPage> {
  final editor = TextEditingController();
  final drafts = <String, String>{};
  String recipient = 'landlord', lang = 'zh';
  bool loading = true, saving = false, editing = false;
  int requestNumber = 0;
  String? error;
  String get draftKey => '${recipient}_$lang';
  @override
  void initState() {
    super.initState();
    load();
  }

  @override
  void dispose() {
    editor.dispose();
    super.dispose();
  }

  void message(Object value) {
    if (mounted) {
      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text('$value')));
    }
  }

  Future<void> load() async {
    final serial = ++requestNumber;
    final key = draftKey;
    if (drafts.containsKey(key)) {
      setState(() {
        editor.text = drafts[key]!;
        loading = false;
        error = null;
      });
      return;
    }
    setState(() {
      loading = true;
      error = null;
    });
    try {
      final report = await widget.api.report(
        widget.session['id'] as String,
        recipient,
        lang,
      );
      if (!mounted || serial != requestNumber) return;
      setState(() {
        editor.text = report['content'] as String;
        loading = false;
      });
    } catch (e) {
      if (mounted && serial == requestNumber) {
        setState(() {
          loading = false;
          error = '$e';
        });
      }
    }
  }

  void select({String? who, String? language}) {
    if (editing) drafts[draftKey] = editor.text;
    setState(() {
      recipient = who ?? recipient;
      lang = language ?? lang;
      editing = false;
    });
    load();
  }

  Future<void> resetTemplate() async {
    final serial = ++requestNumber;
    final key = draftKey;
    setState(() => loading = true);
    try {
      final report = await widget.api.template(
        widget.session['id'] as String,
        recipient,
        lang,
      );
      if (!mounted || serial != requestNumber) return;
      setState(() {
        editor.text = report['content'] as String;
        drafts[key] = editor.text;
        editing = true;
        loading = false;
        error = null;
      });
    } catch (e) {
      if (mounted && serial == requestNumber) {
        setState(() => loading = false);
        message(e);
      }
    }
  }

  Future<void> save() async {
    if (saving || loading) return;
    setState(() => saving = true);
    try {
      await widget.api.save(
        widget.session['id'] as String,
        recipient,
        lang,
        editor.text,
      );
      drafts[draftKey] = editor.text;
      if (!mounted) return;
      message('草稿已保存');
      if (widget.session['status'] == 'investigating') {
        final yes = await showDialog<bool>(
          context: context,
          builder: (ctx) => AlertDialog(
            title: const Text('草稿已保存'),
            content: const Text('是否将当前维修状态标记为待维修？'),
            actions: [
              TextButton(
                onPressed: () => Navigator.pop(ctx, false),
                child: const Text('保持排查中'),
              ),
              FilledButton(
                onPressed: () => Navigator.pop(ctx, true),
                child: const Text('确认标记为待维修'),
              ),
            ],
          ),
        );
        if (yes == true) {
          final updated = await widget.api.status(
            widget.session['id'] as String,
            'awaiting_repair',
          );
          widget.onUpdated(updated);
        }
      }
    } catch (e) {
      message(e);
    } finally {
      if (mounted) setState(() => saving = false);
    }
  }

  Future<void> copy() async {
    try {
      await Clipboard.setData(ClipboardData(text: editor.text));
      message('已复制');
    } catch (_) {
      message('复制未成功，请选中文字手动复制。');
    }
  }

  Future<void> share() async {
    try {
      final box = context.findRenderObject() as RenderBox?;
      await SharePlus.instance.share(
        ShareParams(
          text: editor.text,
          subject: 'SnapFix 报修说明',
          sharePositionOrigin: box == null
              ? null
              : box.localToGlobal(Offset.zero) & box.size,
        ),
      );
    } catch (_) {
      message('分享未成功，请使用复制全文。');
    }
  }

  @override
  Widget build(BuildContext context) => Column(
    children: [
      Expanded(
        child: ListView(
          padding: const EdgeInsets.all(24),
          children: [
            heading('报修文案'),
            const Text(
              '一键生成结构化故障陈述与诉求',
              style: TextStyle(fontSize: 13, color: muted),
            ),
            gap(),
            Wrap(
              spacing: 6,
              children: [
                for (final entry in {
                  'landlord': '房东',
                  'technician': '维修师傅',
                  'after_sales': '官方售后',
                }.entries)
                  ChoiceChip(
                    label: Text(entry.value),
                    selected: recipient == entry.key,
                    onSelected: saving ? null : (_) => select(who: entry.key),
                  ),
              ],
            ),
            gap(),
            Wrap(
              spacing: 8,
              crossAxisAlignment: WrapCrossAlignment.center,
              children: [
                ChoiceChip(
                  label: const Text('中文'),
                  selected: lang == 'zh',
                  onSelected: saving ? null : (_) => select(language: 'zh'),
                ),
                ChoiceChip(
                  label: const Text('English'),
                  selected: lang == 'en',
                  onSelected: saving ? null : (_) => select(language: 'en'),
                ),
                TextButton(
                  onPressed: loading || saving ? null : resetTemplate,
                  child: const Text('重置模板'),
                ),
              ],
            ),
            gap(),
            if (loading)
              const Center(child: CircularProgressIndicator())
            else if (error != null) ...[
              Text(error!),
              action('重试', load),
            ] else
              ProductCard(
                child: TextField(
                  key: const Key('report-editor'),
                  controller: editor,
                  minLines: 12,
                  maxLines: null,
                  style: const TextStyle(fontSize: 15, height: 1.65),
                  decoration: const InputDecoration(
                    border: InputBorder.none,
                    enabledBorder: InputBorder.none,
                    filled: false,
                    contentPadding: EdgeInsets.zero,
                  ),
                  onChanged: (_) {
                    editing = true;
                    drafts[draftKey] = editor.text;
                  },
                ),
              ),
          ],
        ),
      ),
      Padding(
        padding: const EdgeInsets.fromLTRB(20, 8, 20, 20),
        child: Row(
          children: [
            Expanded(
              child: action(
                saving ? '保存中…' : '存草稿',
                loading || saving || error != null ? null : save,
                primary: false,
                key: const Key('save-draft'),
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: action(
                '复制全文',
                loading || error != null ? null : copy,
                primary: false,
                key: const Key('copy-report'),
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: action('分享', loading || error != null ? null : share),
            ),
          ],
        ),
      ),
    ],
  );
}
