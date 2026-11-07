import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';

import '../../theme/snapfix_theme.dart';
import '../../widgets/snapfix_button.dart';
import '../../widgets/snapfix_card.dart';

class ScanPreviewScreen extends StatelessWidget {
  const ScanPreviewScreen({this.image, super.key});

  final XFile? image;

  void _showW1Dialog(BuildContext context) {
    showDialog<void>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('W1 主链路已跑通'),
        content: const Text('首页 → 扫描 → 预览已经可用。分析中与诊断结果将在 FE-1 的 W2 任务中接入真实管线。'),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(dialogContext).pop(),
            child: const Text('知道了'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('确认照片')),
      body: SafeArea(
        top: false,
        child: SingleChildScrollView(
          padding: const EdgeInsets.fromLTRB(20, 8, 20, 28),
          child: Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 680),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    '检查照片质量',
                    style: Theme.of(context).textTheme.headlineMedium,
                  ),
                  const SizedBox(height: 6),
                  const Text(
                    '主体清楚且信息完整时，诊断会更稳定。',
                    style: TextStyle(color: SnapFixColors.sub),
                  ),
                  const SizedBox(height: 18),
                  _PhotoStage(image: image),
                  const SizedBox(height: 18),
                  const _QualityChecks(),
                  const SizedBox(height: 18),
                  const _PrivacyNote(),
                  const SizedBox(height: 20),
                  SnapFixButton(
                    label: '开始诊断',
                    icon: Icons.auto_awesome_rounded,
                    onPressed: () => _showW1Dialog(context),
                  ),
                  const SizedBox(height: 8),
                  SnapFixButton(
                    label: '重新选择',
                    tone: SnapFixButtonTone.ghost,
                    onPressed: () => Navigator.of(context).pop(),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _PhotoStage extends StatelessWidget {
  const _PhotoStage({this.image});

  final XFile? image;

  @override
  Widget build(BuildContext context) {
    return ClipRRect(
      borderRadius: BorderRadius.circular(24),
      child: AspectRatio(
        aspectRatio: 0.92,
        child: image == null
            ? const _DemoPhoto()
            : FutureBuilder<Uint8List>(
                future: image!.readAsBytes(),
                builder: (context, snapshot) {
                  if (snapshot.connectionState != ConnectionState.done) {
                    return const _PhotoLoading();
                  }
                  if (snapshot.hasError || snapshot.data == null) {
                    return const _PhotoError();
                  }
                  return Image.memory(
                    snapshot.data!,
                    fit: BoxFit.cover,
                    width: double.infinity,
                    height: double.infinity,
                  );
                },
              ),
      ),
    );
  }
}

class _DemoPhoto extends StatelessWidget {
  const _DemoPhoto();

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: const BoxDecoration(
        gradient: LinearGradient(
          colors: [Color(0xFF22345D), Color(0xFF0C142A)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
      ),
      child: Stack(
        children: [
          Center(
            child: Container(
              width: 152,
              height: 198,
              decoration: BoxDecoration(
                color: const Color(0xFF111A33),
                borderRadius: BorderRadius.circular(24),
                border: Border.all(color: SnapFixColors.line, width: 2),
              ),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(
                    Icons.router_rounded,
                    color: SnapFixColors.amber,
                    size: 72,
                  ),
                  const SizedBox(height: 16),
                  Container(
                    width: 64,
                    height: 4,
                    decoration: BoxDecoration(
                      color: SnapFixColors.line,
                      borderRadius: BorderRadius.circular(99),
                    ),
                  ),
                ],
              ),
            ),
          ),
          Positioned(
            left: 14,
            top: 14,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 11, vertical: 7),
              decoration: BoxDecoration(
                color: SnapFixColors.amber,
                borderRadius: BorderRadius.circular(99),
              ),
              child: const Text(
                '演示照片',
                style: TextStyle(
                  color: Color(0xFF1A1206),
                  fontSize: 11,
                  fontWeight: FontWeight.w800,
                ),
              ),
            ),
          ),
          const Positioned(
            right: 16,
            bottom: 14,
            child: Text(
              'TP-Link · 红灯',
              style: TextStyle(
                color: SnapFixColors.text,
                fontSize: 12,
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _PhotoLoading extends StatelessWidget {
  const _PhotoLoading();

  @override
  Widget build(BuildContext context) {
    return const ColoredBox(
      color: SnapFixColors.card,
      child: Center(child: CircularProgressIndicator()),
    );
  }
}

class _PhotoError extends StatelessWidget {
  const _PhotoError();

  @override
  Widget build(BuildContext context) {
    return const ColoredBox(
      color: SnapFixColors.card,
      child: Center(
        child: Text(
          '无法读取这张照片，请重新选择。',
          style: TextStyle(color: SnapFixColors.sub),
        ),
      ),
    );
  }
}

class _QualityChecks extends StatelessWidget {
  const _QualityChecks();

  @override
  Widget build(BuildContext context) {
    return const SnapFixCard(
      padding: EdgeInsets.symmetric(horizontal: 18, vertical: 14),
      child: Column(
        children: [
          _QualityRow(label: '主体完整', detail: '设备位于取景框内'),
          Divider(height: 20, color: SnapFixColors.line),
          _QualityRow(label: '画面清晰', detail: '型号与错误码可辨认'),
          Divider(height: 20, color: SnapFixColors.line),
          _QualityRow(label: '光线充足', detail: '无明显过暗或反光'),
        ],
      ),
    );
  }
}

class _QualityRow extends StatelessWidget {
  const _QualityRow({required this.label, required this.detail});

  final String label;
  final String detail;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        const Icon(
          Icons.check_circle_rounded,
          color: SnapFixColors.green,
          size: 20,
        ),
        const SizedBox(width: 10),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                label,
                style: const TextStyle(
                  color: SnapFixColors.text,
                  fontSize: 14,
                  fontWeight: FontWeight.w700,
                ),
              ),
              const SizedBox(height: 2),
              Text(
                detail,
                style: const TextStyle(color: SnapFixColors.sub, fontSize: 11),
              ),
            ],
          ),
        ),
        const Text(
          '通过',
          style: TextStyle(
            color: SnapFixColors.green,
            fontSize: 12,
            fontWeight: FontWeight.w700,
          ),
        ),
      ],
    );
  }
}

class _PrivacyNote extends StatelessWidget {
  const _PrivacyNote();

  @override
  Widget build(BuildContext context) {
    return const Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Icon(Icons.lock_outline_rounded, size: 16, color: SnapFixColors.sub),
        SizedBox(width: 7),
        Expanded(
          child: Text(
            '照片仅用于本次诊断，后端处理后不保留原图。',
            style: TextStyle(
              color: SnapFixColors.sub,
              fontSize: 11,
              height: 1.5,
            ),
          ),
        ),
      ],
    );
  }
}
