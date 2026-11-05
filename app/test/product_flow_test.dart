import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:snapfix/product/api.dart';
import 'package:snapfix/product/product_app.dart';

Json fixture() {
  final data =
      jsonDecode(File('../server/data/ui_demo.json').readAsStringSync()) as Map;
  final s = Json.from((data['sessions'] as List).first as Map);
  s['mode'] = 'demo';
  return s;
}

ProductApi fakeApi(List<Json> calls) {
  final s = fixture();
  return ProductApi(
    baseUrl: 'http://localhost',
    client: MockClient((request) async {
      final path = request.url.path;
      final body = request.body.isEmpty
          ? <String, dynamic>{}
          : Json.from(jsonDecode(request.body) as Map);
      calls.add({'method': request.method, 'path': path, 'body': body});
      Object result = s;
      if (path.endsWith('/demo')) {
        result = s;
      } else if (path.endsWith('/diagnose')) {
        result = {
          ...s,
          'mode': 'live',
          'model': null,
          'revisions': [
            {
              ...revision(s),
              'explanation': '还在学习该维修技能中！',
              'steps': <dynamic>[],
            },
          ],
        };
      } else if (path.contains('/feedback')) {
        final step = path.split('/')[6];
        for (final row in revisionSteps(s)) {
          if (row['id'] == step) {
            row['feedback'] = body['feedback'];
          }
        }
        result = s;
      } else if (path.contains('/reports/')) {
        result = {
          'content': path.endsWith('/en')
              ? 'Repair request: no appointment agreed.'
              : '师傅您好，请安排检查。',
        };
      } else if (path.endsWith('/sessions')) {
        result = [s];
      }
      return http.Response(
        jsonEncode(result),
        200,
        headers: {'content-type': 'application/json; charset=utf-8'},
      );
    }),
  );
}

Future<void> open(WidgetTester tester, ProductApi api) async {
  tester.view.physicalSize = const Size(390, 844);
  tester.view.devicePixelRatio = 1;
  addTearDown(tester.view.resetPhysicalSize);
  addTearDown(tester.view.resetDevicePixelRatio);
  addTearDown(api.close);
  await tester.pumpWidget(SnapFixProductApp(api: api));
  await tester.pump(const Duration(milliseconds: 1200));
  await tester.pumpAndSettle();
}

Future<void> tap(WidgetTester tester, String text) async {
  final target = find.text(text).last;
  await tester.ensureVisible(target);
  await tester.tap(target);
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('正式入口不自动演示；未知技能显示确认文案且无自行操作按钮', (tester) async {
    final calls = <Json>[];
    await open(tester, fakeApi(calls));
    expect(find.text('预览使用流程'), findsOneWidget);
    expect(calls, isEmpty);
    await tap(tester, '输入错误代码排查');
    await tester.enterText(find.byKey(const Key('error-code')), 'ZZ999');
    await tap(tester, '立即分析');
    expect(find.text('还在学习该维修技能中！'), findsOneWidget);
    expect(find.textContaining('开始自行排查'), findsNothing);
    expect(calls.single['path'], '/api/fe2/diagnose');
    expect(tester.takeException(), isNull);
  });
  testWidgets('预览单入口→步骤反馈→报修编辑跨语言保留→真实复制调用', (tester) async {
    final calls = <Json>[];
    String? copied;
    tester.binding.defaultBinaryMessenger.setMockMethodCallHandler(
      SystemChannels.platform,
      (call) async {
        if (call.method == 'Clipboard.setData') {
          copied = (call.arguments as Map)['text'] as String;
        }
        return null;
      },
    );
    addTearDown(
      () => tester.binding.defaultBinaryMessenger.setMockMethodCallHandler(
        SystemChannels.platform,
        null,
      ),
    );
    await open(tester, fakeApi(calls));
    await tap(tester, '预览使用流程');
    await tap(tester, '洗碗机 E24');
    expect(find.textContaining('开始自行排查'), findsOneWidget);
    expect(find.text('转交报修助手 (房东 / 师傅)'), findsOneWidget);
    await tester.tap(find.textContaining('开始自行排查'));
    await tester.pumpAndSettle();
    await tap(tester, '开始逐步排查');
    await tap(tester, '已完成');
    expect(
      calls
          .where((c) => (c['path'] as String).endsWith('/feedback'))
          .single['body'],
      {'feedback': 'done'},
    );
    await tester.tap(find.byTooltip('返回'));
    await tester.pumpAndSettle();
    await tester.tap(find.byTooltip('返回'));
    await tester.pumpAndSettle();
    await tap(tester, '转交报修助手 (房东 / 师傅)');
    await tester.enterText(
      find.byKey(const Key('report-editor')),
      '请周六联系我确认时间',
    );
    await tap(tester, 'English');
    await tap(tester, '中文');
    expect(
      tester
          .widget<TextField>(find.byKey(const Key('report-editor')))
          .controller!
          .text,
      '请周六联系我确认时间',
    );
    await tap(tester, '复制全文');
    expect(copied, '请周六联系我确认时间');
    await tap(tester, '重置模板');
    expect(
      tester
          .widget<TextField>(find.byKey(const Key('report-editor')))
          .controller!
          .text,
      '师傅您好，请安排检查。',
    );
    expect(tester.takeException(), isNull);
  });
  test('安全拒答即使错误附带步骤也不展示', () {
    final s = fixture();
    (s['revisions'] as List).first['is_high_risk'] = true;
    expect(revisionSteps(s), isEmpty);
  });
  test('网络故障不回退为预设诊断', () async {
    final api = ProductApi(
      baseUrl: 'http://localhost',
      client: MockClient((_) async => throw const SocketException('offline')),
    );
    addTearDown(api.close);
    expect(
      () => api.diagnose(code: 'E24'),
      throwsA(
        isA<ProductFailure>().having(
          (e) => e.message,
          'message',
          contains('无法连接后端'),
        ),
      ),
    );
  });
}
