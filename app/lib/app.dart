import 'package:flutter/material.dart';

import 'shell/app_shell.dart';
import 'theme/snapfix_theme.dart';

class SnapFixApp extends StatelessWidget {
  const SnapFixApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'SnapFix 随手修',
      debugShowCheckedModeBanner: false,
      theme: SnapFixTheme.dark,
      home: const AppShell(),
    );
  }
}
