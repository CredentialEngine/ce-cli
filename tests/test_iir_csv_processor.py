"""Bulk signing and publishing tests using local CSVs and mocked API boundaries."""

import csv
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from ce.iir import csv_processor as processor

CTID = "ce-12345678-1234-1234-1234-123456789abc"
DID = "did:web:example.org"
VM = DID + "#key"
ENV = SimpleNamespace(publisher_base="https://api.example", ssl_verify=True)


pytestmark = pytest.mark.unit


def write_rows(path, rows):
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def read_rows(path):
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


@pytest.fixture
def operations(monkeypatch):
    values = {
        "call_is_user_member": (True, ""),
        "call_get_registry_resource": (True, {"Name": "Example"}, ""),
        "call_validate_did_web": (True, {"verificationMethodIds": [VM]}, ""),
        "call_create_challenges": (
            True,
            [{"did": VM, "challenge": "example-challenge"}],
            "",
        ),
        "sign_proof_jwt": "fixture-proof",
        "verify_proof_jwt": (True, ""),
        "call_verify_jwt_signature": (True, ""),
        "call_save_challenge_token": (True, ""),
        "call_get_organization_iir_detail": (True, {"LegalName": "Example Legal"}, ""),
        "call_submit_to_iir": (True, ""),
    }
    mocks = {name: Mock(return_value=value) for name, value in values.items()}
    for name, mock in mocks.items():
        monkeypatch.setattr(processor, name, mock)
    return mocks


@pytest.mark.parametrize(
    "failure,result",
    [
        (None, None),
        ("call_is_user_member", (False, "membership denied")),
        ("call_get_registry_resource", (False, {}, "not found")),
        ("call_validate_did_web", (False, {}, "invalid DID")),
        ("call_create_challenges", (False, [], "challenge failure")),
        ("call_create_challenges", (True, [], "")),
        ("verify_proof_jwt", (False, "verification failed")),
        ("sign_proof_jwt", ValueError("bad key")),
    ],
)
def test_generate_rows(tmp_path, operations, failure, result):
    source, signed, errors = [
        tmp_path / name for name in ("input.csv", "signed.csv", "errors.csv")
    ]
    write_rows(
        source,
        [
            {
                "CTID": CTID,
                "DID": DID,
                "VerificationMethod": VM,
                "Algorithm": "Ed25519",
                "PrivateKey": "fixture",
                "ValidFrom": "01/01/2026",
                "ValidUntil": "01/01/2027",
            }
        ],
    )
    if failure:
        if isinstance(result, Exception):
            operations[failure].side_effect = result
        else:
            operations[failure].return_value = result
    counts = processor.run_generate(
        str(source), str(signed), str(errors), "fixture", ENV, "user"
    )
    if failure:
        assert counts == (0, 1)
        assert not read_rows(signed)
        assert read_rows(errors)[0]["Error"]
    else:
        assert counts == (1, 0)
        assert not read_rows(errors)
        row = read_rows(signed)[0]
        assert row["ProofJWT"] == "fixture-proof"
        assert row["ValidFrom"] == "2026-01-01T00:00:00Z"
        assert row["Challenge"] == "example-challenge"


@pytest.mark.parametrize(
    "field,value",
    [
        ("CTID", "invalid"),
        ("ValidFrom", "invalid"),
        ("DID", "invalid"),
        ("VerificationMethod", ""),
        ("PrivateKey", ""),
    ],
)
def test_invalid_input_row(tmp_path, operations, field, value):
    source, signed, errors = [
        tmp_path / name for name in ("input.csv", "signed.csv", "errors.csv")
    ]
    row = {
        "CTID": CTID,
        "DID": DID,
        "VerificationMethod": VM,
        "PrivateKey": "fixture",
        "ValidFrom": "",
    }
    row[field] = value
    write_rows(source, [row])
    assert processor.run_generate(
        str(source), str(signed), str(errors), "fixture", ENV, "user"
    ) == (0, 1)
    assert read_rows(errors)[0]["Error"]
    operations["sign_proof_jwt"].assert_not_called()


@pytest.mark.parametrize(
    "failure,result",
    [
        (None, None),
        ("call_verify_jwt_signature", (False, "invalid proof")),
        ("call_save_challenge_token", (False, "save failed")),
        ("call_get_registry_resource", (False, {}, "missing registry")),
        ("call_submit_to_iir", (False, "publish failed")),
        ("call_get_organization_iir_detail", (False, {}, "missing accounts")),
    ],
)
def test_publish_rows(tmp_path, operations, failure, result):
    signed, errors = tmp_path / "signed.csv", tmp_path / "errors.csv"
    write_rows(
        signed,
        [
            {
                "CTID": CTID,
                "DID": DID,
                "VerificationMethod": VM,
                "Challenge": "example-challenge",
                "ProofJWT": "fixture-proof",
            }
        ],
    )
    if failure:
        operations[failure].return_value = result
    processor.run_upload(str(signed), str(errors), "fixture", ENV, yes=True)
    rows = read_rows(errors)
    if failure in (None, "call_get_organization_iir_detail"):
        assert not rows
        operations["call_submit_to_iir"].assert_called_once()
        assert operations["call_submit_to_iir"].call_args.args[2] == "Example"
    else:
        assert len(rows) == 1 and rows[0]["Error"]
        if failure != "call_submit_to_iir":
            operations["call_submit_to_iir"].assert_not_called()


def test_missing_and_empty_input(tmp_path, operations):
    source, signed, errors = [
        tmp_path / name for name in ("input.csv", "signed.csv", "errors.csv")
    ]
    with pytest.raises(FileNotFoundError):
        processor.run_generate(
            str(source), str(signed), str(errors), "fixture", ENV, "user"
        )
    source.write_text("CTID\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Missing required CSV"):
        processor.run_generate(
            str(source), str(signed), str(errors), "fixture", ENV, "user"
        )
    processor.run_upload(str(signed), str(errors), "fixture", ENV, yes=True)
    signed.write_text("CTID,DID\n", encoding="utf-8")
    processor.run_upload(str(signed), str(errors), "fixture", ENV, yes=True)
    operations["call_verify_jwt_signature"].assert_not_called()
