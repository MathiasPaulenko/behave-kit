Feature: Environment variables
  As a behave-kit developer
  I want to verify that env() reads variables with defaults and required
  So that configuration is type-safe

  Scenario: env() returns default when variable is missing
    When I read env var "MISSING_VAR" with default "fallback"
    Then the value should be "fallback"

  Scenario: env() returns value when variable is set
    When I set env var "TEST_VAR" to "hello"
    And I read env var "TEST_VAR" with default "fallback"
    Then the value should be "hello"

  Scenario: env() raises when required and missing
    When I read env var "REQUIRED_MISSING" as required
    Then it should raise an EnvVarError
