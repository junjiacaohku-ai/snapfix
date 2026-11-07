import 'package:flutter/material.dart';

import '../../theme/snapfix_theme.dart';
import '../../widgets/snapfix_card.dart';

class ArchivePlaceholderScreen extends StatelessWidget {
  const ArchivePlaceholderScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      bottom: false,
      child: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 520),
            child: SnapFixCard(
              padding: const EdgeInsets.all(26),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Container(
                    width: 64,
                    height: 64,
                    decoration: BoxDecoration(
                      color: SnapFixColors.amber.withValues(alpha: 0.12),
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: const Icon(
                      Icons.history_rounded,
                      color: SnapFixColors.amber,
                      size: 32,
                    ),
                  ),
                  const SizedBox(height: 18),
                  Text(
                    '维修档案',
                    style: Theme.of(context).textTheme.headlineMedium,
                  ),
                  const SizedBox(height: 8),
                  const Text(
                    'FE-2 将在后续接入历史记录、详情只读与删除能力。W1 仅保留入口，避免与并行分支冲突。',
                    textAlign: TextAlign.center,
                    style: TextStyle(color: SnapFixColors.sub, height: 1.55),
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
