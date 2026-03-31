"""
Unit tests for the CLI command layer.
pytest tests/test_cli.py --record-mode=none -s
"""
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
from ce.main import cli

runner = CliRunner()

FAKE_TOKEN = "header.eyJzdWIiOiI1NTBlODQwMC1lMjliLTQxZDQtYTcxNi00NDY2NTU0NDAwMDAifQ.sig"


def _fake_env():
    env = MagicMock()
    env.label = "dev"
    env.publisher_base = "https://localhost:44330"
    return env


# ---------------------------------------------------------------------------
# Shared patch targets — these are what the commands ACTUALLY call
# ---------------------------------------------------------------------------
PATCH_LOGIN    = "ce.commands.iir.require_login"
PATCH_ENV      = "ce.commands.iir.require_environment"
PATCH_GENERATE = "ce.commands.iir.run_generate"
PATCH_UPLOAD   = "ce.commands.iir.run_upload"
PATCH_USER_ID  = "ce.commands.iir.extract_user_id_from_token"


class TestSignChallengesCommand:

    def test_missing_csv_flag_exits_nonzero(self):
        result = runner.invoke(cli, ["iir", "bulk-upload-dids", "sign-challenges"])
        assert result.exit_code != 0
        assert "Missing option" in result.output or "--csv" in result.output

    def test_nonexistent_csv_file_exits_nonzero(self):
        result = runner.invoke(
            cli,
            ["iir", "bulk-upload-dids", "sign-challenges", "--csv", "/no/such/file.csv"],
        )
        assert result.exit_code != 0

    def test_successful_run_exits_zero(self, tmp_path):
        csv_file = tmp_path / "input.csv"
        csv_file.write_text(
            "CTID,DID,VerificationMethod,Algorithm,PrivateKey\n"
            "ce-12345678-1234-1234-1234-123456789abc,"
            "did:key:z6Mk...,did:key:z6Mk...#z6Mk...,Ed25519,zFAKEKEY\n"
        )
        with patch(PATCH_LOGIN,    return_value=FAKE_TOKEN), \
             patch(PATCH_ENV,      return_value=(MagicMock(), _fake_env())), \
             patch(PATCH_USER_ID,  return_value="550e8400-e29b-41d4-a716-446655440000"), \
             patch(PATCH_GENERATE, return_value=(1, 0)):
            result = runner.invoke(
                cli,
                ["iir", "bulk-upload-dids", "sign-challenges", "--csv", str(csv_file)],
            )
        assert result.exit_code == 0, result.output

    def test_run_generate_failure_still_exits_zero(self, tmp_path):
        """All rows failed — run_generate returns (0, N) — command still exits 0,
        errors go to the errors CSV, not a crash."""
        csv_file = tmp_path / "input.csv"
        csv_file.write_text(
            "CTID,DID,VerificationMethod,Algorithm,PrivateKey\n"
            "ce-bad,did:key:z6Mk...,did:key:z6Mk...#z6Mk...,Ed25519,zFAKEKEY\n"
        )
        with patch(PATCH_LOGIN,    return_value=FAKE_TOKEN), \
             patch(PATCH_ENV,      return_value=(MagicMock(), _fake_env())), \
             patch(PATCH_USER_ID,  return_value="550e8400-e29b-41d4-a716-446655440000"), \
             patch(PATCH_GENERATE, return_value=(0, 1)):
            result = runner.invoke(
                cli,
                ["iir", "bulk-upload-dids", "sign-challenges", "--csv", str(csv_file)],
            )
        assert result.exit_code == 0, result.output

    def test_invalid_token_exits_nonzero(self, tmp_path):
        """extract_user_id_from_token raises ValueError — command must exit 1."""
        csv_file = tmp_path / "input.csv"
        csv_file.write_text("CTID,DID,VerificationMethod,Algorithm,PrivateKey\nrow\n")
        with patch(PATCH_LOGIN,   return_value="bad.token"), \
             patch(PATCH_ENV,     return_value=(MagicMock(), _fake_env())), \
             patch(PATCH_USER_ID, side_effect=ValueError("'sub' claim missing")):
            result = runner.invoke(
                cli,
                ["iir", "bulk-upload-dids", "sign-challenges", "--csv", str(csv_file)],
            )
        assert result.exit_code == 1

    def test_next_step_hint_shown_when_rows_succeed(self, tmp_path):
        """The 'Next step: publish' hint only appears when ok > 0."""
        csv_file = tmp_path / "input.csv"
        csv_file.write_text(
            "CTID,DID,VerificationMethod,Algorithm,PrivateKey\n"
            "ce-12345678-1234-1234-1234-123456789abc,"
            "did:key:z6Mk...,did:key:z6Mk...#z6Mk...,Ed25519,zFAKEKEY\n"
        )
        with patch(PATCH_LOGIN,    return_value=FAKE_TOKEN), \
             patch(PATCH_ENV,      return_value=(MagicMock(), _fake_env())), \
             patch(PATCH_USER_ID,  return_value="550e8400-e29b-41d4-a716-446655440000"), \
             patch(PATCH_GENERATE, return_value=(1, 0)):
            result = runner.invoke(
                cli,
                ["iir", "bulk-upload-dids", "sign-challenges", "--csv", str(csv_file)],
            )
        assert "publish" in result.output.lower()

    def test_next_step_hint_absent_when_all_rows_fail(self, tmp_path):
        csv_file = tmp_path / "input.csv"
        csv_file.write_text(
            "CTID,DID,VerificationMethod,Algorithm,PrivateKey\n"
            "ce-bad,did:key:z6Mk...,did:key:z6Mk...#z6Mk...,Ed25519,zFAKEKEY\n"
        )
        with patch(PATCH_LOGIN,    return_value=FAKE_TOKEN), \
             patch(PATCH_ENV,      return_value=(MagicMock(), _fake_env())), \
             patch(PATCH_USER_ID,  return_value="550e8400-e29b-41d4-a716-446655440000"), \
             patch(PATCH_GENERATE, return_value=(0, 1)):
            result = runner.invoke(
                cli,
                ["iir", "bulk-upload-dids", "sign-challenges", "--csv", str(csv_file)],
            )
        assert "publish" not in result.output.lower()

    def test_custom_output_path_accepted(self, tmp_path):
        csv_file = tmp_path / "input.csv"
        csv_file.write_text(
            "CTID,DID,VerificationMethod,Algorithm,PrivateKey\n"
            "ce-12345678-1234-1234-1234-123456789abc,"
            "did:key:z6Mk...,did:key:z6Mk...#z6Mk...,Ed25519,zFAKEKEY\n"
        )
        with patch(PATCH_LOGIN,    return_value=FAKE_TOKEN), \
             patch(PATCH_ENV,      return_value=(MagicMock(), _fake_env())), \
             patch(PATCH_USER_ID,  return_value="550e8400-e29b-41d4-a716-446655440000"), \
             patch(PATCH_GENERATE, return_value=(1, 0)) as mock_gen:
            runner.invoke(
                cli,
                ["iir", "bulk-upload-dids", "sign-challenges",
                 "--csv", str(csv_file), "--output", "custom_out.csv"],
            )
        _, kwargs = mock_gen.call_args
        assert kwargs["output_path"] == "custom_out.csv"


class TestPublishCommand:

    def test_missing_output_file_flag_exits_nonzero(self):
        result = runner.invoke(cli, ["iir", "bulk-upload-dids", "publish"])
        assert result.exit_code != 0

    def test_nonexistent_output_file_exits_nonzero(self):
        result = runner.invoke(
            cli,
            ["iir", "bulk-upload-dids", "publish", "--output-file", "/no/such/file.csv"],
        )
        assert result.exit_code != 0

    def test_successful_publish_exits_zero(self, tmp_path):
        output_file = tmp_path / "output.csv"
        output_file.write_text("CTID,DID\n")  # exists=True requires the file to exist
        with patch(PATCH_LOGIN,  return_value=FAKE_TOKEN), \
             patch(PATCH_ENV,    return_value=(MagicMock(), _fake_env())), \
             patch(PATCH_UPLOAD, return_value=None):
            result = runner.invoke(
                cli,
                ["iir", "bulk-upload-dids", "publish", "--output-file", str(output_file)],
            )
        assert result.exit_code == 0, result.output

    def test_yes_flag_passed_through_to_run_upload(self, tmp_path):
        output_file = tmp_path / "output.csv"
        output_file.write_text("CTID,DID\n")
        with patch(PATCH_LOGIN,  return_value=FAKE_TOKEN), \
             patch(PATCH_ENV,    return_value=(MagicMock(), _fake_env())), \
             patch(PATCH_UPLOAD, return_value=None) as mock_upload:
            runner.invoke(
                cli,
                ["iir", "bulk-upload-dids", "publish",
                 "--output-file", str(output_file), "--yes"],
            )
        _, kwargs = mock_upload.call_args
        assert kwargs["yes"] is True

    def test_yes_flag_defaults_to_false(self, tmp_path):
        output_file = tmp_path / "output.csv"
        output_file.write_text("CTID,DID\n")
        with patch(PATCH_LOGIN,  return_value=FAKE_TOKEN), \
             patch(PATCH_ENV,    return_value=(MagicMock(), _fake_env())), \
             patch(PATCH_UPLOAD, return_value=None) as mock_upload:
            runner.invoke(
                cli,
                ["iir", "bulk-upload-dids", "publish", "--output-file", str(output_file)],
            )
        _, kwargs = mock_upload.call_args
        assert kwargs["yes"] is False

    def test_environment_info_shown_in_output(self, tmp_path):
        output_file = tmp_path / "output.csv"
        output_file.write_text("CTID,DID\n")
        with patch(PATCH_LOGIN,  return_value=FAKE_TOKEN), \
             patch(PATCH_ENV,    return_value=(MagicMock(), _fake_env())), \
             patch(PATCH_UPLOAD, return_value=None):
            result = runner.invoke(
                cli,
                ["iir", "bulk-upload-dids", "publish", "--output-file", str(output_file)],
            )
        assert "dev" in result.output


class TestEnvCommands:
    """
    The env commands call load_cli_config() and save_cli_config() directly —
    patch those, not invented helper functions.
    """

    PATCH_LOAD = "ce.commands.env.load_cli_config"
    PATCH_SAVE = "ce.commands.env.save_cli_config"

    def _fake_config(self, envs=None, current=None):
        cfg = MagicMock()
        cfg.environments = envs or {}
        cfg.current_environment = current
        return cfg

    def test_env_list_exits_zero(self):
        with patch(self.PATCH_LOAD, return_value=self._fake_config()):
            result = runner.invoke(cli, ["env", "list"])
        assert result.exit_code == 0

    def test_env_list_shows_configured_environments(self):
        from ce.config.context import Environment
        env = Environment(
            label="Development", client_id="ce-cli",
            device_auth_url="https://dev/auth", token_url="https://dev/token",
            scopes="openid", publisher_base="https://localhost:44330", ssl_verify=False,
        )
        with patch(self.PATCH_LOAD,
                   return_value=self._fake_config({"dev": env}, current="dev")):
            result = runner.invoke(cli, ["env", "list"])
        assert "dev" in result.output

    def test_env_use_unknown_name_exits_nonzero(self):
        with patch(self.PATCH_LOAD, return_value=self._fake_config({})):
            result = runner.invoke(cli, ["env", "use", "nonexistent"])
        assert result.exit_code != 0

    def test_env_use_known_name_exits_zero(self):
        from ce.config.context import Environment
        env = Environment(
            label="Dev", client_id="ce-cli",
            device_auth_url="https://dev/auth", token_url="https://dev/token",
            scopes="openid", publisher_base="https://localhost:44330", ssl_verify=False,
        )
        cfg = self._fake_config({"dev": env}, current=None)
        with patch(self.PATCH_LOAD, return_value=cfg), \
             patch(self.PATCH_SAVE):
            result = runner.invoke(cli, ["env", "use", "dev"])
        assert result.exit_code == 0

    def test_env_use_sets_current_environment(self):
        from ce.config.context import Environment
        env = Environment(
            label="Dev", client_id="ce-cli",
            device_auth_url="https://dev/auth", token_url="https://dev/token",
            scopes="openid", publisher_base="https://localhost:44330", ssl_verify=False,
        )
        cfg = self._fake_config({"dev": env}, current=None)
        with patch(self.PATCH_LOAD, return_value=cfg), \
             patch(self.PATCH_SAVE) as mock_save:
            runner.invoke(cli, ["env", "use", "dev"])
        assert cfg.current_environment == "dev"
        mock_save.assert_called_once()

    def test_env_show_no_active_env_exits_zero(self):
        with patch(self.PATCH_LOAD, return_value=self._fake_config(current=None)):
            result = runner.invoke(cli, ["env", "show"])
        assert result.exit_code == 0

    def test_env_remove_unknown_exits_nonzero(self):
        with patch(self.PATCH_LOAD, return_value=self._fake_config({})):
            result = runner.invoke(cli, ["env", "remove", "ghost"])
        assert result.exit_code != 0


class TestGlobalDebugFlag:
    def test_debug_flag_enables_debug_mode(self):
        with patch("ce.utils.logging.enable_debug") as mock_debug, \
             patch("ce.commands.auth.account_show", return_value=None):
            runner.invoke(cli, ["--debug", "whoami"])
        mock_debug.assert_called_once()

    def test_debug_flag_absent_does_not_call_enable_debug(self):
        with patch("ce.utils.logging.enable_debug") as mock_debug, \
             patch("ce.commands.auth.account_show", return_value=None):
            runner.invoke(cli, ["whoami"])
        mock_debug.assert_not_called()