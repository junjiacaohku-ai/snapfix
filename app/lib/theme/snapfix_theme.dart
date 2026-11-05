import 'package:flutter/material.dart';

abstract final class SnapFixColors {
  static const bg = Color(0xFF0B1020);
  static const bg2 = Color(0xFF111A33);
  static const card = Color(0xFF16203D);
  static const line = Color(0xFF24335C);
  static const amber = Color(0xFFF5A623);
  static const amber2 = Color(0xFFFFCF6B);
  static const text = Color(0xFFEEF2FF);
  static const sub = Color(0xFF9AA7C7);
  static const green = Color(0xFF3DDC97);
  static const red = Color(0xFFFF6B6B);
}

abstract final class SnapFixRadii {
  static const small = 10.0;
  static const medium = 16.0;
  static const large = 24.0;
  static const pill = 999.0;
}

abstract final class SnapFixTheme {
  static ThemeData get dark {
    const scheme = ColorScheme.dark(
      primary: SnapFixColors.amber,
      onPrimary: Color(0xFF1A1206),
      secondary: SnapFixColors.amber2,
      onSecondary: Color(0xFF1A1206),
      surface: SnapFixColors.card,
      onSurface: SnapFixColors.text,
      error: SnapFixColors.red,
      onError: Colors.white,
      outline: SnapFixColors.line,
    );

    final base = ThemeData(
      useMaterial3: true,
      brightness: Brightness.dark,
      colorScheme: scheme,
      scaffoldBackgroundColor: SnapFixColors.bg,
      splashFactory: InkSparkle.splashFactory,
    );

    return base.copyWith(
      textTheme: base.textTheme.copyWith(
        displaySmall: const TextStyle(
          color: SnapFixColors.text,
          fontSize: 38,
          height: 1.12,
          fontWeight: FontWeight.w800,
          letterSpacing: -1.1,
        ),
        headlineMedium: const TextStyle(
          color: SnapFixColors.text,
          fontSize: 28,
          height: 1.2,
          fontWeight: FontWeight.w800,
          letterSpacing: -0.5,
        ),
        titleLarge: const TextStyle(
          color: SnapFixColors.text,
          fontSize: 22,
          height: 1.3,
          fontWeight: FontWeight.w700,
        ),
        titleMedium: const TextStyle(
          color: SnapFixColors.text,
          fontSize: 17,
          height: 1.35,
          fontWeight: FontWeight.w700,
        ),
        bodyLarge: const TextStyle(
          color: SnapFixColors.text,
          fontSize: 16,
          height: 1.55,
        ),
        bodyMedium: const TextStyle(
          color: SnapFixColors.sub,
          fontSize: 15,
          height: 1.55,
        ),
        labelLarge: const TextStyle(
          fontSize: 16,
          fontWeight: FontWeight.w700,
          letterSpacing: 0.1,
        ),
      ),
      appBarTheme: const AppBarTheme(
        backgroundColor: Colors.transparent,
        foregroundColor: SnapFixColors.text,
        elevation: 0,
        centerTitle: false,
        titleTextStyle: TextStyle(
          color: SnapFixColors.text,
          fontSize: 20,
          fontWeight: FontWeight.w700,
        ),
      ),
      navigationBarTheme: NavigationBarThemeData(
        backgroundColor: const Color(0xFF0E162D),
        indicatorColor: SnapFixColors.amber.withValues(alpha: 0.16),
        labelTextStyle: WidgetStateProperty.resolveWith((states) {
          final selected = states.contains(WidgetState.selected);
          return TextStyle(
            color: selected ? SnapFixColors.amber2 : SnapFixColors.sub,
            fontSize: 12,
            fontWeight: selected ? FontWeight.w700 : FontWeight.w500,
          );
        }),
        iconTheme: WidgetStateProperty.resolveWith((states) {
          final selected = states.contains(WidgetState.selected);
          return IconThemeData(
            color: selected ? SnapFixColors.amber : SnapFixColors.sub,
            size: 24,
          );
        }),
      ),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          backgroundColor: SnapFixColors.amber,
          foregroundColor: const Color(0xFF1A1206),
          disabledBackgroundColor: SnapFixColors.line,
          disabledForegroundColor: SnapFixColors.sub,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(14),
          ),
          textStyle: const TextStyle(fontSize: 16, fontWeight: FontWeight.w800),
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: SnapFixColors.text,
          side: const BorderSide(color: SnapFixColors.line),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(14),
          ),
          textStyle: const TextStyle(fontSize: 15, fontWeight: FontWeight.w700),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: SnapFixColors.card,
        hintStyle: const TextStyle(color: SnapFixColors.sub),
        labelStyle: const TextStyle(color: SnapFixColors.sub),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
          borderSide: const BorderSide(color: SnapFixColors.line),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
          borderSide: const BorderSide(color: SnapFixColors.line),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
          borderSide: const BorderSide(color: SnapFixColors.amber),
        ),
      ),
      snackBarTheme: SnackBarThemeData(
        backgroundColor: SnapFixColors.card,
        contentTextStyle: const TextStyle(color: SnapFixColors.text),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        behavior: SnackBarBehavior.floating,
      ),
    );
  }
}
