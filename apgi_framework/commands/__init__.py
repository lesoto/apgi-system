from typing import Dict, Type

from apgi_framework.commands.base import BaseCommand
from apgi_framework.commands.test import (
    RunTestCommand,
    RunBatchCommand,
    BatchTestCommand,
    RunEnhancedTestsCommand,
    OrganizeTestsCommand,
)
from apgi_framework.commands.config import GenerateConfigCommand, SetParamsCommand
from apgi_framework.commands.analysis import (
    TestResultsCommand,
    TestAnalysisCommand,
    TestCoverageCommand,
)
from apgi_framework.commands.system import ValidateSystemCommand, StatusCommand

COMMAND_REGISTRY: Dict[str, Type[BaseCommand]] = {
    "run-test": RunTestCommand,
    "run-batch": RunBatchCommand,
    "batch-test": BatchTestCommand,
    "run-tests": RunEnhancedTestsCommand,
    "organize-tests": OrganizeTestsCommand,
    "test-results": TestResultsCommand,
    "test-analysis": TestAnalysisCommand,
    "test-coverage": TestCoverageCommand,
    "generate-config": GenerateConfigCommand,
    "validate-system": ValidateSystemCommand,
    "status": StatusCommand,
    "set-params": SetParamsCommand,
}
