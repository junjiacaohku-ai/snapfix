import 'package:flutter/material.dart';

import '../theme/snapfix_theme.dart';

enum SnapFixButtonTone { primary, secondary, ghost }

class SnapFixButton extends StatelessWidget {
  const SnapFixButton({
    required this.label,
    required this.onPressed,
    this.icon,
    this.tone = SnapFixButtonTone.primary,
    this.fullWidth = true,
    this.busy = false,
    super.key,
  });

  final String label;
  final VoidCallback? onPressed;
  final IconData? icon;
  final SnapFixButtonTone tone;
  final bool fullWidth;
  final bool busy;

  @override
  Widget build(BuildContext context) {
    final content = Row(
      mainAxisSize: MainAxisSize.min,
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        if (busy) ...[
          const SizedBox(
            width: 18,
            height: 18,
            child: CircularProgressIndicator(strokeWidth: 2),
          ),
          const SizedBox(width: 10),
        ] else if (icon != null) ...[
          Icon(icon, size: 20),
          const SizedBox(width: 9),
        ],
        Text(label),
      ],
    );

    final button = switch (tone) {
      SnapFixButtonTone.primary => FilledButton(
        onPressed: busy ? null : onPressed,
        child: content,
      ),
      SnapFixButtonTone.secondary => OutlinedButton(
        onPressed: busy ? null : onPressed,
        child: content,
      ),
      SnapFixButtonTone.ghost => TextButton(
        onPressed: busy ? null : onPressed,
        style: TextButton.styleFrom(foregroundColor: SnapFixColors.amber2),
        child: content,
      ),
    };

    return SizedBox(
      width: fullWidth ? double.infinity : null,
      height: tone == SnapFixButtonTone.ghost ? 44 : 56,
      child: button,
    );
  }
}
