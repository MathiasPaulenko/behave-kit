Feature: TypedContext
  As a behave-kit developer
  I want to verify that TypedContext validates attributes against a schema
  So that context access is type-safe

  Scenario: TypedContext allows declared attributes
    Given a TypedContext with schema declaring "driver" and "base_url"
    When I setup the context with driver "chrome" and base_url "https://test.com"
    Then the typed context driver should be "chrome"
    And the typed context base_url should be "https://test.com"

  Scenario: TypedContext rejects undeclared attributes
    Given a TypedContext with schema declaring "driver"
    When I try to access "undeclared_attr" from the typed context
    Then it should raise a ScopeError
