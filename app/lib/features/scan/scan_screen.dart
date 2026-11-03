import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';

import '../../theme/snapfix_theme.dart';
import '../../widgets/snapfix_button.dart';
import '../../widgets/snapfix_card.dart';
import 'scan_preview_screen.dart';

class ScanScreen extends StatefulWidget {
  const ScanScreen({super.key});

  @override
  State<ScanScreen> createState() => _ScanScreenState();
}

class _ScanScreenState extends State<ScanScreen> {
  final ImagePicker _picker = ImagePicker();
  bool _busy = false;

  Future<void> _pick(ImageSource source) async {
    if (_busy) return;
    setState(() => _busy = true);
    try {
      final image = await _picker.pickImage(
        source: source,
        maxWidth: 2048,
        imageQuality: 88,
      );
      if (image == null || !mounted) return;
      await Navigator.of(context).push(
        MaterialPageRoute<void>(
          builder: (_) => ScanPreviewScreen(image: image),
        ),
      );
    } catch (error) {
      if (!mounted) return;
      ScaffoldMessenger.of(context)
        ..hideCurrentSnackBar()
        ..showSnackBar(
          SnackBar(
            content: Text(
              '无法打开${source == ImageSource.camera ? '相机' : '相册'}，请检查权限后重试。',
            ),
          ),
        );
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  void _openDemo() {
    Navigator.of(
      context,
    ).push(MaterialPageRoute<void>(builder: (_) => const ScanPreviewScreen()));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('扫描设备')),
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
                  const Text(
                    '对准设备或错误码',
                    style: TextStyle(
                      color: SnapFixColors.amber2,
                      fontSize: 12,
                      fontWeight: FontWeight.w800,
                      letterSpacing: 1,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    '保持画面清晰，尽量让型号、标签和指示灯同时入镜。',
                    style: Theme.of(context).textTheme.bodyMedium,
                  ),
                  const SizedBox(height: 20),
                  const _Viewfinder(),
                  const SizedBox(height: 18),
                  Row(
                    children: [
                      Expanded(
                        child: SnapFixButton(
                          label: '拍照',
                          icon: Icons.camera_alt_rounded,
                          busy: _busy,
                          onPressed: () => _pick(ImageSource.camera),
                        ),
                      ),
                      const SizedBox(width: 10),
                      Expanded(
                        child: SnapFixButton(
                          label: '相册',
                          icon: Icons.photo_library_outlined,
                          tone: SnapFixButtonTone.secondary,
                          onPressed: _busy
                              ? null
                              : () => _pick(ImageSource.gallery),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 10),
                  SnapFixButton(
                    key: const Key('demo-preview-button'),
                    label: '使用演示照片',
                    icon: Icons.play_circle_outline_rounded,
                    tone: SnapFixButtonTone.ghost,
                    onPressed: _busy ? null : _openDemo,
                  ),
                  const SizedBox(height: 18),
                  const _CaptureTips(),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _Viewfinder extends StatelessWidget {
  const _Viewfinder();

  @override
  Widget build(BuildContext context) {
    return AspectRatio(
      aspectRatio: 0.88,
      child: Container(
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(26),
          gradient: const RadialGradient(
            center: Alignment(0, -0.15),
            radius: 1.15,
            colors: [Color(0xFF1B2C54), Color(0xFF0C142A)],
          ),
          border: Border.all(color: SnapFixColors.line),
        ),
        child: Stack(
          children: [
            const Positioned.fill(
              child: Padding(
                padding: EdgeInsets.all(18),
                child: CustomPaint(painter: _CornerFramePainter()),
              ),
            ),
            Center(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Container(
                    width: 92,
                    height: 92,
                    decoration: BoxDecoration(
                      color: SnapFixColors.card.withValues(alpha: 0.76),
                      borderRadius: BorderRadius.circular(28),
                      border: Border.all(color: SnapFixColors.line),
                    ),
                    child: const Icon(
                      Icons.router_outlined,
                      size: 48,
                      color: SnapFixColors.amber,
                    ),
                  ),
                  const SizedBox(height: 18),
                  const Text(
                    '将设备置于框内',
                    style: TextStyle(
                      color: SnapFixColors.text,
                      fontSize: 16,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                  const SizedBox(height: 6),
                  const Text(
                    '支持型号标签与屏幕错误码',
                    style: TextStyle(color: SnapFixColors.sub, fontSize: 12),
                  ),
                ],
              ),
            ),
            Align(
              alignment: const Alignment(0, -0.38),
              child: Container(
                height: 2,
                margin: const EdgeInsets.symmetric(horizontal: 58),
                decoration: BoxDecoration(
                  color: SnapFixColors.amber.withValues(alpha: 0.8),
                  boxShadow: [
                    BoxShadow(
                      color: SnapFixColors.amber.withValues(alpha: 0.34),
                      blurRadius: 12,
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _CornerFramePainter extends CustomPainter {
  const _CornerFramePainter();

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = SnapFixColors.amber
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2.4
      ..strokeCap = StrokeCap.round;
    const length = 36.0;

    final paths = [
      Path()
        ..moveTo(0, length)
        ..lineTo(0, 0)
        ..lineTo(length, 0),
      Path()
        ..moveTo(size.width - length, 0)
        ..lineTo(size.width, 0)
        ..lineTo(size.width, length),
      Path()
        ..moveTo(0, size.height - length)
        ..lineTo(0, size.height)
        ..lineTo(length, size.height),
      Path()
        ..moveTo(size.width - length, size.height)
        ..lineTo(size.width, size.height)
        ..lineTo(size.width, size.height - length),
    ];

    for (final path in paths) {
      canvas.drawPath(path, paint);
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

class _CaptureTips extends StatelessWidget {
  const _CaptureTips();

  @override
  Widget build(BuildContext context) {
    return const SnapFixCard(
      padding: EdgeInsets.all(16),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(Icons.lightbulb_outline_rounded, color: SnapFixColors.amber),
          SizedBox(width: 11),
          Expanded(
            child: Text(
              '拍摄小贴士：打开室内灯光，避免反光；如果设备有显示屏，请让错误码保持清晰。',
              style: TextStyle(
                color: SnapFixColors.sub,
                fontSize: 12,
                height: 1.5,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
