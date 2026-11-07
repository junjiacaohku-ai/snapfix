import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';

import 'package:snapfix/product/product_app.dart';

Future<void> tapText(WidgetTester tester, String text) async {
  final target = find.text(text).last;
  await tester.ensureVisible(target);
  await tester.tap(target);
  await tester.pumpAndSettle();
}

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('W3 产品预览 → 步骤反馈 → 报修真实后端链路', (tester) async {
    await tester.pumpWidget(const SnapFixProductApp());
    await tester.pump(const Duration(milliseconds: 1300));
    await tester.pumpAndSettle();

    await tapText(tester, '预览使用流程');
    await tapText(tester, '路由器外部检查');

    expect(find.textContaining('TP-Link'), findsWidgets);
    await tapText(tester, '开始自行排查 (3 步)');
    await tapText(tester, '开始逐步排查');

    expect(find.text('步骤 1 / 3'), findsOneWidget);
    await tapText(tester, '已完成');
    expect(find.text('步骤 2 / 3'), findsOneWidget);

    await tester.tap(find.byTooltip('返回'));
    await tester.pumpAndSettle();
    await tester.tap(find.byTooltip('返回'));
    await tester.pumpAndSettle();
    await tapText(tester, '转交报修助手 (房东 / 师傅)');

    final editor = tester.widget<TextField>(
      find.byKey(const Key('report-editor')),
    );
    expect(editor.controller!.text, contains('TP-Link'));
    await tapText(tester, '复制全文');
    expect(tester.takeException(), isNull);
  });
}
