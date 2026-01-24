-- Test data seed script for AdtroBot
-- Purpose: Seed database with test users and basic data for E2E testing
-- Usage: psql $DATABASE_URL < tests/fixtures/seed.sql

-- Cleanup: Run before seeding to ensure clean state
-- DELETE FROM tarot_spreads WHERE user_id IN (SELECT id FROM users WHERE username LIKE 'test_%');
-- DELETE FROM payments WHERE user_id IN (SELECT id FROM users WHERE username LIKE 'test_%');
-- DELETE FROM users WHERE username LIKE 'test_%';

-- Test admin user for admin panel testing
INSERT INTO users (telegram_id, username, zodiac_sign, birth_date, is_premium, created_at)
VALUES (111111111, 'test_admin', 'capricorn', '1990-01-15', true, NOW())
ON CONFLICT (telegram_id) DO UPDATE SET
  username = EXCLUDED.username,
  is_premium = EXCLUDED.is_premium;

-- Test free user for bot testing
INSERT INTO users (telegram_id, username, zodiac_sign, birth_date, is_premium, created_at)
VALUES (222222222, 'test_free_user', 'leo', '1995-08-10', false, NOW())
ON CONFLICT (telegram_id) DO UPDATE SET
  username = EXCLUDED.username,
  is_premium = EXCLUDED.is_premium;

-- Test premium user for premium feature testing
INSERT INTO users (telegram_id, username, zodiac_sign, birth_date, is_premium, premium_until, daily_spread_limit, created_at)
VALUES (333333333, 'test_premium_user', 'scorpio', '1988-11-22', true, NOW() + INTERVAL '30 days', 20, NOW())
ON CONFLICT (telegram_id) DO UPDATE SET
  username = EXCLUDED.username,
  is_premium = EXCLUDED.is_premium,
  premium_until = EXCLUDED.premium_until,
  daily_spread_limit = EXCLUDED.daily_spread_limit;

-- Test user with full birth data for natal chart testing
INSERT INTO users (
  telegram_id, username, zodiac_sign, birth_date, birth_time,
  birth_city, birth_lat, birth_lon, is_premium, created_at
)
VALUES (
  444444444, 'test_natal_user', 'virgo', '1992-09-05', '14:30:00',
  'Москва', 55.7558, 37.6173, true, NOW()
)
ON CONFLICT (telegram_id) DO UPDATE SET
  username = EXCLUDED.username,
  birth_time = EXCLUDED.birth_time,
  birth_city = EXCLUDED.birth_city,
  birth_lat = EXCLUDED.birth_lat,
  birth_lon = EXCLUDED.birth_lon;

-- Sample tarot spread for history testing
INSERT INTO tarot_spreads (user_id, spread_type, question, cards, interpretation, created_at)
SELECT
  u.id,
  'three_card',
  'Что ждет меня в ближайшем будущем?',
  '[{"card_id": "ar01", "reversed": false, "position": 1}, {"card_id": "cu05", "reversed": true, "position": 2}, {"card_id": "sw10", "reversed": false, "position": 3}]'::jsonb,
  'Маг в первой позиции указывает на новые возможности и силу для их реализации...',
  NOW() - INTERVAL '1 day'
FROM users u
WHERE u.username = 'test_free_user'
ON CONFLICT DO NOTHING;

-- Note: Payments are typically created through the actual payment flow,
-- so we don't seed them here. Use PaymentFactory for test payments.

-- Verification queries (uncomment to check):
-- SELECT id, telegram_id, username, is_premium FROM users WHERE username LIKE 'test_%';
-- SELECT id, user_id, spread_type, created_at FROM tarot_spreads LIMIT 5;
