import 'package:flutter/material.dart';

import '../../theme/snapfix_theme.dart';
import '../../widgets/snapfix_button.dart';
import '../../widgets/snapfix_card.dart';
import '../placeholder/feature_placeholder_screen.dart';
import '../scan/scan_screen.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({required this.onOpenArchive, super.key});

  final VoidCallback onOpenArchive;

  void _openScan(BuildContext context) {
    Navigator.of(context)
        .push(MaterialPageRoute<void>(builder: (_) => const ScanScreen()));
  }

  void _openErrorCode(BuildContext context) {
    Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (_) => const FeaturePlaceholderScreen(
          eyebrow: 'F1b · 错误码速查',
          title: '手动输入也能诊断',
          message: '品牌与错误码输入页将在 W2 接入检索管线。当前 W1 先冻结入口与视觉骨架。',
          icon: Icons.keyboard_alt_outlined,
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      bottom: false,
      child: SingleChildScrollView(
        padding: const EdgeInsets.fromLTRB(20, 18, 20, 28),
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 680),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const _HomeHeader(),
                const SizedBox(height: 24),
                _ScanHero(onScan: () => _openScan(context)),
                const SizedBox(height: 14),
                Row(
                  children: [
                    Expanded(
                      child: SnapFixButton(
                        label: '错误码速查',
                        icon: Icons.keyboard_alt_outlined,
                        tone: SnapFixButtonTone.secondary,
                        onPressed: () => _openErrorCode(context),
                      ),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: SnapFixButton(
                        label: '维修档案',
                        icon: Icons.history_rounded,
                        tone: SnapFixButtonTone.secondary,
                        onPressed: onOpenArchive,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 24),
                Text('从判断到行动', style: Theme.of(context).textTheme.titleLarge),
                const SizedBox(height: 12),
                const _CapabilityGrid(),
                const SizedBox(height: 18),
                const _SafetyNote(),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _HomeHeader extends StatelessWidget {
  const _HomeHeader();

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.center,
      children: [
        Container(
          width: 44,
          height: 44,
          decoration: BoxDecoration(
            color: SnapFixColors.amber,
            borderRadius: BorderRadius.circular(13),
            boxShadow: [
              BoxShadow(
                color: SnapFixColors.amber.withValues(alpha: 0.22),
                blurRadius: 22,
              ),
            ],
          ),
          child: const Icon(
            Icons.home_repair_service_rounded,
            color: Color(0xFF1A1206),
            size: 25,
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'SnapFix 随手修',
                style: Theme.of(context).textTheme.titleLarge,
              ),
              const SizedBox(height: 2),
              const Text(
                '先搞懂，再决定。',
                style: TextStyle(color: SnapFixColors.sub, fontSize: 13),
              ),
            ],
          ),
        ),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 7),
          decoration: BoxDecoration(
            color: SnapFixColors.green.withValues(alpha: 0.1),
            borderRadius: BorderRadius.circular(SnapFixRadii.pill),
            border: Border.all(
              color: SnapFixColors.green.withValues(alpha: 0.35),
            ),
          ),
          child: const Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(Icons.bolt_rounded, size: 14, color: SnapFixColors.green),
              SizedBox(width: 3),
              Text(
                'MOCK READY',
                style: TextStyle(
                  color: SnapFixColors.green,
                  fontSize: 10,
                  fontWeight: FontWeight.w800,
                  letterSpacing: 0.4,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _ScanHero extends StatelessWidget {
  const _ScanHero({required this.onScan});

  final VoidCallback onScan;

  @override
  Widget build(BuildContext context) {
    return SnapFixCard(
      padding: const EdgeInsets.all(20),
      gradient: const LinearGradient(
        colors: [Color(0xFF1A264A), Color(0xFF121A34)],
        begin: Alignment.topLeft,
        end: Alignment.bottomRight,
      ),
      borderColor: SnapFixColors.amber.withValues(alpha: 0.28),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            '拍一张，先搞懂\n哪里坏了',
            style: Theme.of(context).textTheme.displaySmall,
          ),
          const SizedBox(height: 10),
          const Text(
            '识别设备与可见故障，给出可执行的三档决策。',
            style: TextStyle(color: SnapFixColors.sub, fontSize: 15),
          ),
          const SizedBox(height: 20),
          const _ScanFrame(),
          const SizedBox(height: 18),
          SnapFixButton(
            label: '拍照诊断',
            icon: Icons.camera_alt_rounded,
            onPressed: onScan,
          ),
        ],
      ),
    );
  }
}

class _ScanFrame extends StatelessWidget {
  const _ScanFrame();

  @override
  Widget build(BuildContext context) {
    return AspectRatio(
      aspectRatio: 1.7,
      child: Container(
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(18),
          gradient: const RadialGradient(
            center: Alignment(0, -0.2),
            radius: 1.2,
            colors: [Color(0xFF20325E), Color(0xFF0D152B)],
          ),
          border: Border.all(color: SnapFixColors.line),
        ),
        child: Stack(
          children: [
            const Positioned.fill(
              child: CustomPaint(painter: _ScanCornerPainter()),
            ),
            Center(
              child: Container(
                width: 68,
                height: 68,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: SnapFixColors.amber.withValues(alpha: 0.12),
                ),
                child: const Icon(
                  Icons.view_in_ar_rounded,
                  color: SnapFixColors.amber,
                  size: 34,
                ),
              ),
            ),
            Align(
              alignment: const Alignment(0, -0.02),
              child: Container(
                height: 2,
                margin: const EdgeInsets.symmetric(horizontal: 42),
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    colors: [
                      Colors.transparent,
                      SnapFixColors.amber.withValues(alpha: 0.85),
                      Colors.transparent,
                    ],
                  ),
                  boxShadow: [
                    BoxShadow(
                      color: SnapFixColors.amber.withValues(alpha: 0.28),
                      blurRadius: 10,
                    ),
                  ],
                ),
              ),
            ),
            const Positioned(
              left: 16,
              bottom: 12,
              child: Text(
                '对准设备 · 包含错误码',
                style: TextStyle(color: SnapFixColors.sub, fontSize: 11),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _ScanCornerPainter extends CustomPainter {
  const _ScanCornerPainter();

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = SnapFixColors.amber
      ..strokeWidth = 2
      ..strokeCap = StrokeCap.round
      ..style = PaintingStyle.stroke;

    const inset = 20.0;
    const length = 28.0;
    final paths = [
      Path()
        ..moveTo(inset, inset + length)
        ..lineTo(inset, inset)
        ..lineTo(inset + length, inset),
      Path()
        ..moveTo(size.width - inset - length, inset)
        ..lineTo(size.width - inset, inset)
        ..lineTo(size.width - inset, inset + length),
      Path()
        ..moveTo(inset, size.height - inset - length)
        ..lineTo(inset, size.height - inset)
        ..lineTo(inset + length, size.height - inset),
      Path()
        ..moveTo(size.width - inset - length, size.height - inset)
        ..lineTo(size.width - inset, size.height - inset)
        ..lineTo(size.width - inset, size.height - inset - length),
    ];

    for (final path in paths) {
      canvas.drawPath(path, paint);
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

class _CapabilityGrid extends StatelessWidget {
  const _CapabilityGrid();

  @override
  Widget build(BuildContext context) {
    return const Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Expanded(
          child: _CapabilityCard(
            icon: Icons.center_focus_strong_rounded,
            title: '看懂',
            body: '设备与故障',
          ),
        ),
        SizedBox(width: 10),
        Expanded(
          child: _CapabilityCard(
            icon: Icons.alt_route_rounded,
            title: '判断',
            body: '修 / 房东 / 师傅',
          ),
        ),
        SizedBox(width: 10),
        Expanded(
          child: _CapabilityCard(
            icon: Icons.description_outlined,
            title: '闭环',
            body: '中英报修信',
          ),
        ),
      ],
    );
  }
}

class _CapabilityCard extends StatelessWidget {
  const _CapabilityCard({
    required this.icon,
    required this.title,
    required this.body,
  });

  final IconData icon;
  final String title;
  final String body;

  @override
  Widget build(BuildContext context) {
    return SnapFixCard(
      padding: const EdgeInsets.symmetric(horizontal: 13, vertical: 15),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, color: SnapFixColors.amber, size: 22),
          const SizedBox(height: 12),
          Text(
            title,
            style: const TextStyle(
              color: SnapFixColors.text,
              fontSize: 15,
              fontWeight: FontWeight.w700,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            body,
            style: const TextStyle(
              color: SnapFixColors.sub,
              fontSize: 11,
              height: 1.4,
            ),
          ),
        ],
      ),
    );
  }
}

class _SafetyNote extends StatelessWidget {
  const _SafetyNote();

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: SnapFixColors.red.withValues(alpha: 0.07),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: SnapFixColors.red.withValues(alpha: 0.22)),
      ),
      child: const Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(Icons.shield_outlined, size: 18, color: SnapFixColors.red),
          SizedBox(width: 9),
          Expanded(
            child: Text(
              '高压电、燃气等高风险问题将直接拒答，并建议联系专业人士。',
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
