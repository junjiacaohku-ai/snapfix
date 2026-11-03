import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';

import 'package:snapfix/app.dart';

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('模拟器 W1 主链路验收', (tester) async {
    await tester.pumpWidget(const SnapFixApp());
    await tester.pumpAndSettle();

    expect(find.text('拍照诊断'), findsOneWidget);

    await tester.ensureVisible(find.text('拍照诊断'));
    await tester.tap(find.text('拍照诊断'));
    await tester.pumpAndSettle();

    expect(find.text('扫描设备'), findsOneWidget);

    final demoButton = find.byKey(const Key('demo-preview-button'));
    await tester.ensureVisible(demoButton);
    await tester.tap(demoButton);
    await tester.pumpAndSettle();

    expect(find.text('确认照片'), findsOneWidget);
    expect(find.text('检查照片质量'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}
