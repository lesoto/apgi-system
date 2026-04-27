from typing import Dict, Type

from apgi_framework.commands.analysis import (
    TestAnalysisCommand,
    TestCoverageCommand,
    TestResultsCommand,
)
from apgi_framework.commands.base import BaseCommand
from apgi_framework.commands.config import GenerateConfigCommand, SetParamsCommand
from apgi_framework.commands.system import StatusCommand, ValidateSystemCommand
from apgi_framework.commands.test import (
    BatchTestCommand,
    OrganizeTestsCommand,
    RunBatchCommand,
    RunEnhancedTestsCommand,
    RunTestCommand,
)

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
