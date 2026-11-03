import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:snapfix/app.dart';

void main() {
  testWidgets('W1 首页 → 扫描 → 预览链路可走通', (tester) async {
    tester.view.physicalSize = const Size(390, 844);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(const SnapFixApp());
    await tester.pumpAndSettle();

    expect(find.textContaining('SnapFix'), findsOneWidget);
    expect(find.text('拍照诊断'), findsOneWidget);

    await tester.ensureVisible(find.text('拍照诊断'));
    await tester.tap(find.text('拍照诊断'));
    await tester.pumpAndSettle();

    expect(find.text('扫描设备'), findsOneWidget);
    expect(find.text('拍照'), findsOneWidget);
    expect(find.text('相册'), findsOneWidget);

    final demoButton = find.byKey(const Key('demo-preview-button'));
    await tester.ensureVisible(demoButton);
    await tester.tap(demoButton);
    await tester.pumpAndSettle();

    expect(find.text('确认照片'), findsOneWidget);
    expect(find.text('检查照片质量'), findsOneWidget);
    expect(find.text('开始诊断'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('首页保留错误码与档案入口', (tester) async {
    tester.view.physicalSize = const Size(390, 844);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(const SnapFixApp());
    await tester.pumpAndSettle();

    expect(find.text('错误码速查'), findsOneWidget);
    expect(find.text('维修档案'), findsOneWidget);

    await tester.ensureVisible(find.text('错误码速查'));
    await tester.tap(find.text('错误码速查'));
    await tester.pumpAndSettle();

    expect(find.text('手动输入也能诊断'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}
