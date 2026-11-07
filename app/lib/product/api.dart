import 'dart:async';
import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;

typedef Json = Map<String, dynamic>;

/// Shared FE-2 contract; no implicit demo fallback and no API keys in the app.
class ProductApi {
  ProductApi({String? baseUrl, http.Client? client})
    : baseUrl =
          baseUrl ??
          const String.fromEnvironment('SNAPFIX_API', defaultValue: ''),
      client = client ?? http.Client();
  final String baseUrl;
  final http.Client client;
  bool demo = false;
  String get origin => baseUrl.isNotEmpty
      ? baseUrl
      : kIsWeb
      ? Uri.base.origin
      : defaultTargetPlatform == TargetPlatform.android
      ? 'http://10.0.2.2:8000'
      : 'http://127.0.0.1:8000';
  Uri uri(String path) => Uri.parse('$origin/api/fe2$path');
  Uri v1Uri(String path) => Uri.parse('$origin/api$path');
  Future<dynamic> decode(Future<http.Response> work) async {
    try {
      final response = await work.timeout(const Duration(seconds: 35));
      final body = jsonDecode(utf8.decode(response.bodyBytes));
      if (response.statusCode >= 400) {
        throw ProductFailure(
          body is Map && body['detail'] is String
              ? body['detail'] as String
              : '请求未成功，请检查输入后重试。',
        );
      }
      return body;
    } on ProductFailure {
      rethrow;
    } on TimeoutException {
      throw const ProductFailure('连接超时，请稍后重试。');
    } catch (_) {
      throw const ProductFailure('无法连接后端，请检查服务和网络后重试。');
    }
  }

  Future<dynamic> send(
    String method,
    Uri url, [
    Json? body,
  ]) {
    final request = http.Request(method, url);
    request.headers['Content-Type'] = 'application/json';
    if (body != null) request.body = jsonEncode(body);
    return decode(client.send(request).then(http.Response.fromStream));
  }

  Future<dynamic> request(String method, String path, [Json? body]) =>
      send(method, uri(path), body);
  Future<dynamic> requestV1(String method, String path, [Json? body]) =>
      send(method, v1Uri(path), body);
  Future<bool> realVisionAvailable() async {
    final capabilities = Json.from(
      await request('GET', '/capabilities') as Map,
    );
    return capabilities['real_vision_connected'] == true;
  }

  Future<List<Json>> list({String? mode}) async => (await request(
    'GET',
    '/sessions?mode=${mode ?? (demo ? 'demo' : 'live')}',
  ) as List).map((e) => Json.from(e as Map)).toList();
  Future<List<Json>> cases({
    String q = '',
    String brand = '',
    String appliance = '',
  }) async => (await request(
    'GET',
    '/cases?${Uri(queryParameters: {'q': q, 'brand': brand, 'appliance': appliance}).query}',
  ) as List).map((e) => Json.from(e as Map)).toList();
  Future<Json> get(String id) async => Json.from(
    await request('GET', '/sessions/${Uri.encodeComponent(id)}') as Map,
  );
  Future<Json> importV1(String id) async => Json.from(
    await request('POST', '/import/${Uri.encodeComponent(id)}') as Map,
  );
  Future<Json> scenario(String value) async =>
      Json.from(await request('POST', '/demo', {'scenario': value}) as Map);
  Future<Json> diagnose({
    String brand = '',
    String category = '',
    String code = '',
    String note = '',
  }) async {
    if (note.trim().isEmpty &&
        code.trim().isNotEmpty &&
        await realVisionAvailable()) {
      final legacy = Json.from(
        await requestV1('POST', '/diagnose/manual', {
          'brand': brand,
          'error_code': code,
        }) as Map,
      );
      return importV1(legacy['id'] as String);
    }
    return Json.from(
      await request('POST', '/diagnose', {
        'brand': brand,
        'category': category,
        'error_code': code,
        'note': note,
      }) as Map,
    );
  }

  Future<Json> photo(Uint8List bytes, String name) async {
    if (bytes.length > 5 * 1024 * 1024) {
      throw const ProductFailure('请选择不超过 5MB 的照片。');
    }
    final realVision = await realVisionAvailable();
    final req = http.MultipartRequest(
      'POST',
      realVision ? v1Uri('/analyze/image') : uri('/diagnose/photo'),
    )..files.add(http.MultipartFile.fromBytes('file', bytes, filename: name));
    final result = Json.from(
      await decode(client.send(req).then(http.Response.fromStream)) as Map,
    );
    if (realVision && result['source_mode'] == 'mock') {
      throw const ProductFailure('真实识别暂不可用，请稍后重试或使用明确的流程预览。');
    }
    return realVision ? importV1(result['id'] as String) : result;
  }

  Future<Json> feedback(String id, String step, String value) async =>
      Json.from(
        await request('POST', '/sessions/$id/steps/$step/feedback', {
          'feedback': value,
        }) as Map,
      );
  Future<Json> status(String id, String value) async => Json.from(
    await request('PATCH', '/sessions/$id/status', {'status': value}) as Map,
  );
  Future<void> delete(String id) async {
    await request('DELETE', '/sessions/$id');
  }

  Future<Json> followUp(String id, String note, String? photoRef) async =>
      Json.from(
        await request('POST', '/sessions/$id/follow-ups', {
          'note': note,
          'photo_ref': photoRef,
        }) as Map,
      );
  Future<Json> report(String id, String who, String lang) async => Json.from(
    await request('POST', '/sessions/$id/reports/$who/$lang') as Map,
  );
  Future<Json> template(String id, String who, String lang) async => Json.from(
    await request('GET', '/sessions/$id/reports/$who/$lang/template') as Map,
  );
  Future<Json> save(String id, String who, String lang, String text) async =>
      Json.from(
        await request('PUT', '/sessions/$id/reports/$who/$lang', {
          'content': text,
        }) as Map,
      );
  Future<Json> check(String id, String code) async => Json.from(
    await request('POST', '/cases/$id/checks', {'errorCode': code}) as Map,
  );
  void close() => client.close();
}

class ProductFailure implements Exception {
  const ProductFailure(this.message);
  final String message;
  @override
  String toString() => message;
}

Json revision(Json session) => Json.from(
  (session['revisions'] as List)[session['current_revision_index'] as int]
      as Map,
);
List<Json> revisionSteps(Json session) =>
    (revision(session)['is_high_risk'] == true
            ? <dynamic>[]
            : revision(session)['steps'] as List)
        .map((e) => Json.from(e as Map))
        .toList();
