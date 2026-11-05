import 'package:flutter/material.dart';

const ink = Color(0xff020617),
    panel = Color(0xff0f172a),
    amber = Color(0xfff59e0b),
    muted = Color(0xff94a3b8);
const line = Color(0xff253044);

ThemeData productTheme() => ThemeData(
  brightness: Brightness.dark,
  scaffoldBackgroundColor: ink,
  useMaterial3: true,
  colorScheme: const ColorScheme.dark(
    primary: amber,
    surface: panel,
    onPrimary: ink,
    secondary: amber,
    onSecondary: ink,
    secondaryContainer: panel,
    onSecondaryContainer: amber,
  ),
  textTheme: const TextTheme(
    bodyMedium: TextStyle(fontSize: 16, height: 1.5),
    bodySmall: TextStyle(fontSize: 13, color: muted, height: 1.5),
  ),
  appBarTheme: const AppBarTheme(
    backgroundColor: ink,
    scrolledUnderElevation: 0,
    centerTitle: true,
    titleTextStyle: TextStyle(fontSize: 15, fontWeight: FontWeight.w600),
  ),
  filledButtonTheme: FilledButtonThemeData(
    style: FilledButton.styleFrom(
      minimumSize: const Size(0, 46),
      shape: const StadiumBorder(),
      textStyle: const TextStyle(fontSize: 14, fontWeight: FontWeight.w700),
    ),
  ),
  outlinedButtonTheme: OutlinedButtonThemeData(
    style: OutlinedButton.styleFrom(
      minimumSize: const Size(0, 44),
      side: const BorderSide(color: line),
      foregroundColor: Colors.white70,
      shape: const StadiumBorder(),
    ),
  ),
  inputDecorationTheme: InputDecorationTheme(
    filled: true,
    fillColor: panel,
    border: OutlineInputBorder(
      borderRadius: BorderRadius.circular(22),
      borderSide: const BorderSide(color: line),
    ),
    enabledBorder: OutlineInputBorder(
      borderRadius: BorderRadius.circular(22),
      borderSide: const BorderSide(color: line),
    ),
    contentPadding: const EdgeInsets.symmetric(horizontal: 18, vertical: 14),
  ),
  bottomSheetTheme: const BottomSheetThemeData(
    backgroundColor: panel,
    showDragHandle: true,
  ),
);

class ProductCard extends StatelessWidget {
  const ProductCard({
    required this.child,
    this.padding = const EdgeInsets.all(18),
    this.borderColor = line,
    super.key,
  });
  final Widget child;
  final EdgeInsets padding;
  final Color borderColor;
  @override
  Widget build(BuildContext context) => Container(
    padding: padding,
    decoration: BoxDecoration(
      color: panel,
      borderRadius: BorderRadius.circular(22),
      border: Border.all(color: borderColor),
    ),
    child: child,
  );
}

Widget action(
  String label,
  VoidCallback? onPressed, {
  bool primary = true,
  Key? key,
}) => Padding(
  padding: const EdgeInsets.symmetric(vertical: 4),
  child: SizedBox(
    width: double.infinity,
    child: primary
        ? FilledButton(key: key, onPressed: onPressed, child: Text(label))
        : OutlinedButton(key: key, onPressed: onPressed, child: Text(label)),
  ),
);
Widget heading(String value) => Text(
  value,
  style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w700),
);
Widget gap([double value = 16]) => SizedBox(height: value);
