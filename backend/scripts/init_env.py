"""Create a local .env with random secrets without printing credentials."""

from pathlib import Path
import secrets


def main():
    destination = Path(".env")
    if destination.exists():
        print(".env already exists; preserving it.")
        return
    password = secrets.token_hex(24)
    text = Path(".env.example").read_text(encoding="utf-8")
    text = text.replace(
        "JWT_SECRET_KEY=CHANGE_ME_USE_A_RANDOM_SECRET_OF_AT_LEAST_32_CHARACTERS",
        "JWT_SECRET_KEY=" + secrets.token_urlsafe(48),
    )
    text = text.replace(
        "postgresql+psycopg://livestock:CHANGE_ME@", "postgresql+psycopg://livestock:" + password + "@"
    ).replace("POSTGRES_PASSWORD=CHANGE_ME", "POSTGRES_PASSWORD=" + password)
    destination.write_text(text, encoding="utf-8")
    print("Created .env with random local secrets. No credentials were printed.")


if __name__ == "__main__":
    main()
