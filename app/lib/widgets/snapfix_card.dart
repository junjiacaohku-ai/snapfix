import 'package:flutter/material.dart';

import '../theme/snapfix_theme.dart';

class SnapFixCard extends StatelessWidget {
  const SnapFixCard({
    required this.child,
    this.padding = const EdgeInsets.all(20),
    this.color = SnapFixColors.card,
    this.borderColor = SnapFixColors.line,
    this.gradient,
    this.onTap,
    super.key,
  });

  final Widget child;
  final EdgeInsetsGeometry padding;
  final Color color;
  final Color borderColor;
  final Gradient? gradient;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final decoration = BoxDecoration(
      color: gradient == null ? color : null,
      gradient: gradient,
      borderRadius: BorderRadius.circular(SnapFixRadii.large),
      border: Border.all(color: borderColor),
      boxShadow: const [
        BoxShadow(
          color: Color(0x33000000),
          blurRadius: 28,
          offset: Offset(0, 12),
        ),
      ],
    );

    final content = Padding(padding: padding, child: child);

    if (onTap == null) {
      return Container(decoration: decoration, child: content);
    }

    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(SnapFixRadii.large),
        child: Ink(decoration: decoration, child: content),
      ),
    );
  }
}
