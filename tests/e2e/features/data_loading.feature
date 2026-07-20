Feature: Data loading
  As a behave-kit developer
  I want to verify that load_data() works with CSV and JSON
  So that test data is loaded correctly

  Scenario: Load CSV data
    Given a CSV file "users.csv" with columns "name,age"
    When I load data from "users.csv"
    Then the result should be a list of 2 records
    And the first record should have name "Alice"

  Scenario: Load JSON data
    Given a JSON file "config.json" with key "base_url" and value "https://example.com"
    When I load data from "config.json"
    Then the result should have key "base_url" with value "https://example.com"
