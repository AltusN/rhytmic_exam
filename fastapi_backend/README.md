# FastAPI Backend

## Setup

1. Create and activate your Python virtual environment.
2. Install dependencies required by FastAPI, SQLAlchemy, aiosqlite, python-jose, bcrypt, and python-dotenv.
3. Copy `.env.example` to `.env` and update values.
4. Start server (example):

```bash
uvicorn app.main:app --reload
```

## Authentication Endpoints

- `POST /users/` register user
- `POST /token` login and receive bearer token
- `POST /auth/logout` stateless logout response
- `POST /auth/reset-password-request` request password reset token
- `POST /auth/reset-password` update password using reset token

## User Endpoints

- `GET /users/me` current user profile
- `GET /users/{user_id}` self/admin profile lookup
- `PATCH /users/me` update own profile

## Exam Endpoints

- `GET /exams/theory` fetch theory questions based on user level
- `POST /exams/theory/submit` submit theory answers and receive score
- `GET /exams/practical` fetch practical question flow and current progress
- `POST /exams/practical/progress` save practical progress incrementally
- `POST /exams/practical/submit` submit practical answers and receive score
- `GET /exams/results` current user exam result summary

## Admin Endpoints

- `GET /admin/users` list users (paginated)
- `PATCH /admin/users/{user_id}` update user state/details
- `DELETE /admin/users/{user_id}` delete a user (self-delete blocked)
- `GET /admin/questions` list questions (paginated, filterable)
- `GET /admin/questions/{question_id}` fetch single question
- `POST /admin/questions` create question
- `PATCH /admin/questions/{question_id}` update question
- `DELETE /admin/questions/{question_id}` delete question
- `GET /exams/admin/results` list results summary (paginated)
- `GET /exams/admin/results/export` export results CSV

## Notes

- The backend currently defaults to SQLite with async SQLAlchemy.
- Email send is asynchronous with retry and no-op behavior if mail settings are not configured.
- OpenAPI docs are available at `/docs`.
