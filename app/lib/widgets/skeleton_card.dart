import 'package:flutter/material.dart';

import '../theme/snapfix_theme.dart';

class SkeletonBlock extends StatelessWidget {
  const SkeletonBlock({
    required this.width,
    required this.height,
    this.radius = 8,
    super.key,
  });

  final double width;
  final double height;
  final double radius;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: width,
      height: height,
      decoration: BoxDecoration(
        color: SnapFixColors.line.withValues(alpha: 0.72),
        borderRadius: BorderRadius.circular(radius),
      ),
    );
  }
}

class SkeletonCard extends StatelessWidget {
  const SkeletonCard({this.height = 132, super.key});

  final double height;

  @override
  Widget build(BuildContext context) {
    return Semantics(
      label: '内容加载中',
      child: Container(
        height: height,
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          color: SnapFixColors.card,
          border: Border.all(color: SnapFixColors.line),
          borderRadius: BorderRadius.circular(SnapFixRadii.large),
        ),
        child: const Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            SkeletonBlock(width: 96, height: 12),
            SizedBox(height: 16),
            SkeletonBlock(width: double.infinity, height: 18),
            SizedBox(height: 10),
            SkeletonBlock(width: 210, height: 12),
          ],
        ),
      ),
    );
  }
}
