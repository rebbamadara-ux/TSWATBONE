# REBBA Auth API — starter

This is the first backend component for REBBA: account registration, login, player IDs and a basic profile endpoint.

## Deploy on Railway

1. Add these files to the root of the GitHub repository connected to Railway.
2. In Railway, add a PostgreSQL database to the project.
3. In the backend service, add variable `DATABASE_URL` by referencing the PostgreSQL service's `DATABASE_URL`.
4. Add variable `SECRET_KEY` with a long random secret (at least 32 random characters). Keep it private.
5. Redeploy.

## Test

`GET /health`

Register with JSON:
```json
{
  "username": "rebba_player",
  "email": "player@example.com",
  "password": "a-long-password-123"
}
```

`POST /api/auth/register`

Login with JSON:
```json
{
  "identity": "rebba_player",
  "password": "a-long-password-123"
}
```

`POST /api/auth/login`

Use the returned token:
`GET /api/player/me`
Header: `Authorization: Bearer YOUR_TOKEN`

## Important limitations

This is an account/authentication prototype, not a Free Fire 2020-compatible server. It does not implement the original game's network protocol, matchmaking, gameplay, inventory, payments, or Garena services. Those require protocol analysis and independent implementation. Do not use real passwords from existing accounts.
