"""
Main Test Runner Window

This module implements the primary GUI window for the test runner with test organization,
selection, and execution controls.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import PySide6  # noqa: F401  # type: ignore[import-not-found]

    PYSIDE6_AVAILABLE = True
except ImportError:
    PYSIDE6_AVAILABLE = False

if PYSIDE6_AVAILABLE:
    from PySide6.QtCore import (  # type: ignore[import-not-found]
        Qt,
        QThread,
        QTimer,
        Signal,
        pyqtSignal,
    )
    from PySide6.QtGui import QFont, QIcon, QPixmap  # type: ignore[import-not-found]
    from PySide6.QtWidgets import (  # type: ignore[import-not-found]
        QApplication,
        QCheckBox,
        QComboBox,
        QDoubleSpinBox,
        QFrame,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QMainWindow,
        QProgressBar,
        QPushButton,
        QScrollArea,
        QSpinBox,
        QSplitter,
        QTabWidget,
        QTextEdit,
        QTreeWidget,
        QTreeWidgetItem,
        QVBoxLayout,
        QWidget,
    )
else:
    # Fallback for environments without PySide6
    class QMainWindow:  # type: ignore[no-redef]
        def __init__(self, parent=None) -> None:
            pass

        def setWindowTitle(self, title) -> None:
            pass

        def setMinimumSize(self, width, height) -> None:
            pass

        def setCentralWidget(self, widget) -> None:
            pass

        def show(self) -> None:
            pass

    class QWidget:  # type: ignore[no-redef]
        def __init__(self, parent=None) -> None:
            pass

        def show(self) -> None:
            pass

    class Signal:  # type: ignore[no-redef]
        def __init__(self, *args) -> None:
            self._connected_slots: List[Any] = []

        def connect(self, slot) -> None:
            """Connect a slot to this signal."""
            self._connected_slots.append(slot)

        def emit(self, *args) -> None:
            """Emit the signal with arguments."""
            for slot in self._connected_slots:
                slot(*args)

    class QTreeWidget:  # type: ignore[no-redef]
        ExtendedSelection = 3

        def __init__(self, parent=None) -> None:
            self.itemChanged = Signal()
            self._children: List[Any] = []

        def setHeaderLabels(self, labels) -> None:
            pass

        def setSelectionMode(self, mode) -> None:
            pass

        def clear(self) -> None:
            pass

        def expandAll(self) -> None:
            pass

        def collapseAll(self) -> None:
            pass

        def addChild(self, child) -> None:
            self._children.append(child)

    class QTreeWidgetItemIterator:
        def __init__(self, tree) -> None:
            self._tree = tree
            self._index = 0

        def value(self) -> Any:
            # Simplified implementation
            return None

        def __iadd__(self, other) -> "QTreeWidgetItemIterator":
            self._index += 1
            return self

    class QTreeWidgetItem:  # type: ignore[no-redef]
        def __init__(self, parent=None, strings=None) -> None:
            self._parent = parent
            self._strings: List[str] = strings or []
            self._children: List[Any] = []
            self._check_state = 0
            self._flags = 0
            if parent:
                parent.addChild(self)

        def setFlags(self, flags) -> None:
            self._flags = flags

        def flags(self) -> int:
            return self._flags

        def setCheckState(self, column, state) -> None:
            self._check_state = state

        def checkState(self, column) -> int:
            return self._check_state

        def setData(self, column, role, data) -> None:
            pass

        def data(self, column, role) -> Any:
            return None

        def text(self, column: int) -> str:
            if column < len(self._strings):
                return self._strings[column]
            return ""

        def setText(self, column, text) -> None:
            if column < len(self._strings):
                self._strings[column] = text
            else:
                self._strings.append(text)

        def parent(self) -> Any:
            return self._parent

        def childCount(self) -> int:
            return len(self._children)

        def child(self, index) -> Any:
            if 0 <= index < len(self._children):
                return self._children[index]
            return None

        def addChild(self, child) -> None:
            self._children.append(child)

    class QPushButton:  # type: ignore[no-redef]
        def __init__(self, text: Optional[str] = None, parent: Optional[Any] = None) -> None:
            self.clicked = Signal()

        def setStyleSheet(self, style: str) -> None:
            pass

        def setEnabled(self, enabled: bool) -> None:
            pass

    class QLineEdit:  # type: ignore[no-redef]
        def __init__(self, text: Optional[str] = None, parent: Optional[Any] = None) -> None:
            self.textChanged = Signal()

        def setPlaceholderText(self, text: str) -> None:
            pass

        def text(self) -> str:
            return ""

    class QComboBox:  # type: ignore[no-redef]
        def __init__(self, parent: Optional[Any] = None) -> None:
            self.currentTextChanged = Signal()

        def addItem(self, item: str) -> None:
            pass

        def addItems(self, items: List[str]) -> None:
            pass

        def currentText(self) -> str:
            return ""

        def findText(self, text: str) -> int:
            return -1

        def setCurrentIndex(self, index: int) -> None:
            pass

        def clear(self) -> None:
            pass

    class QCheckBox:  # type: ignore[no-redef]
        def __init__(self, text: Optional[str] = None, parent: Optional[Any] = None) -> None:
            self.stateChanged = Signal()

        def setChecked(self, checked: bool) -> None:
            pass

        def isChecked(self) -> bool:
            return False

        def setText(self, text: str) -> None:
            pass

    class QTextEdit:  # type: ignore[no-redef]
        def __init__(self, parent: Optional[Any] = None) -> None:
            pass

    class QProgressBar:  # type: ignore[no-redef]
        def __init__(self, parent: Optional[Any] = None) -> None:
            pass

        def setVisible(self, visible: bool) -> None:
            pass

        def setRange(self, min_val, max_val) -> None:
            pass

        def setValue(self, value) -> None:
            pass

    class QLabel:  # type: ignore[no-redef]
        def __init__(self, text: Optional[str] = None, parent: Optional[Any] = None) -> None:
            pass

        def setText(self, text: str) -> None:
            pass

    class QSpinBox:  # type: ignore[no-redef]
        def __init__(self, parent: Optional[Any] = None) -> None:
            pass

        def setRange(self, min_val: int, max_val: int) -> None:
            pass

        def setValue(self, value) -> None:
            pass

        def value(self) -> int:
            return 0

    class QDoubleSpinBox:  # type: ignore[no-redef]
        def __init__(self, parent=None) -> None:
            pass

        def setRange(self, min_val, max_val) -> None:
            pass

        def setValue(self, value) -> None:
            pass

        def setSuffix(self, suffix) -> None:
            pass

        def value(self) -> float:
            return 0.0

    class QFrame:  # type: ignore[no-redef]
        def __init__(self, parent: Optional[Any] = None) -> None:
            pass

    class QScrollArea:  # type: ignore[no-redef]
        def __init__(self, parent: Optional[Any] = None) -> None:
            pass

        def setWidget(self, widget: Any) -> None:
            pass

        def setWidgetResizable(self, resizable: bool) -> None:
            pass

        def setMaximumWidth(self, width: int) -> None:
            pass

    class QApplication:  # type: ignore[no-redef]
        def __init__(self, *args: Any) -> None:
            pass

        def exec(self) -> int:
            return 0

    class QVBoxLayout:  # type: ignore[no-redef]
        def __init__(self, parent: Optional[Any] = None) -> None:
            pass

        def addWidget(self, widget: Any) -> None:
            pass

        def addLayout(self, layout: Any) -> None:
            pass

    class QHBoxLayout:  # type: ignore[no-redef]
        def __init__(self, parent: Optional[Any] = None) -> None:
            pass

        def addWidget(self, widget: Any) -> None:
            pass

        def addLayout(self, layout: Any) -> None:
            pass

        def addStretch(self) -> None:
            pass

    pyqtSignal = Signal

    class Qt:  # type: ignore[no-redef]
        Horizontal = 1
        Vertical = 2
        ItemIsTristate = 8
        ItemIsUserCheckable = 32
        Unchecked = 0
        Checked = 2
        PartiallyChecked = 1
        UserRole = 32

    class QSplitter:  # type: ignore[no-redef]
        def __init__(self, orientation=None, parent=None):
            pass

        def addWidget(self, widget):
            pass

        def setSizes(self, sizes):
            pass

    class QGroupBox:  # type: ignore[no-redef]
        def __init__(self, title=None, parent=None):
            pass

    class QTabWidget:  # type: ignore[no-redef]
        def __init__(self, parent=None):
            pass

        def addTab(self, widget, title):
            pass

    class QTimer:  # type: ignore[no-redef]
        def __init__(self, parent=None):
            self.timeout = Signal()

        def setSingleShot(self, single):
            pass

        def start(self, msec):
            pass

        def stop(self):
            pass

    class QThread:  # type: ignore[no-redef]
        def __init__(self, parent=None):
            pass

        def start(self):
            pass

        def wait(self):
            pass

    class QIcon:  # type: ignore[no-redef]
        def __init__(self, filename=None):
            pass

    class QFont:  # type: ignore[no-redef]
        def __init__(self, family=None, pointSize=-1):
            pass

        @staticmethod
        def setFamily(family):
            pass

        @staticmethod
        def setPointSize(size):
            pass

    class QPixmap:  # type: ignore[no-redef]
        def __init__(self, filename=None):
            pass


from apgi_framework.utils.framework_test_utils import (
    FrameworkConfiguration,
    FrameworkResults,
    FrameworkRunCategory,
    FrameworkTestCase,
)


class TestTreeWidget(QTreeWidget):
    """Custom tree widget for displaying tests with categories and modules."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setHeaderLabels(["Test Name", "Category", "Module", "Status", "Time"])
        self.setSelectionMode(QTreeWidget.ExtendedSelection)
        self.itemChanged.connect(self._on_item_changed)
        self._test_items: Dict[str, QTreeWidgetItem] = {}

    def populate_tests(self, test_cases: List[FrameworkTestCase]):
        """Populate the tree with test cases organized by category and module."""
        self.clear()
        self._test_items.clear()

        # Group tests by category and module
        category_groups: Dict[FrameworkRunCategory, Dict[str, List[FrameworkTestCase]]] = {}

        for test_case in test_cases:
            if test_case.category not in category_groups:
                category_groups[test_case.category] = {}

            if test_case.module not in category_groups[test_case.category]:
                category_groups[test_case.category][test_case.module] = []

            category_groups[test_case.category][test_case.module].append(test_case)

        # Create tree structure
        for category, modules in category_groups.items():
            category_item = QTreeWidgetItem(self, [category.value.title(), "", "", "", ""])
            category_item.setFlags(
                category_item.flags() | Qt.ItemIsTristate | Qt.ItemIsUserCheckable
            )
            category_item.setCheckState(0, Qt.Unchecked)

            for module_name, tests in modules.items():
                module_item = QTreeWidgetItem(category_item, [module_name, "", "", "", ""])
                module_item.setFlags(
                    module_item.flags() | Qt.ItemIsTristate | Qt.ItemIsUserCheckable
                )
                module_item.setCheckState(0, Qt.Unchecked)

                for test in tests:
                    test_item = QTreeWidgetItem(
                        module_item,
                        [
                            test.name,
                            test.category.value,
                            test.module,
                            "Not Run",
                            (
                                f"{test.estimated_duration:.3f}s"
                                if test.estimated_duration > 0
                                else ""
                            ),
                        ],
                    )
                    test_item.setFlags(test_item.flags() | Qt.ItemIsUserCheckable)
                    test_item.setCheckState(0, Qt.Unchecked)
                    test_item.setData(0, Qt.UserRole, test)
                    self._test_items[test.name] = test_item

        self.expandAll()

    def get_selected_tests(self) -> List[FrameworkTestCase]:
        """Get all checked test cases."""
        selected_tests = []

        for test_name, item in self._test_items.items():
            if item.checkState(0) == Qt.Checked:
                test_data = item.data(0, Qt.UserRole)
                if test_data:
                    selected_tests.append(test_data)

        return selected_tests

    def update_test_status(self, test_name: str, status: str, execution_time: float = 0.0):
        """Update the status and execution time of a test."""
        if test_name in self._test_items:
            item = self._test_items[test_name]
            item.setText(3, status)
            if execution_time > 0:
                item.setText(4, f"{execution_time:.3f}s")

    def _on_item_changed(self, item: QTreeWidgetItem, column: int):
        """Handle item check state changes."""
        if column == 0:  # Only handle check state changes
            self._update_parent_check_state(item)
            self._update_child_check_states(item)

    def _update_parent_check_state(self, item: QTreeWidgetItem):
        """Update parent item check state based on children."""
        parent = item.parent()
        if not parent:
            return

        checked_count = 0
        total_count = parent.childCount()

        for i in range(total_count):
            child = parent.child(i)
            if child.checkState(0) == Qt.Checked:
                checked_count += 1

        if checked_count == 0:
            parent.setCheckState(0, Qt.Unchecked)
        elif checked_count == total_count:
            parent.setCheckState(0, Qt.Checked)
        else:
            parent.setCheckState(0, Qt.PartiallyChecked)

        self._update_parent_check_state(parent)

    def _update_child_check_states(self, item: QTreeWidgetItem):
        """Update child item check states based on parent."""
        if item.checkState(0) != Qt.PartiallyChecked:
            check_state = item.checkState(0)
            for i in range(item.childCount()):
                child = item.child(i)
                child.setCheckState(0, check_state)
                self._update_child_check_states(child)


class TestFilterWidget(QWidget):
    """Widget for filtering tests by various criteria."""

    filter_changed = Signal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        """Set up the filter UI."""
        layout = QVBoxLayout(self)

        # Search filter
        search_group = QGroupBox("Search")
        search_layout = QVBoxLayout(search_group)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search tests by name...")
        self.search_input.textChanged.connect(self.filter_changed.emit)
        search_layout.addWidget(self.search_input)

        layout.addWidget(search_group)

        # Category filter
        category_group = QGroupBox("Categories")
        category_layout = QVBoxLayout(category_group)

        self.category_checkboxes = {}
        for category in FrameworkRunCategory:
            checkbox = QCheckBox(category.value.title())
            checkbox.setChecked(True)
            checkbox.stateChanged.connect(self.filter_changed.emit)
            self.category_checkboxes[category] = checkbox
            category_layout.addWidget(checkbox)

        layout.addWidget(category_group)

        # Module filter
        module_group = QGroupBox("Modules")
        module_layout = QVBoxLayout(module_group)

        self.module_combo = QComboBox()
        self.module_combo.addItem("All Modules")
        self.module_combo.currentTextChanged.connect(self.filter_changed.emit)
        module_layout.addWidget(self.module_combo)

        layout.addWidget(module_group)

        # Status filter
        status_group = QGroupBox("Status")
        status_layout = QVBoxLayout(status_group)

        self.show_passed = QCheckBox("Show Passed")
        self.show_failed = QCheckBox("Show Failed")
        self.show_skipped = QCheckBox("Show Skipped")
        self.show_not_run = QCheckBox("Show Not Run")

        for checkbox in [
            self.show_passed,
            self.show_failed,
            self.show_skipped,
            self.show_not_run,
        ]:
            checkbox.setChecked(True)
            checkbox.stateChanged.connect(self.filter_changed.emit)
            status_layout.addWidget(checkbox)

        layout.addWidget(status_group)

    def update_modules(self, modules: List[str]):
        """Update the module filter with available modules."""
        current_text = self.module_combo.currentText()
        self.module_combo.clear()
        self.module_combo.addItem("All Modules")
        self.module_combo.addItems(sorted(modules))

        # Restore previous selection if it still exists
        index = self.module_combo.findText(current_text)
        if index >= 0:
            self.module_combo.setCurrentIndex(index)

    def get_filter_criteria(self) -> Dict:
        """Get current filter criteria."""
        return {
            "search_text": self.search_input.text().lower(),
            "categories": [cat for cat, cb in self.category_checkboxes.items() if cb.isChecked()],
            "module": (
                self.module_combo.currentText()
                if self.module_combo.currentText() != "All Modules"
                else None
            ),
            "show_passed": self.show_passed.isChecked(),
            "show_failed": self.show_failed.isChecked(),
            "show_skipped": self.show_skipped.isChecked(),
            "show_not_run": self.show_not_run.isChecked(),
        }


class FrameworkConfigurationWidget(QWidget):
    """Widget for configuring test execution parameters."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        """Set up the configuration UI."""
        layout = QVBoxLayout(self)

        # Execution settings
        exec_group = QGroupBox("Execution Settings")
        exec_layout = QVBoxLayout(exec_group)

        # Parallel execution
        parallel_layout = QHBoxLayout()
        self.parallel_checkbox = QCheckBox("Enable Parallel Execution")
        self.parallel_checkbox.setChecked(True)
        parallel_layout.addWidget(self.parallel_checkbox)

        parallel_layout.addWidget(QLabel("Max Workers:"))
        self.max_workers_spin = QSpinBox()
        self.max_workers_spin.setRange(1, 16)
        self.max_workers_spin.setValue(4)
        parallel_layout.addWidget(self.max_workers_spin)

        exec_layout.addLayout(parallel_layout)

        # Timeout
        timeout_layout = QHBoxLayout()
        timeout_layout.addWidget(QLabel("Timeout (seconds):"))
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(10, 3600)
        self.timeout_spin.setValue(300)
        timeout_layout.addWidget(self.timeout_spin)
        exec_layout.addLayout(timeout_layout)

        # Verbose output
        self.verbose_checkbox = QCheckBox("Verbose Output")
        exec_layout.addWidget(self.verbose_checkbox)

        layout.addWidget(exec_group)

        # Coverage settings
        coverage_group = QGroupBox("Coverage Settings")
        coverage_layout = QVBoxLayout(coverage_group)

        self.collect_coverage_checkbox = QCheckBox("Collect Coverage Data")
        self.collect_coverage_checkbox.setChecked(True)
        coverage_layout.addWidget(self.collect_coverage_checkbox)

        # Coverage thresholds
        threshold_layout = QHBoxLayout()
        threshold_layout.addWidget(QLabel("Line Coverage Threshold:"))
        self.line_threshold_spin = QDoubleSpinBox()
        self.line_threshold_spin.setRange(0.0, 100.0)
        self.line_threshold_spin.setValue(95.0)
        self.line_threshold_spin.setSuffix("%")
        threshold_layout.addWidget(self.line_threshold_spin)

        threshold_layout.addWidget(QLabel("Branch Coverage Threshold:"))
        self.branch_threshold_spin = QDoubleSpinBox()
        self.branch_threshold_spin.setRange(0.0, 100.0)
        self.branch_threshold_spin.setValue(90.0)
        self.branch_threshold_spin.setSuffix("%")
        threshold_layout.addWidget(self.branch_threshold_spin)

        coverage_layout.addLayout(threshold_layout)

        layout.addWidget(coverage_group)

        # Property test settings
        property_group = QGroupBox("Property Test Settings")
        property_layout = QVBoxLayout(property_group)

        iterations_layout = QHBoxLayout()
        iterations_layout.addWidget(QLabel("Iterations:"))
        self.iterations_spin = QSpinBox()
        self.iterations_spin.setRange(10, 10000)
        self.iterations_spin.setValue(100)
        iterations_layout.addWidget(self.iterations_spin)
        property_layout.addLayout(iterations_layout)

        layout.addWidget(property_group)

    def get_configuration(self) -> FrameworkConfiguration:
        """Get the current test configuration."""
        return FrameworkConfiguration(
            parallel=self.parallel_checkbox.isChecked(),
            max_workers=self.max_workers_spin.value(),
            timeout=self.timeout_spin.value(),
            verbose=self.verbose_checkbox.isChecked(),
            coverage=self.collect_coverage_checkbox.isChecked(),
        )

    def set_configuration(self, config: FrameworkConfiguration):
        """Set the configuration values."""
        self.parallel_checkbox.setChecked(config.parallel)
        self.max_workers_spin.setValue(config.max_workers)
        self.timeout_spin.setValue(config.timeout or 300)
        self.verbose_checkbox.setChecked(config.verbose)
        self.collect_coverage_checkbox.setChecked(config.coverage)


class MainTestWindow(QMainWindow):
    """Main window for the test runner GUI."""

    # Signals
    test_execution_requested = Signal(list, FrameworkConfiguration)  # selected_tests, config
    test_execution_cancelled = Signal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._test_cases: List[FrameworkTestCase] = []
        self._filtered_tests: List[FrameworkTestCase] = []
        self._setup_ui()
        self._setup_connections()

    def _setup_ui(self):
        """Set up the main UI."""
        self.setWindowTitle("APGI Test Runner")
        self.setMinimumSize(1200, 800)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QHBoxLayout(central_widget)

        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        # Left panel - Test organization and filters
        left_panel = self._create_left_panel()
        splitter.addWidget(left_panel)

        # Right panel - Configuration and controls
        right_panel = self._create_right_panel()
        splitter.addWidget(right_panel)

        # Set splitter proportions
        splitter.setSizes([800, 400])

    def _create_left_panel(self) -> QWidget:
        """Create the left panel with test tree and filters."""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Test tree
        tree_group = QGroupBox("Test Suite")
        tree_layout = QVBoxLayout(tree_group)

        # Test selection controls
        selection_layout = QHBoxLayout()
        self.select_all_btn = QPushButton("Select All")
        self.select_none_btn = QPushButton("Select None")
        self.expand_all_btn = QPushButton("Expand All")
        self.collapse_all_btn = QPushButton("Collapse All")

        selection_layout.addWidget(self.select_all_btn)
        selection_layout.addWidget(self.select_none_btn)
        selection_layout.addWidget(self.expand_all_btn)
        selection_layout.addWidget(self.collapse_all_btn)
        selection_layout.addStretch()

        tree_layout.addLayout(selection_layout)

        # Test tree widget
        self.test_tree = TestTreeWidget()
        tree_layout.addWidget(self.test_tree)

        layout.addWidget(tree_group)

        # Filter panel
        filter_scroll = QScrollArea()
        self.filter_widget = TestFilterWidget()
        filter_scroll.setWidget(self.filter_widget)
        filter_scroll.setWidgetResizable(True)
        filter_scroll.setMaximumWidth(300)

        layout.addWidget(filter_scroll)

        return panel

    def _create_right_panel(self) -> QWidget:
        """Create the right panel with configuration and controls."""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Configuration widget
        config_scroll = QScrollArea()
        self.config_widget = FrameworkConfigurationWidget()
        config_scroll.setWidget(self.config_widget)
        config_scroll.setWidgetResizable(True)

        layout.addWidget(config_scroll)

        # Execution controls
        controls_group = QGroupBox("Execution Controls")
        controls_layout = QVBoxLayout(controls_group)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        controls_layout.addWidget(self.progress_bar)

        # Status label
        self.status_label = QLabel("Ready")
        controls_layout.addWidget(self.status_label)

        # Control buttons
        button_layout = QHBoxLayout()

        self.run_selected_btn = QPushButton("Run Selected Tests")
        self.run_selected_btn.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; font-weight: bold; }"
        )

        self.run_all_btn = QPushButton("Run All Tests")
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setEnabled(False)

        button_layout.addWidget(self.run_selected_btn)
        button_layout.addWidget(self.run_all_btn)
        button_layout.addWidget(self.cancel_btn)

        controls_layout.addLayout(button_layout)

        # Test count info
        self.test_count_label = QLabel("Tests: 0 total, 0 selected")
        controls_layout.addWidget(self.test_count_label)

        layout.addWidget(controls_group)

        return panel

    def _setup_connections(self):
        """Set up signal connections."""
        # Tree selection controls
        self.select_all_btn.clicked.connect(self._select_all_tests)
        self.select_none_btn.clicked.connect(self._select_no_tests)
        self.expand_all_btn.clicked.connect(self.test_tree.expandAll)
        self.collapse_all_btn.clicked.connect(self.test_tree.collapseAll)

        # Execution controls
        self.run_selected_btn.clicked.connect(self._run_selected_tests)
        self.run_all_btn.clicked.connect(self._run_all_tests)
        self.cancel_btn.clicked.connect(self._cancel_execution)

        # Filter changes
        self.filter_widget.filter_changed.connect(self._apply_filters)

        # Test tree changes
        self.test_tree.itemChanged.connect(self._update_test_count)

    def load_test_cases(self, test_cases: List[FrameworkTestCase]):
        """Load test cases into the tree."""
        self._test_cases = test_cases
        self._filtered_tests = test_cases.copy()

        # Update module filter
        modules = list(set(test.module for test in test_cases))
        self.filter_widget.update_modules(modules)

        # Populate tree
        self.test_tree.populate_tests(self._filtered_tests)
        self._update_test_count()

    def _apply_filters(self):
        """Apply current filter criteria to test cases."""
        if not self._test_cases:
            return

        criteria = self.filter_widget.get_filter_criteria()
        filtered_tests = []

        for test in self._test_cases:
            # Search filter
            if criteria["search_text"] and criteria["search_text"] not in test.name.lower():
                continue

            # Category filter
            if test.category not in criteria["categories"]:
                continue

            # Module filter
            if criteria["module"] and test.module != criteria["module"]:
                continue

            # Status filter (simplified for now)
            # In a real implementation, you'd check actual test status

            filtered_tests.append(test)

        self._filtered_tests = filtered_tests
        self.test_tree.populate_tests(self._filtered_tests)
        self._update_test_count()

    def _select_all_tests(self):
        """Select all visible tests."""
        iterator = QTreeWidgetItemIterator(self.test_tree)
        while iterator.value():
            item = iterator.value()
            if item.flags() & Qt.ItemIsUserCheckable and item.parent():  # Only leaf items
                item.setCheckState(0, Qt.Checked)
            iterator += 1
        self._update_test_count()

    def _select_no_tests(self):
        """Deselect all tests."""
        iterator = QTreeWidgetItemIterator(self.test_tree)
        while iterator.value():
            item = iterator.value()
            if item.flags() & Qt.ItemIsUserCheckable:
                item.setCheckState(0, Qt.Unchecked)
            iterator += 1
        self._update_test_count()

    def _update_test_count(self):
        """Update the test count display."""
        total_tests = len(self._filtered_tests)
        selected_tests = len(self.test_tree.get_selected_tests())
        self.test_count_label.setText(f"Tests: {total_tests} total, {selected_tests} selected")

    def _run_selected_tests(self):
        """Run the selected tests."""
        selected_tests = self.test_tree.get_selected_tests()
        if not selected_tests:
            self.status_label.setText("No tests selected")
            return

        config = self.config_widget.get_configuration()
        self._start_execution()
        self.test_execution_requested.emit(selected_tests, config)

    def _run_all_tests(self):
        """Run all filtered tests."""
        if not self._filtered_tests:
            self.status_label.setText("No tests available")
            return

        # Select all tests first
        self._select_all_tests()
        selected_tests = self.test_tree.get_selected_tests()

        config = self.config_widget.get_configuration()
        self._start_execution()
        self.test_execution_requested.emit(selected_tests, config)

    def _cancel_execution(self):
        """Cancel test execution."""
        self.test_execution_cancelled.emit()
        self._stop_execution()

    def _start_execution(self) -> None:
        """Update UI for test execution start."""
        self.run_selected_btn.setEnabled(False)
        self.run_all_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.status_label.setText("Running tests...")

    def _stop_execution(self) -> None:
        """Update UI for test execution stop."""
        self.run_selected_btn.setEnabled(True)
        self.run_all_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.status_label.setText("Ready")

    def update_execution_progress(self, current: int, total: int, current_test: str = "") -> None:
        """Update execution progress."""
        if total > 0:
            self.progress_bar.setRange(0, total)
            self.progress_bar.setValue(current)
            status_text = f"Running tests... ({current}/{total})"
            if current_test:
                status_text += f" - {current_test}"
            self.status_label.setText(status_text)

    def update_test_result(self, test_name: str, status: str, execution_time: float = 0.0) -> None:
        """Update a test result in the tree."""
        self.test_tree.update_test_status(test_name, status, execution_time)

    def execution_completed(self, results: FrameworkResults) -> None:
        """Handle execution completion."""
        self._stop_execution()

        # Update status
        pass_rate = (
            (results.passed_tests / results.total_tests * 100) if results.total_tests > 0 else 0
        )
        self.status_label.setText(
            f"Completed: {results.passed_tests}/{results.total_tests} passed ({pass_rate:.1f}%)"
        )


def main():
    """Main function for testing the GUI."""
    app = QApplication(sys.argv)

    # Create sample test cases
    sample_tests = [
        FrameworkTestCase(
            name="test_core_analysis",
            file_path=Path("tests/test_core_analysis.py"),
            module="core.analysis",
            class_name=None,
            method_name="test_core_analysis",
            category=FrameworkRunCategory.UNIT,
            line_number=10,
            docstring="Test core analysis functionality",
        ),
        FrameworkTestCase(
            name="test_clinical_integration",
            file_path=Path("tests/test_clinical.py"),
            module="clinical",
            class_name=None,
            method_name="test_clinical_integration",
            category=FrameworkRunCategory.INTEGRATION,
            line_number=20,
            docstring="Test clinical integration",
        ),
        FrameworkTestCase(
            name="test_neural_processing",
            file_path=Path("tests/test_neural.py"),
            module="neural",
            class_name=None,
            method_name="test_neural_processing",
            category=FrameworkRunCategory.MODULE_SPECIFIC,
            line_number=30,
            docstring="Test neural processing",
        ),
    ]

    window = MainTestWindow()
    window.load_test_cases(sample_tests)
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
