"""
generate_dummy_data.py
Synthetic employee dataset generator for testing PII detection & redaction workflows.
Generates customizable row counts with fields: nama/name, nik, no_hp, email, alamat, gaji, npwp.
"""

import csv
import random
import os
from faker import Faker

fake = Faker("id_ID")  # Indonesian locale for realistic national format patterns


def generate_nik() -> str:
    """Generates synthetic 16-digit Indonesian National ID (NIK)."""
    # Format: [area_code 6 digits][birthdate 6 digits][sequence 4 digits]
    area_code = str(random.randint(110000, 999999))
    dob = fake.date_of_birth(minimum_age=20, maximum_age=60)
    dd = dob.day
    mm = dob.month
    yy = dob.year % 100
    dob_str = f"{dd:02d}{mm:02d}{yy:02d}"
    seq = str(random.randint(1, 9999)).zfill(4)
    return f"{area_code}{dob_str}{seq}"


def generate_phone() -> str:
    """Generates synthetic Indonesian mobile phone number (08xx)."""
    prefixes = [
        "0812", "0813", "0814", "0815", "0816", "0817", "0818", "0819",
        "0821", "0822", "0823", "0852", "0853", "0856", "0857", "0858",
        "0877", "0878", "0895", "0896", "0897", "0898", "0899"
    ]
    prefix = random.choice(prefixes)
    suffix = "".join([str(random.randint(0, 9)) for _ in range(8)])
    return f"{prefix}{suffix}"


def generate_npwp() -> str:
    """Generates synthetic Indonesian Tax ID (NPWP) format: XX.XXX.XXX.X-XXX.XXX."""
    parts = [
        str(random.randint(10, 99)),
        str(random.randint(100, 999)),
        str(random.randint(100, 999)),
        str(random.randint(1, 9)),
        str(random.randint(100, 999)),
        str(random.randint(100, 999)),
    ]
    return f"{parts[0]}.{parts[1]}.{parts[2]}.{parts[3]}-{parts[4]}.{parts[5]}"


def generate_email(name: str) -> str:
    """Generates synthetic corporate or personal email from employee name."""
    domains = [
        "gmail.com", "yahoo.co.id", "outlook.com", "hotmail.com",
        "company.co.id", "enterprise.com", "mail.id"
    ]
    clean_name = name.lower().replace(" ", ".").replace("'", "")
    suffix = random.choice(["", str(random.randint(1, 99)), str(random.randint(100, 999))])
    domain = random.choice(domains)
    return f"{clean_name}{suffix}@{domain}"


def generate_salary() -> str:
    """Generates formatted monthly salary string."""
    base = random.choice([
        4500000, 5000000, 5500000, 6000000, 6500000, 7000000, 7500000,
        8000000, 8500000, 9000000, 10000000, 11000000, 12000000, 13000000,
        14000000, 15000000, 17000000, 20000000, 25000000, 30000000,
    ])
    return f"Rp {base:,.0f}".replace(",", ".")


def generate_dummy_data(num_rows: int = 100, output_path: str = None) -> str:
    """
    Generates synthetic employee dataset and writes to CSV.

    Args:
        num_rows: Number of records to generate (default: 100).
        output_path: Destination file path for generated CSV.

    Returns:
        Absolute path to generated CSV.
    """
    if output_path is None:
        data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
        os.makedirs(data_dir, exist_ok=True)
        output_path = os.path.join(data_dir, "dummy_input.csv")

    fieldnames = ["nama", "nik", "no_hp", "email", "alamat", "gaji", "npwp"]
    rows = []

    for _ in range(num_rows):
        nama = fake.name()
        row = {
            "nama": nama,
            "nik": generate_nik(),
            "no_hp": generate_phone(),
            "email": generate_email(nama),
            "alamat": fake.address().replace("\n", ", "),
            "gaji": generate_salary(),
            "npwp": generate_npwp(),
        }
        rows.append(row)

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Generated {num_rows} synthetic employee records -> {output_path}")
    return output_path


if __name__ == "__main__":
    generate_dummy_data()
