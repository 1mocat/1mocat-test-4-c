#!/usr/bin/env python3
"""Python re-implementation of cobol/src/program.cbl (BOOKFORUM)."""
import os
import sys

ACCOUNTS_FILE = os.path.join("data", "ACCOUNTS.DAT")
BOOKS_FILE = os.path.join("data", "BOOKS.DAT")
TRANSACTIONS_FILE = os.path.join("data", "TRANSACTIONS.DAT")
INPUT_FILE = os.path.join("src", "INPUT.DAT")

ACC_REC_LEN = 4 + 20 + 10   # 34
BOOK_REC_LEN = 4 + 20 + 4   # 28
TRANS_REC_LEN = 4 + 10 + 4 + 4  # 22
INPUT_REC_LEN = 4 + 4 + 4 + 10  # 22


def _digits_or_zero(b: bytes) -> int:
    s = b.decode("latin-1")
    out = []
    for ch in s:
        out.append(ch if ch.isdigit() else "0")
    return int("".join(out)) if out else 0


def main():
    with open(INPUT_FILE, "rb") as f:
        data = f.read()
    if not data:
        print("Error: Input file is empty")
        return
    rec = data[:INPUT_REC_LEN].ljust(INPUT_REC_LEN, b" ")
    buyer_id = rec[0:4]
    seller_id = rec[4:8]
    book_id = rec[8:12]
    # WS-AMOUNT is PIC 9(10)V99 but INPUT-AMOUNT is PIC 9(10) -> integer value
    amount = _digits_or_zero(rec[12:22])

    # ---- Validation ----
    buyer_found = seller_found = book_found = valid_owner = False

    with open(ACCOUNTS_FILE, "rb") as f:
        acc_data = f.read()
    for i in range(0, len(acc_data), ACC_REC_LEN):
        r = acc_data[i:i + ACC_REC_LEN]
        if len(r) < ACC_REC_LEN:
            break
        aid = r[0:4]
        if aid == buyer_id:
            buyer_found = True
        if aid == seller_id:
            seller_found = True

    with open(BOOKS_FILE, "rb") as f:
        book_data = f.read()
    for i in range(0, len(book_data), BOOK_REC_LEN):
        r = book_data[i:i + BOOK_REC_LEN]
        if len(r) < BOOK_REC_LEN:
            break
        bid = r[0:4]
        owner = r[24:28]
        if bid == book_id:
            book_found = True
            if owner == seller_id:
                valid_owner = True

    print(" ")

    if not (buyer_found and seller_found and book_found and valid_owner):
        print("Transaction failed due to validation errors")
        return

    # ---- Process transaction ----
    # Update ACCOUNTS
    new_acc = bytearray()
    for i in range(0, len(acc_data), ACC_REC_LEN):
        r = bytearray(acc_data[i:i + ACC_REC_LEN])
        if len(r) < ACC_REC_LEN:
            new_acc.extend(r)
            continue
        aid = bytes(r[0:4])
        bal = _digits_or_zero(bytes(r[24:34]))
        if aid == buyer_id:
            bal = (bal - amount) % (10 ** 10)
            r[24:34] = f"{bal:010d}".encode("latin-1")
        if aid == seller_id:
            bal = _digits_or_zero(bytes(r[24:34]))
            bal = (bal + amount) % (10 ** 10)
            r[24:34] = f"{bal:010d}".encode("latin-1")
        new_acc.extend(r)
    with open(ACCOUNTS_FILE, "wb") as f:
        f.write(bytes(new_acc))

    # Update BOOKS
    new_books = bytearray()
    for i in range(0, len(book_data), BOOK_REC_LEN):
        r = bytearray(book_data[i:i + BOOK_REC_LEN])
        if len(r) < BOOK_REC_LEN:
            new_books.extend(r)
            continue
        bid = bytes(r[0:4])
        if bid == book_id:
            r[24:28] = buyer_id
        new_books.extend(r)
    with open(BOOKS_FILE, "wb") as f:
        f.write(bytes(new_books))

    # Append transaction
    trans_rec = (
        book_id
        + f"{amount:010d}".encode("latin-1")
        + seller_id
        + buyer_id
    )
    with open(TRANSACTIONS_FILE, "ab") as f:
        f.write(trans_rec)

    print("Transaction completed successfully")


if __name__ == "__main__":
    main()
