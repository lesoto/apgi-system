from apgi_framework.cli import APGIFrameworkCLI


def test_cli_has_run():
    cli = APGIFrameworkCLI()
    assert hasattr(cli, "run")
    assert hasattr(APGIFrameworkCLI, "run")


if __name__ == "__main__":
    cli = APGIFrameworkCLI()
    print(f"Has run: {hasattr(cli, 'run')}")
