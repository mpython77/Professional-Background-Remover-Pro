"""Logger singleton tests."""

import logging

from utils.logger import setup_logger, _loggers


class TestLoggerSingleton:
    """Logger singleton pattern tests."""

    def test_same_name_returns_same_logger(self) -> None:
        """Calling with the same name should return the same logger instance."""
        logger1 = setup_logger("test_singleton_a")
        logger2 = setup_logger("test_singleton_a")
        assert logger1 is logger2

    def test_different_names_return_different_loggers(self) -> None:
        """Different names should return different logger instances."""
        logger1 = setup_logger("test_diff_1")
        logger2 = setup_logger("test_diff_2")
        assert logger1 is not logger2

    def test_no_duplicate_handlers(self) -> None:
        """Calling again should not add duplicate handlers."""
        name = "test_no_dup"
        logger1 = setup_logger(name)
        handler_count_1 = len(logger1.handlers)
        logger2 = setup_logger(name)
        handler_count_2 = len(logger2.handlers)
        assert handler_count_1 == handler_count_2

    def test_logger_level(self) -> None:
        """Logger level should be set correctly."""
        lgr = setup_logger("test_level")
        assert lgr.level == logging.DEBUG

    def test_logger_has_handlers(self) -> None:
        """Logger should have at least 2 handlers (console + file)."""
        lgr = setup_logger("test_handlers")
        assert len(lgr.handlers) >= 2

    def test_cached_in_dict(self) -> None:
        """Logger should be cached in the _loggers dictionary."""
        name = "test_cached"
        lgr = setup_logger(name)
        assert name in _loggers
        assert _loggers[name] is lgr
