import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:liferainbow/app.dart';

void main() {
  testWidgets('App loads without error', (WidgetTester tester) async {
    // Build our app and trigger a frame.
    await tester.pumpWidget(
      const ProviderScope(
        child: LifeRainbowApp(),
      ),
    );

    // Verify that the app loads (shows loading indicator initially)
    expect(find.byType(CircularProgressIndicator), findsOneWidget);
  });
}
